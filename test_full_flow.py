import sys
import requests


# ===================================================
# CONFIGURATION
# ===================================================

BASE_URL = "http://127.0.0.1:8000"


# ===================================================
# SMALL HELPER
# ===================================================

def request(method, endpoint, **kwargs):
    """
    Send a request to the CrisisGrid backend.

    If something goes wrong, print the backend's
    response clearly and stop the test.
    """

    url = BASE_URL + endpoint

    try:
        response = requests.request(
            method,
            url,
            timeout=60,
            **kwargs
        )

    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to ResQ.")
        print("Make sure this is running:")
        print()
        print("uvicorn main:app --reload")
        sys.exit(1)

    except requests.exceptions.RequestException as error:
        print("\n❌ Request failed:")
        print(error)
        sys.exit(1)


    if not response.ok:

        print("\n❌ BACKEND ERROR")
        print("------------------------------")
        print("Endpoint:", endpoint)
        print("Status:", response.status_code)

        try:
            print("Response:", response.json())
        except Exception:
            print("Response:", response.text)

        print("------------------------------")

        sys.exit(1)


    return response.json()


# ===================================================
# STEP 1
# CHECK BACKEND
# ===================================================

print()
print("=" * 55)
print("🚨 RESQ END-TO-END BACKEND TEST")
print("=" * 55)


print("\n[1/8] Checking backend...")


home = request(
    "GET",
    "/"
)


print(
    "✅ Backend connected:",
    home.get("message")
)


# ===================================================
# STEP 2
# CREATE INCIDENT
# ===================================================

print("\n[2/8] Creating emergency incident...")


incident_payload = {

    "description": (
        "Flood water is rising around a house. "
        "Four people are trapped on the upper floor "
        "and need evacuation by boat."
    ),

    "location":
        "Central Kolkata",

    "latitude":
        22.5726,

    "longitude":
        88.3639
}


incident_response = request(
    "POST",
    "/incidents",
    json=incident_payload
)


incident = incident_response[
    "incident"
]


incident_id = incident[
    "incident_id"
]


print("✅ Incident created")
print("   ID:", incident_id)
print(
    "   Disaster:",
    incident["disaster_type"]
)
print(
    "   People:",
    incident["people_affected"]
)
print(
    "   Required resources:",
    incident["required_resources"]
)


priority = incident_response[
    "priority"
]


print(
    "   Priority:",
    priority["score"],
    "-",
    priority["level"]
)


# ===================================================
# STEP 3
# CREATE TEST RESOURCES
# ===================================================

print("\n[3/8] Creating rescue resources...")


resource_1_payload = {

    "name":
        "E2E Boat Team Alpha",

    "resource_type":
        "rescue_team",

    "capacity":
        6,

    "capabilities": [
        "flood_rescue",
        "evacuation"
    ],

    "equipment": [
        "boat",
        "life_jackets"
    ],

    "location":
        "Sector 5 Rescue Base",

    "latitude":
        22.5750,

    "longitude":
        88.4200
}


resource_2_payload = {

    "name":
        "E2E Boat Team Bravo",

    "resource_type":
        "rescue_team",

    "capacity":
        6,

    "capabilities": [
        "flood_rescue",
        "evacuation"
    ],

    "equipment": [
        "boat",
        "life_jackets",
        "first_aid_kit"
    ],

    "location":
        "Sealdah Rescue Base",

    "latitude":
        22.5708,

    "longitude":
        88.3745
}


resource_1 = request(
    "POST",
    "/resources",
    json=resource_1_payload
)


resource_2 = request(
    "POST",
    "/resources",
    json=resource_2_payload
)


print(
    "✅ Created:",
    resource_1["name"]
)


print(
    "✅ Created:",
    resource_2["name"]
)


# ===================================================
# STEP 4
# RESOURCE MATCHING
# ===================================================

print("\n[4/8] Running resource matcher...")


matching = request(
    "GET",
    f"/incidents/{incident_id}/resource-matches"
)


matching_result = matching[
    "resource_matching"
]


candidates = matching_result[
    "all_candidates"
]


print(
    f"✅ Found {len(candidates)} "
    "suitable/partial candidate(s)"
)


for candidate in candidates:

    resource = candidate[
        "resource"
    ]

    print()
    print(
        "   •",
        resource["name"]
    )

    print(
        "     Covers:",
        candidate[
            "covered_requirements"
        ]
    )

    print(
        "     Suitability:",
        candidate[
            "suitability_score"
        ]
    )


# ===================================================
# STEP 5
# DISPATCH RECOMMENDATION
# ===================================================

