from ai_extractor import extract_incident_data


report = """
Water is entering our house.
My grandmother cannot walk.
There are four of us inside.
"""


result = extract_incident_data(report)


print("Disaster type:", result.disaster_type)
print("People affected:", result.people_affected)
print("Vulnerable people:", result.vulnerable_people)
print("Injuries:", result.injuries)
print("Mobility issue:", result.mobility_issue)
print("Required resources:", result.required_resources)
print("Uncertainty:", result.uncertainty_notes)