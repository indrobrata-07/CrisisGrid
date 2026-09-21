from resource_matcher import match_resources
from routing_service import get_route


# ---------------------------------------------------
# DISPATCH ENGINE
# ---------------------------------------------------

def build_dispatch_plan(
    incident,
    resources
):

    # -----------------------------------------------
    # 1. Make sure incident has GPS coordinates
    # -----------------------------------------------

    if (
        incident["latitude"] is None
        or incident["longitude"] is None
    ):
        raise ValueError(
            "Incident does not have GPS coordinates."
        )


    # -----------------------------------------------
    # 2. Run normal Resource Matcher first
    # -----------------------------------------------

    matching_result = match_resources(
        incident,
        resources
    )


    candidates = (
        matching_result[
            "all_candidates"
        ]
    )


    routed_candidates = []


    # -----------------------------------------------
    # 3. Calculate road route for every candidate
    # -----------------------------------------------

    for candidate in candidates:

        resource = candidate[
            "resource"
        ]


        # Can't route a resource without GPS
        if (
            resource["latitude"] is None
            or resource["longitude"] is None
        ):

            routed_candidates.append({

                **candidate,

                "route": None,

                "route_error": (
                    "Resource has no GPS coordinates"
                )
            })

            continue


        # -------------------------------------------
        # Ask GraphHopper for actual road route
        # -------------------------------------------

        try:

            route = get_route(

                resource["latitude"],
                resource["longitude"],

                incident["latitude"],
                incident["longitude"],
            )


            routed_candidates.append({

                **candidate,

                "route": route,

                "route_error": None
            })


        except Exception as error:

            # One failed route should NOT crash
            # the whole dispatch engine.

            routed_candidates.append({

                **candidate,

                "route": None,

                "route_error": str(error)
            })


    # -----------------------------------------------
    # 4. Build dispatch bundle
    #
    # Example:
    #
    # Incident needs:
    # boat
    # rescue_team
    # ambulance
    #
    # Could produce:
    #
    # Boat Team 01
    # +
    # Ambulance 02
    # -----------------------------------------------

    unmet_requirements = set(
        matching_result[
            "required_resources"
        ]
    )


    recommended_dispatches = []

    remaining_candidates = [
        candidate
        for candidate
        in routed_candidates
        if candidate["route"] is not None
    ]


    while (
        unmet_requirements
        and remaining_candidates
    ):

        best_candidate = None
        best_new_coverage = set()


        for candidate in remaining_candidates:

            coverage = set(
                candidate[
                    "covered_requirements"
                ]
            )


            new_coverage = (
                coverage
                & unmet_requirements
            )


            if not new_coverage:
                continue


            # ---------------------------------------
            # Candidate ranking
            #
            # Priority:
            #
            # 1. Covers more unmet requirements
            # 2. Has sufficient capacity
            # 3. Faster road ETA
            # 4. Higher suitability score
            # ---------------------------------------

            if best_candidate is None:

                best_candidate = candidate
                best_new_coverage = (
                    new_coverage
                )

                continue


            current_key = (

                len(new_coverage),

                int(
                    candidate[
                        "capacity_sufficient"
                    ]
                ),

                -candidate[
                    "route"
                ][
                    "eta_minutes"
                ],

                candidate[
                    "suitability_score"
                ],
            )


            best_key = (

                len(best_new_coverage),

                int(
                    best_candidate[
                        "capacity_sufficient"
                    ]
                ),

                -best_candidate[
                    "route"
                ][
                    "eta_minutes"
                ],

                best_candidate[
                    "suitability_score"
                ],
            )


            if current_key > best_key:

                best_candidate = (
                    candidate
                )

                best_new_coverage = (
                    new_coverage
                )


        # No candidate can satisfy anything else.
        if best_candidate is None:
            break


        recommended_dispatches.append({

            "resource":
                best_candidate[
                    "resource"
                ],

            "covers":
                sorted(
                    best_new_coverage
                ),

            "suitability_score":
                best_candidate[
                    "suitability_score"
                ],

            "capacity_sufficient":
                best_candidate[
                    "capacity_sufficient"
                ],

            "route":
                best_candidate[
                    "route"
                ],

            "reasons":
                best_candidate[
                    "reasons"
                ],
        })


        unmet_requirements -= (
            best_new_coverage
        )


        remaining_candidates.remove(
            best_candidate
        )


    # -----------------------------------------------
    # 5. Sort all routed candidates by ETA
    # -----------------------------------------------

    routed_candidates.sort(

        key=lambda candidate: (

            candidate["route"] is None,

            candidate["route"][
                "eta_minutes"
            ]
            if candidate["route"]
            else float("inf")
        )
    )


    # -----------------------------------------------
    # 6. Return dispatch recommendation
    # -----------------------------------------------

    return {

        "required_resources":
            matching_result[
                "required_resources"
            ],

        "recommended_dispatches":
            recommended_dispatches,

        "unmet_requirements":
            sorted(
                unmet_requirements
            ),

        "all_routed_candidates":
            routed_candidates,
    }