import json
from datetime import datetime, timezone

from database import get_connection


# ---------------------------------------------------
# CREATE INCIDENT
# ---------------------------------------------------

def create_incident(incident):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO incidents (
            incident_id,
            description,
            location,
            disaster_type,
            people_affected,
            vulnerable_people,
            injuries,
            mobility_issue,
            danger_level,
            required_resources,
            status,
            assigned_team_id,
            created_at,
            updated_at,
            updates,
            latitude,
            longitude
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            incident.incident_id,

            incident.description,

            incident.location,

            incident.disaster_type,

            incident.people_affected,

            incident.vulnerable_people,

            incident.injuries,

            int(
                incident.mobility_issue
            ),

            incident.danger_level,

            json.dumps(
                incident.required_resources
            ),

            incident.status.value,

            incident.assigned_team_id,

            incident.created_at.isoformat(),

            incident.updated_at.isoformat(),

            json.dumps(
                incident.updates
            ),

            # NEW
            incident.latitude,

            # NEW
            incident.longitude
        )
    )

    connection.commit()
    connection.close()

    return get_incident(
        incident.incident_id
    )


# ---------------------------------------------------
# GET ONE INCIDENT
# ---------------------------------------------------

def get_incident(
    incident_id
):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM incidents
        WHERE incident_id = ?
        """,
        (
            incident_id,
        )
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return _row_to_dict(
        row
    )


# ---------------------------------------------------
# GET ALL INCIDENTS
# ---------------------------------------------------

def get_all_incidents():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM incidents
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return [
        _row_to_dict(row)
        for row in rows
    ]


# ---------------------------------------------------
# UPDATE INCIDENT USING AI EXTRACTION
# ---------------------------------------------------

def update_incident_from_ai(
    incident_id,
    new_description,
    extracted
):

    incident = get_incident(
        incident_id
    )

    if incident is None:
        return None


    previous_updates = list(
        incident["updates"]
    )


    current_description = (
        incident["description"]
        .strip()
    )


    # Avoid duplicate consecutive history entries
    if (
        not previous_updates
        or previous_updates[-1].strip()
        != current_description
    ):

        previous_updates.append(
            current_description
        )


    updated_at = datetime.now(
        timezone.utc
    ).isoformat()


    connection = get_connection()


    connection.execute(
        """
        UPDATE incidents

        SET
            description = ?,
            disaster_type = ?,
            people_affected = ?,
            vulnerable_people = ?,
            injuries = ?,
            mobility_issue = ?,
            required_resources = ?,
            updates = ?,
            updated_at = ?

        WHERE incident_id = ?
        """,
        (
            new_description,

            extracted.disaster_type,

            extracted.people_affected,

            extracted.vulnerable_people,

            extracted.injuries,

            int(
                extracted.mobility_issue
            ),

            json.dumps(
                extracted.required_resources
            ),

            json.dumps(
                previous_updates
            ),

            updated_at,

            incident_id
        )
    )


    connection.commit()
    connection.close()


    return get_incident(
        incident_id
    )


# ---------------------------------------------------
# CONVERT SQLITE ROW TO NORMAL DICTIONARY
# ---------------------------------------------------

def _row_to_dict(row):

    return {
        "incident_id":
            row["incident_id"],

        "description":
            row["description"],

        "location":
            row["location"],

        # NEW
        "latitude":
            row["latitude"],

        # NEW
        "longitude":
            row["longitude"],

        "disaster_type":
            row["disaster_type"],

        "people_affected":
            row["people_affected"],

        "vulnerable_people":
            row["vulnerable_people"],

        "injuries":
            row["injuries"],

        "mobility_issue":
            bool(
                row["mobility_issue"]
            ),

        "danger_level":
            row["danger_level"],

        "required_resources":
            json.loads(
                row["required_resources"]
            ),

        "status":
            row["status"],

        "assigned_team_id":
            row["assigned_team_id"],

        "created_at":
            row["created_at"],

        "updated_at":
            row["updated_at"],

        "updates":
            json.loads(
                row["updates"]
            ),
    }