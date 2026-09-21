# ---------------------------------------------------
# RESOURCE MATCHER
# ---------------------------------------------------


# A requirement may be satisfied by different
# resource properties.
#
# Example:
# "boat" can be equipment on a rescue team.
# "ambulance" may appear as the resource type.

REQUIREMENT_ALIASES = {

    "rescue_team": {
        "rescue_team",
        "flood_rescue",
        "evacuation"
    },

    "boat": {
        "boat"
    },

    "ambulance": {
        "ambulance",
        "medical_transport"
    },

    "medical_team": {
        "medical_team",
        "emergency_medical_support"
    },

    "medicine": {
        "medicine"
    },

    "oxygen": {
        "oxygen"
    },

    "blood": {
        "blood"
    },

    "water": {
        "water"
    },

    "food": {
        "food"
    }
}


# ---------------------------------------------------
# NORMALIZE TEXT
# ---------------------------------------------------

def normalize(value):

    return (
        value
        .strip()
        .lower()
        .replace(" ", "_")
    )


# ---------------------------------------------------
# BUILD SEARCHABLE TOKENS FOR A RESOURCE
# ---------------------------------------------------

def get_resource_tokens(resource):

    tokens = {
        normalize(
            resource["resource_type"]
        )
    }


    for capability in resource[
        "capabilities"
    ]:

        tokens.add(
            normalize(capability)
        )


    for equipment in resource[
        "equipment"
    ]:

        tokens.add(
            normalize(equipment)
        )


    return tokens


# ---------------------------------------------------
# CHECK WHETHER RESOURCE SATISFIES REQUIREMENT
# ---------------------------------------------------

def resource_matches_requirement(
    resource,
    requirement
):

    requirement = normalize(
        requirement
    )


    resource_tokens = (
        get_resource_tokens(
            resource
        )
    )


    accepted_tokens = (
        REQUIREMENT_ALIASES.get(
            requirement,
            {requirement}
        )
    )


    return bool(
        resource_tokens
        & accepted_tokens
    )


# ---------------------------------------------------
# DETERMINE RELEVANT CAPACITY REQUIREMENT
# ---------------------------------------------------

def get_required_capacity(
    incident,
    resource
):

    resource_type = normalize(
        resource["resource_type"]
    )


    capabilities = {
        normalize(capability)
        for capability
        in resource["capabilities"]
    }


    # Rescue / evacuation resources should ideally
    # handle the number of people affected.
    if (
        resource_type == "rescue_team"
        or "evacuation" in capabilities
        or "flood_rescue" in capabilities
    ):

        return max(
            incident["people_affected"],
            1
        )


    # Medical resources mainly need capacity
    # relative to injured people.
    if (
        resource_type
        in {
            "ambulance",
            "medical_team"
        }
        or "emergency_medical_support"
        in capabilities
    ):

        return max(
            incident["injuries"],
            1
        )


    return 1


# ---------------------------------------------------
# EVALUATE ONE RESOURCE
# ---------------------------------------------------

