import json
from datetime import datetime, timezone

from database import get_connection


# ---------------------------------------------------
# CREATE RESOURCE
# ---------------------------------------------------

def create_resource(resource):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO resources (
            resource_id,
            name,
            resource_type,
            capacity,
            capabilities,
            equipment,
            location,
            latitude,
            longitude,
            status,
            current_assignment,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resource.resource_id,
            resource.name,
            resource.resource_type,
            resource.capacity,

            json.dumps(
                resource.capabilities
            ),

            json.dumps(
                resource.equipment
            ),

            resource.location,
            resource.latitude,
            resource.longitude,
            resource.status.value,
            resource.current_assignment,
            resource.created_at.isoformat(),
            resource.updated_at.isoformat()
        )
    )

    connection.commit()
    connection.close()

    return get_resource(
        resource.resource_id
    )


# ---------------------------------------------------
# GET ONE RESOURCE
# ---------------------------------------------------

def get_resource(resource_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM resources
        WHERE resource_id = ?
        """,
        (resource_id,)
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return _row_to_dict(row)


# ---------------------------------------------------
# GET ALL RESOURCES
# ---------------------------------------------------

def get_all_resources():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return [
        _row_to_dict(row)
        for row in rows
    ]


# ---------------------------------------------------
# UPDATE RESOURCE STATUS
# ---------------------------------------------------

def update_resource_status(
    resource_id,
    new_status
):

    resource = get_resource(
        resource_id
    )

    if resource is None:
        return None

    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    connection.execute(
        """
        UPDATE resources

        SET
            status = ?,
            updated_at = ?

        WHERE resource_id = ?
        """,
        (
            new_status,
            updated_at,
            resource_id
        )
    )

    connection.commit()
    connection.close()

    return get_resource(
        resource_id
    )


# ---------------------------------------------------
# NEW: UPDATE RESOURCE LIVE LOCATION
# ---------------------------------------------------

def update_resource_location(
    resource_id,
    latitude,
    longitude
):

    resource = get_resource(
        resource_id
    )

    if resource is None:
        return None


    updated_at = datetime.now(
        timezone.utc
    ).isoformat()


    connection = get_connection()


    connection.execute(
        """
        UPDATE resources

        SET
            latitude = ?,
            longitude = ?,
            updated_at = ?

        WHERE resource_id = ?
        """,
        (
            latitude,
            longitude,
            updated_at,
            resource_id
        )
    )


    connection.commit()
    connection.close()


    return get_resource(
        resource_id
    )


# ---------------------------------------------------
# CONVERT SQLITE ROW TO DICTIONARY
# ---------------------------------------------------

def _row_to_dict(row):

    return {
        "resource_id":
            row["resource_id"],

        "name":
            row["name"],

        "resource_type":
            row["resource_type"],

        "capacity":
            row["capacity"],

        "capabilities":
            json.loads(
                row["capabilities"]
            ),

        "equipment":
            json.loads(
                row["equipment"]
            ),

        "location":
            row["location"],

        "latitude":
            row["latitude"],

        "longitude":
            row["longitude"],

        "status":
            row["status"],

        "current_assignment":
            row["current_assignment"],

        "created_at":
            row["created_at"],

        "updated_at":
            row["updated_at"]
    }