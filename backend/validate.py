# validate.py
# EHR Clinical Data Reconciliation Engine
# By: Anastasiya Gorlov
# Tuesday, March 17th, 2026 and Wed, March 18th, 2026
# This file handles the AI logic for data quality validation
# It is called by main.py when endpoint 2 receives a request

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# libraries

from dotenv import load_dotenv #loading the env.. and fixing the broken function body
load_dotenv()

import anthropic # talking to Claude AI
import json # convert Claude's response to python dict
import os # reading API key from environment
from datetime import datetime # to check how old the data is 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# creating connection to Claude, reading API KEY safely
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY. Add it to your .env file, and try again.")
client = anthropic.Anthropic(api_key=api_key)

# Rule-Based Checks - they run before Claude, these are free and fast

def run_basic_checks(payload: dict) -> list: #payload here is the patient data from front end
    issues = []

    # Check 1 - Empty Allergies list - likely not documented
    allergies = payload.get('allergies', None)
    if allergies is None or allergies == []:
        issues.append({
            'field': 'allergies',
            'issue': 'No allergies documented - likely incomplete',
            'severity': 'medium'
        })

    # Check 2 - Blood pressure range check
    # normal 90/60 to 180/120 -- anthing outside the range is suspicious

    vitals = payload.get('vital_signs', {})
    bp = vitals.get('blood_pressure', '')
    if bp:
        try:
            # here we split 340/180 into systolic = 340  and diastolic = 180
            systolic = int(bp.split('/')[0])
            diastolic = int(bp.split('/')[1])
            if systolic > 300 or systolic < 50 or diastolic > 200 or diastolic < 20:
                issues.append({
                    'field': 'vital_signs.blood_pressure',
                    'issue': f'Blood pressure {bp} is physiologically implausible',
                    'severity': 'high'
                })
        except:
            # if we can't read the BP format, we flag it
            issues.append({
                'field': 'vital_signs.blood_pressure',
                'issue': 'Blood pressure could not be read',
                'severity': 'medium'
            })

    # Check 3 - data staleness check
    # data older than 6 months (180 days)  is considered stale
    last_updated = payload.get('last_updated')
    if last_updated:
        try:
            #strptime = converts string to datetime object
            update_date = datetime.strptime(last_updated, '%Y-%m-%d')
            #calculate how many days old the data is
            days_old = (datetime.now() - update_date).days
            if days_old > 180:
                issues.append({
                    'field': 'last_updated',
                    'issue': f'Data is {days_old // 30}+ months old',
                    'severity': 'medium'
                })
        except:
            pass # if date format is wrong we skip check

    return issues 


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# Main Validation Function
# this is called by main.py when endpoint 2 gets a request

async def validate_data_quality(payload: dict) -> dict:
    # payload = patient records
    # payload is the patient records sent from frontend, (-> returns the dict)
    print("Starting data quality validation, please wait..")

    # checking for issues, runs free basic checks, before sending API money
    basic_issues = run_basic_checks(payload)

    # our actual prompt for Claude
    # for our f-string ( which lets us insert variables with {}) 
    # we add the FULL patient record AND the basic issues, for deeper analysis

    prompt = f"""You are a clinical data quality helper.

Review this patient record and respond ONLY with valid JSON.
Do not use markdown.
Do not use triple backticks.
Do not include any text outside the JSON.

Use exactly this structure:
{{
  "overall_score": 0,
  "breakdown": {{
    "completeness": 0,
    "accuracy": 0,
    "timeliness": 0,
    "clinical_plausibility": 0
  }},
  "issues_detected": [
    {{
      "field": "string",
      "issue": "string",
      "severity": "high"
    }}
  ],
  "summary": "string"
}}

Patient record:
{json.dumps(payload, indent=2)}

Issues already found by basic checks:
{json.dumps(basic_issues, indent=2)}
"""
    
    # calling Claude with error handling
    print("Calling Claude AI, please wait..")
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # our Claude version
            max_tokens=1000,  # max length of Claude's response
            messages=[
                {'role': 'user', 'content': prompt}
                # role 'user' = we are asking
                # content = our actual message to Claude
            ]
        )
        ai_response = message.content[0].text # Claude Ai reply
        print ("Claude has responded!")
     
    # too many requests sent too fast
    except anthropic.RateLimitError:
        raise Exception("Rate limit is reached, please wait and try again.")
    
    # something went wrong on Anthropic side
    except anthropic.APIError as e:
        raise Exception (f"API error: {str(e)}")


# Parse Claudes JSON respose into Python dict
# this is where json.loads converts JSON string to Python dict

    try:
        cleaned = ai_response.strip() # removing all extra spaces
        if cleaned.startswith("'''"):
            cleaned = cleaned.split("''''")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned [4:] # remove word "json"
        result = json.loads(cleaned) # getting our Python dict

    except json.JSONDecodeError:
        raise Exception ("Could not parse Claude response as a JSON")

    print("Validation complete!")
    return result # send the results back to our main.py

# This is the end of our validate.py 