def evaluate_resource(
    incident,
    resource
):

    required_resources = [
        normalize(requirement)
        for requirement
        in incident["required_resources"]
    ]


    # -----------------------------------------------
    # Resource must currently be available
    # -----------------------------------------------

    if resource["status"] != "available":

        return None


    # -----------------------------------------------
    # Determine which requirements it can cover
    # -----------------------------------------------

    covered_requirements = []


    for requirement in required_resources:

        if resource_matches_requirement(
            resource,
            requirement
        ):

            covered_requirements.append(
                requirement
            )


    # Resource is irrelevant to this incident.
    if not covered_requirements:

        return None


    # -----------------------------------------------
    # Capacity
    # -----------------------------------------------

    required_capacity = (
        get_required_capacity(
            incident,
            resource
        )
    )


    capacity_sufficient = (
        resource["capacity"]
        >= required_capacity
    )


    # -----------------------------------------------
    # Suitability score
    #
    # NOTE:
    # This is NOT the incident priority score.
    #
    # It only measures how suitable this resource is.
    # -----------------------------------------------

    total_requirements = max(
        len(required_resources),
        1
    )


    coverage_ratio = (
        len(covered_requirements)
        / total_requirements
    )


    score = 0


    # Requirement coverage = biggest factor
    score += (
        coverage_ratio * 70
    )


    # Capacity
    if capacity_sufficient:
        score += 20
    else:
        score += 5


    # Available status
    score += 10


    score = round(
        min(score, 100),
        2
    )


    # -----------------------------------------------
    # Explainability
    # -----------------------------------------------

    reasons = []


    for requirement in covered_requirements:

        reasons.append(
            f"Matches required resource: "
            f"{requirement}"
        )


    if capacity_sufficient:

        reasons.append(
            (
                f"Capacity sufficient: "
                f"{resource['capacity']} "
                f">= {required_capacity}"
            )
        )

    else:

        reasons.append(
            (
                f"Capacity may be insufficient: "
                f"{resource['capacity']} "
                f"< {required_capacity}"
            )
        )


    reasons.append(
        "Resource is currently available"
    )


    return {

        "resource":
            resource,

        "covered_requirements":
            covered_requirements,

        "capacity_required":
            required_capacity,

        "capacity_sufficient":
            capacity_sufficient,

        "suitability_score":
            score,

        "reasons":
            reasons
    }


# ---------------------------------------------------
# FIND BEST RESOURCE COMBINATION
# ---------------------------------------------------

def match_resources(
    incident,
    resources
):

    required_resources = [
        normalize(requirement)
        for requirement
        in incident[
            "required_resources"
        ]
    ]


    candidates = []


    # -----------------------------------------------
    # Evaluate all resources
    # -----------------------------------------------

    for resource in resources:

        result = evaluate_resource(
            incident,
            resource
        )


        if result is not None:

            candidates.append(
                result
            )


    # -----------------------------------------------
    # Sort strongest candidates first
    # -----------------------------------------------

    candidates.sort(

        key=lambda candidate: (
            len(
                candidate[
                    "covered_requirements"
                ]
            ),

            candidate[
                "capacity_sufficient"
            ],

            candidate[
                "suitability_score"
            ]
        ),

        reverse=True
    )


    # -----------------------------------------------
    # Build a resource bundle
    #
    # Example:
    #
    # Boat Team covers:
    # rescue_team + boat
    #
    # Ambulance covers:
    # ambulance + medical_team
    # -----------------------------------------------

    unmet_requirements = set(
        required_resources
    )


    selected_resources = []


    remaining_candidates = (
        candidates.copy()
    )


    while (
        unmet_requirements
        and remaining_candidates
    ):

        best_candidate = None

        best_new_coverage = set()


        for candidate in remaining_candidates:

            candidate_coverage = set(
                candidate[
                    "covered_requirements"
                ]
            )


            new_coverage = (
                candidate_coverage
                & unmet_requirements
            )


            if (
                len(new_coverage)
                > len(best_new_coverage)
            ):

                best_candidate = candidate

                best_new_coverage = (
                    new_coverage
                )


            elif (
                len(new_coverage)
                == len(best_new_coverage)
                and best_candidate is not None
                and candidate[
                    "suitability_score"
                ]
                > best_candidate[
                    "suitability_score"
                ]
            ):

                best_candidate = candidate

                best_new_coverage = (
                    new_coverage
                )


        if (
            best_candidate is None
            or not best_new_coverage
        ):

            break


        selected_resources.append(
            best_candidate
        )


        unmet_requirements -= (
            best_new_coverage
        )


        remaining_candidates.remove(
            best_candidate
        )


    # -----------------------------------------------
    # Return explainable result
    # -----------------------------------------------

    return {

        "required_resources":
            required_resources,

        "recommended_resources":
            selected_resources,

        "unmet_requirements":
            sorted(
                unmet_requirements
            ),

        "all_candidates":
            candidates
    }