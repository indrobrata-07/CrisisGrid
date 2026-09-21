from datetime import datetime, timezone


# ---------------------------------------------------
# HELPER: COMBINE CURRENT DESCRIPTION + HISTORY
# ---------------------------------------------------

def get_full_description(incident):
    parts = []

    for previous_description in incident.get("updates", []):
        parts.append(previous_description)

    parts.append(
        incident["description"]
    )

    return " ".join(parts).lower()


# ---------------------------------------------------
# 1. IMMEDIATE DANGER
# ---------------------------------------------------

def calculate_danger_score(incident):
    score = 0

    description = get_full_description(
        incident
    )

    # Extremely serious medical danger
    if any(
        phrase in description
        for phrase in [
            "unconscious",
            "not breathing",
            "severe bleeding",
            "heart attack",
            "critical condition"
        ]
    ):
        score += 60

    # People trapped
    if "trapped" in description:
        score += 30

    # Rapidly worsening danger
    if any(
        phrase in description
        for phrase in [
            "rising rapidly",
            "water rising rapidly",
            "fire spreading rapidly",
            "building collapsing",
            "collapsed building"
        ]
    ):
        score += 35

    # General dangerous conditions
    if any(
        phrase in description
        for phrase in [
            "water is rising",
            "water rising",
            "fire spreading",
            "smoke",
            "flooded"
        ]
    ):
        score += 20

    # Injuries
    if incident["injuries"] > 0:
        score += min(
            incident["injuries"] * 15,
            30
        )

    # Mobility problems
    if incident["mobility_issue"]:
        score += 10

    return min(score, 100)


# ---------------------------------------------------
# 2. VULNERABILITY
# ---------------------------------------------------

def calculate_vulnerability_score(incident):
    score = 0

    vulnerable_people = incident[
        "vulnerable_people"
    ]

    injuries = incident[
        "injuries"
    ]

    if vulnerable_people > 0:
        score += min(
            40 + (vulnerable_people * 10),
            70
        )

    if injuries > 0:
        score += min(
            injuries * 15,
            30
        )

    if incident["mobility_issue"]:
        score += 20

    return min(score, 100)


# ---------------------------------------------------
# 3. PEOPLE AFFECTED
# ---------------------------------------------------

def calculate_people_score(people):

    if people >= 50:
        return 100

    if people >= 20:
        return 80

    if people >= 10:
        return 60

    if people >= 5:
        return 40

    if people >= 2:
        return 20

    return 10


# ---------------------------------------------------
# 4. SITUATION DETERIORATION
# ---------------------------------------------------

def calculate_deterioration_score(incident):

    description = get_full_description(
        incident
    )

    severe_signals = [
        "rising rapidly",
        "getting worse rapidly",
        "spreading rapidly",
        "suddenly collapsed",
        "now trapped",
        "situation critical"
    ]

    worsening_signals = [
        "water is rising",
        "water rising",
        "getting worse",
        "worsening",
        "fire spreading",
        "flood increasing",
        "condition worsening"
    ]

    for phrase in severe_signals:
        if phrase in description:
            return 100

    for phrase in worsening_signals:
        if phrase in description:
            return 70

    return 0


# ---------------------------------------------------
# 5. WAITING TIME
# ---------------------------------------------------

def calculate_waiting_score(created_at):

    created_time = datetime.fromisoformat(
        created_at
    )

    now = datetime.now(
        timezone.utc
    )

    waiting_minutes = (
        now - created_time
    ).total_seconds() / 60

    if waiting_minutes >= 120:
        return 100

    if waiting_minutes >= 60:
        return 80

    if waiting_minutes >= 30:
        return 60

    if waiting_minutes >= 15:
        return 40

    if waiting_minutes >= 5:
        return 20

    return 0


# ---------------------------------------------------
# 6. RESOURCE URGENCY
# ---------------------------------------------------

def calculate_resource_urgency_score(resources):

    resources = [
        resource.lower()
        for resource in resources
    ]

    if any(
        resource in resources
        for resource in [
            "ambulance",
            "medical_team"
        ]
    ):
        return 100

    if "boat" in resources:
        return 80

    if "rescue_team" in resources:
        return 60

    if any(
        resource in resources
        for resource in [
            "medicine",
            "oxygen",
            "blood"
        ]
    ):
        return 70

    if any(
        resource in resources
        for resource in [
            "water",
            "food"
        ]
    ):
        return 30

    return 0


# ---------------------------------------------------
# CRITICAL OVERRIDE
# ---------------------------------------------------

def check_critical_override(incident):
    """
    Detect clearly life-threatening situations.

    For now we use the latest description for the override,
    rather than the full history.

    This helps prevent an old critical phrase from forcing
    the incident to remain critical forever.
    """

    description = incident[
        "description"
    ].lower()

    reasons = []


    if "not breathing" in description:
        reasons.append(
            "Person reported as not breathing"
        )


    if "unconscious" in description:
        reasons.append(
            "Person reported as unconscious"
        )


    if "severe bleeding" in description:
        reasons.append(
            "Severe bleeding reported"
        )


    if "heart attack" in description:
        reasons.append(
            "Possible heart attack reported"
        )


    # Structural collapse + trapped people
    if (
        (
            "building collapsing" in description
            or "building collapsed" in description
            or "collapsed building" in description
        )
        and "trapped" in description
    ):
        reasons.append(
            "People trapped in a collapsing or collapsed building"
        )


    return {
        "triggered": len(reasons) > 0,
        "reasons": reasons
    }


# ---------------------------------------------------
# FINAL PRIORITY CALCULATION
# ---------------------------------------------------

def calculate_priority(incident):

    danger = calculate_danger_score(
        incident
    )

    vulnerability = (
        calculate_vulnerability_score(
            incident
        )
    )

    people = calculate_people_score(
        incident["people_affected"]
    )

    deterioration = (
        calculate_deterioration_score(
            incident
        )
    )

    waiting = calculate_waiting_score(
        incident["created_at"]
    )

    resource_urgency = (
        calculate_resource_urgency_score(
            incident["required_resources"]
        )
    )


    # Normal weighted calculation
    weighted_score = (
        0.30 * danger
        + 0.20 * vulnerability
        + 0.20 * people
        + 0.15 * deterioration
        + 0.10 * waiting
        + 0.05 * resource_urgency
    )

    weighted_score = round(
        weighted_score,
        2
    )


    # Check life-threatening override
    critical_override = (
        check_critical_override(
            incident
        )
    )


    # Final score normally equals weighted score
    final_score = weighted_score


    # If an explicit life-threatening condition exists,
    # guarantee at least CRITICAL threshold.
    if critical_override["triggered"]:
        final_score = max(
            final_score,
            80
        )


    final_score = round(
        final_score,
        2
    )


    # Determine level
    if final_score >= 80:
        priority_level = "CRITICAL"

    elif final_score >= 60:
        priority_level = "HIGH"

    elif final_score >= 40:
        priority_level = "MEDIUM"

    else:
        priority_level = "LOW"


    return {
        "score": final_score,

        # Shows what the normal formula produced
        "weighted_score": weighted_score,

        "level": priority_level,

        "critical_override": (
            critical_override["triggered"]
        ),

        "override_reasons": (
            critical_override["reasons"]
        ),

        "breakdown": {
            "immediate_danger": danger,

            "vulnerability": vulnerability,

            "people_affected": people,

            "deterioration": deterioration,

            "waiting_time": waiting,

            "resource_urgency": resource_urgency
        }
    }