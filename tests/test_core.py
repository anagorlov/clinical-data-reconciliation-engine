# test_core.py
# EHR Clinical Data Reconciliation Engine
# By: Anastasiya Gorlov
# Wed, March 18th, 2026
# This file is for the 5 unit tests covering core logic
# This file is responsible for checking one small piece of code that it works
# We give it input and check to get the expected output
# Great for future, since it will check if something breaks our tests will catch it

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
import sys
import os

# + backend folder so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".." "backend"))
from reconcile import detect_duplicates, calculate_source_weights
from validate import run_basic_checks


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# TEST 1 - duplicate detection finds the same drug

# Testing: giving it two sources with the same Metformin drug
# Result: should find 1 duplicate
# assert = checks for it to be TRUE, if not FAIL

sources = [
    {'system': 'Hospital', 'medication': 'Metformin 1000mg'},
    {'system': 'Clinic', 'medication': 'Metformin 500mg'},
]
duplicates = detect_duplicates(sources)
assert len(duplicates) == 1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# TEST 2 - no duplicates for different drugs

# Testing: giving it two different drugs
# Result: should find 0 duplicates
# list is empty for no duplicates

sources = [
        {'system': 'Hospital', 'medication': 'Aspirin 81mg'},
        {'system': 'Clinic', 'medication': 'Metformin 500mg'},
    ]
duplicates = detect_duplicates(sources)
assert duplicates == []

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# TEST 3 - high reliability gets higher weight than low

# Testing: high reliability should always get a higher weight than low

sources = [
        {'system': 'Hospital', 'source_reliability': 'high'},
        {'system': 'Pharmacy', 'source_reliability': 'low'},
    ]
weights = calculate_source_weights(sources)
assert weights['Hospital'] > weights['Pharmacy']

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# TEST 4 - implausible blood pressure gets flagged as high

# Testing: blood pressure 340/180 is not possible
# Result: basic checks should catch it and flag as high severity

record = {
    'vital_signs': {'blood_pressure': '340/180'},
    'last_updated': '2025-01-01'
}

# find any issues related to blood pressure
# should find at least 1 issues and it should be high severity

issues = run_basic_checks(record)
bp_issues = [i for i in issues if 'blood_pressure' in i['field']]
assert len(bp_issues) > 0
assert bp_issues[0]['severity'] == 'high'


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
# TEST 5 - empty allergies gets flagged as medium

# Testing: empty list of allergies should be flagged as medium severity
# Result: find issues related to allergies, should have found at least 1

record = {
        'allergies': [],
        'vital_signs': {'blood_pressure': '120/80'},
        'last_updated': '2025-01-01'
    }
issues = run_basic_checks(record)
allergy_issues = [i for i in issues if i['field'] == 'allergies']
assert len(allergy_issues) > 0  # should have found at least 1
assert allergy_issues[0]['severity'] == 'medium'

# end of of the test_core.py