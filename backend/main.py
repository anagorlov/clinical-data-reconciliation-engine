# main.py
# EHR Clinical Data Reconciliation Engine
# By: Anastasiya Gorlov 
# Tuesday, March 17th, 2026 
# Here we create our web server and the two API endpoints

# BACKEND API

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# libraries
from fastapi import FastAPI, HTTPException, Depends # our web server
from fastapi.middleware.cors import CORSMiddleware # frontend talks to backend
from fastapi.security.api_key import APIKeyHeader # API Key protection
import os # reading secret API key

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# App Setup
# creating our web server
app = FastAPI(
    title="Clinical Data Reconciliation Engine",
    description="AI-powered EHR data reconciliation API",
    version ="1.0"
)
# allowing frontend to talk to backend
# this is needed so the browser DOES NOT block the connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allows any webpage to connect
    allow_methods=["*"], # allows any type to request
    allow_headers=["*"], # allows any headers
)
print("App is set up!")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# Requirement: Basic API key protection

# Everyone who wants to call our API needs to
# INCLUDE THIS KEY in the request(if not, it will be rejected)

# our secret key
# using default key if nothing is set (for testing)
# + reads the key from env. variables
API_KEY = os.getenv("APP_API_KEY","dev-key-123")

# telling FastAPI to look for "x-api-key" in the request header
api_key_header = APIKeyHeader(name="x-api-key")

# checking requests for valid API key, 
# if wrong = reject, if right = let the request through
def verify_api_key(key:str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Incorrect API key.")
    return key

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# In-memory cache: saves money by not calling Claude twice for same request

cache = {} #empty dictionary to store responses

# convering the data into string so we can use it as a key
def make_cache_key(prefix: str, data: dict) -> str:
    import json
    return f"{prefix}:{json.dumps(data, sort_keys=True)}"


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`

# Requirement: POST /api/reconcile/medication

# Endpoint 1
# This is the part where our endpoint1 receives conflictng medication records 
# and sends them to Claude, after it returns the reconciled result

@app.post ("/api/reconcile/medication")
# payload = the patient record sent from the frontend
async def reconcile_endpoint(payload: dict, api_key: str = Depends(verify_api_key)):

    # making sure sources are included
    if "sources" not in payload or not payload["sources"]:
        raise HTTPException(status_code=400, detail="sources field is required")
    
    # checking cache before calling Claude
    # call Claude (function is built in reconcile.py)
    # save our cache and return the result
    cache_key = make_cache_key("reconcile", payload)
    if cache_key in cache:
        print("returning cached result!")
        return cache[cache_key]

    try:
        from reconcile import reconcile_medication
        result = await reconcile_medication(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    cache[cache_key] = result
    return result

# Endpoint 2

# This is where endpoint2 receives the patients record
# It sends it to Claude, and returns a quality score with any issues

@app.post ("/api/validate/data-quality")
# payload = the patient record sent from the frontend
async def validate_endpoint(payload: dict, api_key: str = Depends(verify_api_key)):

    # making sure that the records are not empty
    if not payload:
        raise HTTPException(status_code=400, detail="patient record can not be empty" )
    
    # checking cache before calling Claude
    # call Claude (function built in validate.py)
    # save our cache and return the result
    cache_key = make_cache_key("validate", payload)
    if cache_key in cache:
        return cache[cache_key]

    try:
        from validate import validate_data_quality
        result = await validate_data_quality(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    cache[cache_key] = result
    return result

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# Health check endpoint
# this is a simple test to make sure our server is running
# visit http://localhost:8000 in browser to test it

@app.get('/') #visiting a page with GET
def root():
    return {'status': 'running', 'message': 'EHR Reconciliation API is live'}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# Run the server
# STARTS OUR web server when we run python main.py!! YAY!

if __name__ == '__main__':

    import uvicorn #runs our FastAPI server
 
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)

    # host='0.0.0.0' = accept connections from anywhere
    # port=8000 = run on port 8000
    # reload=True = automatically restart when we change code

    
# End of our main.py
# Thank you! 