print(
    "\n[5/8] Calculating road routes "
    "and dispatch recommendation..."
)


dispatch_response = request(
    "GET",
    (
        f"/incidents/"
        f"{incident_id}/"
        "dispatch-recommendation"
    )
)


dispatch_plan = dispatch_response[
    "dispatch_plan"
]


recommended = dispatch_plan[
    "recommended_dispatches"
]


unmet = dispatch_plan[
    "unmet_requirements"
]


if not recommended:

    print()
    print(
        "❌ CrisisGrid could not recommend "
        "any dispatch resources."
    )

    print(
        "Unmet requirements:",
        unmet
    )

    sys.exit(1)


print(
    f"✅ Recommended "
    f"{len(recommended)} resource(s)"
)


resource_ids = []


for recommendation in recommended:

    resource = recommendation[
        "resource"
    ]

    route = recommendation[
        "route"
    ]

    resource_ids.append(
        resource["resource_id"]
    )


    print()
    print(
        "🚑",
        resource["name"]
    )

    print(
        "   Covers:",
        recommendation["covers"]
    )

    print(
        "   Capacity sufficient:",
        recommendation[
            "capacity_sufficient"
        ]
    )

    print(
        "   Distance:",
        route["distance_km"],
        "km"
    )

    print(
        "   ETA:",
        route["eta_minutes"],
        "minutes"
    )


if unmet:

    print()
    print(
        "⚠️ Unmet requirements:",
        unmet
    )

else:

    print()
    print(
        "✅ All incident requirements covered"
    )


# ===================================================
# STEP 6
# ASSIGN RESOURCES
# ===================================================

print(
    "\n[6/8] Operator accepting "
    "dispatch recommendation..."
)


assignment_payload = {

    "resource_ids":
        resource_ids
}


assignment_response = request(
    "POST",
    f"/incidents/{incident_id}/assign",
    json=assignment_payload
)


assigned_incident = assignment_response[
    "incident"
]


print(
    "✅ Resources assigned"
)


print(
    "   Incident status:",
    assigned_incident["status"]
)


for assignment in assignment_response[
    "assignments"
]:

    print(
        "   •",
        assignment["name"],
        "→",
        assignment["resource_status"]
    )


# ===================================================
# STEP 7
# START RESPONSE
# ===================================================

print(
    "\n[7/8] Starting emergency response..."
)


start_response = request(
    "POST",
    f"/incidents/{incident_id}/start"
)


started_incident = start_response[
    "incident"
]


print(
    "✅ Emergency response started"
)


print(
    "   Incident status:",
    started_incident["status"]
)


for assignment in start_response[
    "assignments"
]:

    print(
        "   •",
        assignment["name"]
    )

    print(
        "     Assignment:",
        assignment[
            "assignment_status"
        ]
    )

    print(
        "     Resource:",
        assignment[
            "resource_status"
        ]
    )


# ===================================================
# STEP 8
# RESOLVE INCIDENT
# ===================================================

print(
    "\n[8/8] Resolving incident..."
)


resolve_response = request(
    "POST",
    f"/incidents/{incident_id}/resolve"
)


resolved_incident = resolve_response[
    "incident"
]


print(
    "✅ Incident resolved"
)


print(
    "   Incident status:",
    resolved_incident["status"]
)


all_resources_released = True


for assignment in resolve_response[
    "assignments"
]:

    print()
    print(
        "   •",
        assignment["name"]
    )

    print(
        "     Assignment:",
        assignment[
            "assignment_status"
        ]
    )

    print(
        "     Resource:",
        assignment[
            "resource_status"
        ]
    )

    print(
        "     Current assignment:",
        assignment[
            "current_assignment"
        ]
    )


    if (
        assignment[
            "resource_status"
        ]
        != "available"
    ):

        all_resources_released = False


    if (
        assignment[
            "current_assignment"
        ]
        is not None
    ):

        all_resources_released = False


# ===================================================
# FINAL VERIFICATION
# ===================================================

print()
print("=" * 55)


if (
    resolved_incident["status"]
    == "resolved"
    and all_resources_released
):

    print(
        "🔥 CrisisGrid END-TO-END TEST PASSED 🔥"
    )

    print()
    print(
        "Report → AI → Priority → Matching"
    )

    print(
        "→ Routing → Dispatch → Assignment"
    )

    print(
        "→ Response → Resolution → Release"
    )


else:

    print(
        "⚠️ TEST FINISHED, "
        "BUT FINAL STATE WAS NOT CORRECT"
    )


print("=" * 55)
print()