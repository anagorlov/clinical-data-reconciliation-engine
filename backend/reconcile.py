# reconcile.py
# EHR Clinical Data Reconciliation Engine
# By: Anastasiya Gorlov 
# Tuesday, March 17th, 2026 
# This .py file is called by main.py when endpoint 1 receives a request

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# libraries
from dotenv import load_dotenv
load_dotenv()

import anthropic # talking to Claude AI
import json # convert Claude's response to python dict
import os # reading API key from environment
from anthropic import Anthropic


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# creating connection to Claude, reading API KEY safely
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY. Add it to your .env file, and try again.")
client = anthropic.Anthropic(api_key=api_key)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# Bonus Feature: Duplicate Detection
# This simply checks if two sources list the same medication

# sources = list of medication records from different systems
# returns a list of any duplicates that are found

def detect_duplicates(sources: list) -> list:
    duplicates = []  # empty list to store duplicates we find

    # compare every source against every other source
    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):

            # get the medication name from each source
            med_a = sources[i].get('medication', '').lower()
            med_b = sources[j].get('medication', '').lower()

            # get just the first word (the drug name only)
            # example: 'Metformin 500mg daily' becomes 'metformin'
            drug_a = med_a.split()[0] if med_a else ''
            drug_b = med_b.split()[0] if med_b else ''

            # if same drug found in two sources it will get flagged
            if drug_a and drug_b and drug_a == drug_b:
                duplicates.append({
                    'source_a': sources[i].get('system'),
                    'source_b': sources[j].get('system'),
                    'issue': 'Same medication listed in multiple sources',
                    'medication_a': sources[i].get('medication'),
                    'medication_b': sources[j].get('medication')
                })

    return duplicates

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# Bonus Feature: Confidence Score Calibration
# This part will calculate how trustworthy the source is before it calls Claude

def calculate_source_weights(sources: list) -> dict:
    reliability_weights = {'high': 1.0, 'medium': 0.6, 'low': 0.2}
    weights = {}  # empty dict to store our calculated weights

    for source in sources:
        system = source.get('system', 'unknown')
        reliability = source.get('source_reliability', 'medium')

        # get the weight for this reliability level
        # if reliability not found use 0.5 as default
        weight = reliability_weights.get(reliability, 0.5)

        # save the weight rounded to 3 decimal places
        weights[system] = round(weight, 3)

    return weights

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# Prompt Engineering
# Here we are building the message we send to Claude

def build_prompt(payload: dict, source_weights: dict) -> str:
    # payload = the full request data
    # source_weights = our pre-calculated reliability weights
    # returns the full prompt string we send to Claude

    patient_context = payload.get('patient_context', {})
    sources = payload.get('sources', [])

    prompt = f'''You are a clinical  AI assistant
helping reconcile conflicting medication records.

PATIENT CONTEXT:
{json.dumps(patient_context, indent=2)}

CONFLICTING MEDICATION RECORDS:
{json.dumps(sources, indent=2)}

SOURCE RELIABILITY WEIGHTS (higher = more trustworthy):
{json.dumps(source_weights, indent=2)}

Analyze all sources and determine the most accurate medication.
Consider: source reliability, recency, patient conditions and labs.

Respond ONLY in JSON with exactly these fields:
{{
  "reconciled_medication": "the most accurate medication and dose",
  "confidence_score": 0.00,
  "reasoning": "explanation referencing sources and patient context",
  "recommended_actions": ["action 1", "action 2"],
  "clinical_safety_check": "PASSED or FLAGGED with explanation"
}}'''

    return prompt

# This is our reconcile function to get results on our frontend
async def reconcile_medication(payload: dict) -> dict:
    print('Starting medication reconciliation...')

    sources = payload.get('sources', [])
    duplicates = detect_duplicates(sources)
    source_weights = calculate_source_weights(sources)
    prompt = build_prompt(payload, source_weights)

    try:
        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        ai_response = message.content[0].text

    except anthropic.RateLimitError:
        raise Exception('Rate limit reached. Please wait and try again.')
    except anthropic.APIError as e:
        raise Exception(f'API error: {str(e)}')

    try:
        cleaned = ai_response.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('```')[1]
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]
        result = json.loads(cleaned)

    except json.JSONDecodeError:
        raise Exception('Could not parse Claude response as JSON')

    result['source_weights'] = source_weights
    result['duplicates_detected'] = duplicates if duplicates else 'none'

    print('Reconciliation complete!')
    return result
# reconcile.py ends here
# Thank you!