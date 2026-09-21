from datetime import datetime, timezone

from database import get_connection


# ===================================================
# ASSIGN RESOURCES TO INCIDENT
# ===================================================

def assign_resources_to_incident(
    incident_id,
    resource_ids
):

    # Remove duplicate IDs while keeping order
    resource_ids = list(
        dict.fromkeys(resource_ids)
    )


    if not resource_ids:

        raise ValueError(
            "At least one resource must be assigned."
        )


    connection = get_connection()


    try:

        # Prevent simultaneous assignment conflicts
        connection.execute(
            "BEGIN IMMEDIATE"
        )


        # ============================================
        # 1. VERIFY INCIDENT
        # ============================================

        incident = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,)
        ).fetchone()


        if incident is None:

            raise ValueError(
                "Incident not found."
            )


        if incident["status"] == "resolved":

            raise ValueError(
                "Cannot assign resources "
                "to a resolved incident."
            )


        if incident["status"] == "in_progress":

            raise ValueError(
                "Incident is already in progress."
            )


        # ============================================
        # 2. VERIFY RESOURCES
        # ============================================

        resources = []


        for resource_id in resource_ids:

            resource = connection.execute(
                """
                SELECT *
                FROM resources
                WHERE resource_id = ?
                """,
                (resource_id,)
            ).fetchone()


            if resource is None:

                raise ValueError(
                    "Resource not found: "
                    f"{resource_id}"
                )


            if resource["status"] != "available":

                raise ValueError(
                    f"{resource['name']} "
                    "is not currently available."
                )


            resources.append(
                resource
            )


        # ============================================
        # 3. ASSIGNMENT TIME
        # ============================================

        assigned_at = datetime.now(
            timezone.utc
        ).isoformat()


        # ============================================
        # 4. ASSIGN EACH RESOURCE
        # ============================================

        for resource in resources:

            resource_id = (
                resource["resource_id"]
            )


            # ----------------------------------------
            # Create assignment record
            # ----------------------------------------

            connection.execute(
                """
                INSERT INTO
                incident_resource_assignments (

                    incident_id,
                    resource_id,
                    assigned_at,
                    status
                )

                VALUES (?, ?, ?, ?)
                """,
                (
                    incident_id,
                    resource_id,
                    assigned_at,
                    "assigned"
                )
            )


            # ----------------------------------------
            # Reserve resource
            # ----------------------------------------

            connection.execute(
                """
                UPDATE resources

                SET
                    status = ?,
                    current_assignment = ?,
                    updated_at = ?

                WHERE resource_id = ?
                """,
                (
                    "assigned",
                    incident_id,
                    assigned_at,
                    resource_id
                )
            )


        # ============================================
        # 5. UPDATE INCIDENT STATUS
        # ============================================

        legacy_team_id = (
            incident["assigned_team_id"]
            or resource_ids[0]
        )


        connection.execute(
            """
            UPDATE incidents

            SET
                status = ?,
                assigned_team_id = ?,
                updated_at = ?

            WHERE incident_id = ?
            """,
            (
                "assigned",
                legacy_team_id,
                assigned_at,
                incident_id
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise


    finally:

        connection.close()


    return get_incident_assignments(
        incident_id
    )


# ===================================================
# START INCIDENT RESPONSE
# ===================================================

def start_incident_response(
    incident_id
):

    connection = get_connection()


    try:

        connection.execute(
            "BEGIN IMMEDIATE"
        )


        # ============================================
        # 1. GET INCIDENT
        # ============================================

        incident = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,)
        ).fetchone()


        if incident is None:

            raise ValueError(
                "Incident not found."
            )


        if incident["status"] == "resolved":

            raise ValueError(
                "Resolved incident cannot be started."
            )


        if incident["status"] == "in_progress":

            raise ValueError(
                "Incident is already in progress."
            )


        if incident["status"] != "assigned":

            raise ValueError(
                "Incident must have assigned "
                "resources before response can start."
            )


        # ============================================
        # 2. GET ACTIVE ASSIGNMENTS
        # ============================================

        assignments = connection.execute(
            """
            SELECT *
            FROM incident_resource_assignments

            WHERE
                incident_id = ?
                AND status = 'assigned'
            """,
            (incident_id,)
        ).fetchall()


        if not assignments:

            raise ValueError(
                "No assigned resources were found "
                "for this incident."
            )


        started_at = datetime.now(
            timezone.utc
        ).isoformat()


        # ============================================
        # 3. MARK ASSIGNMENTS IN PROGRESS
        # ============================================

        connection.execute(
            """
            UPDATE incident_resource_assignments

            SET status = 'in_progress'

            WHERE
                incident_id = ?
                AND status = 'assigned'
            """,
            (incident_id,)
        )


        # ============================================
        # 4. MARK RESOURCES BUSY
        # ============================================

        for assignment in assignments:

            connection.execute(
                """
                UPDATE resources

                SET
                    status = 'busy',
                    updated_at = ?

                WHERE
                    resource_id = ?
                    AND current_assignment = ?
                """,
                (
                    started_at,
                    assignment["resource_id"],
                    incident_id
                )
            )


        # ============================================
        # 5. MARK INCIDENT IN PROGRESS
        # ============================================

        connection.execute(
            """
            UPDATE incidents

            SET
                status = 'in_progress',
                updated_at = ?

            WHERE incident_id = ?
            """,
            (
                started_at,
                incident_id
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise


    finally:

        connection.close()


    return get_incident_assignments(
        incident_id
    )


# ===================================================
# RESOLVE INCIDENT
# ===================================================

def resolve_incident_response(
    incident_id
):

    connection = get_connection()


    try:

        connection.execute(
            "BEGIN IMMEDIATE"
        )


        # ============================================
        # 1. GET INCIDENT
        # ============================================

        incident = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,)
        ).fetchone()


        if incident is None:

            raise ValueError(
                "Incident not found."
            )


        if incident["status"] == "resolved":

            raise ValueError(
                "Incident is already resolved."
            )


        if incident["status"] not in {
            "assigned",
            "in_progress"
        }:

            raise ValueError(
                "Incident must be assigned or "
                "in progress before it can be resolved."
            )


        # ============================================
        # 2. GET ACTIVE ASSIGNMENTS
        # ============================================

        assignments = connection.execute(
            """
            SELECT *
            FROM incident_resource_assignments

            WHERE
                incident_id = ?
                AND status IN (
                    'assigned',
                    'in_progress'
                )
            """,
            (incident_id,)
        ).fetchall()


        resolved_at = datetime.now(
            timezone.utc
        ).isoformat()


        # ============================================
        # 3. COMPLETE ASSIGNMENTS
        # ============================================

        connection.execute(
            """
            UPDATE incident_resource_assignments

            SET status = 'completed'

            WHERE
                incident_id = ?
                AND status IN (
                    'assigned',
                    'in_progress'
                )
            """,
            (incident_id,)
        )


        # ============================================
        # 4. RELEASE RESOURCES
        # ============================================

        for assignment in assignments:

            connection.execute(
                """
                UPDATE resources

                SET
                    status = 'available',
                    current_assignment = NULL,
                    updated_at = ?

                WHERE
                    resource_id = ?
                    AND current_assignment = ?
                """,
                (
                    resolved_at,
                    assignment["resource_id"],
                    incident_id
                )
            )


        # ============================================
        # 5. RESOLVE INCIDENT
        # ============================================

        connection.execute(
            """
            UPDATE incidents

            SET
                status = 'resolved',
                updated_at = ?

            WHERE incident_id = ?
            """,
            (
                resolved_at,
                incident_id
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise


    finally:

        connection.close()


    return get_incident_assignments(
        incident_id
    )


# ===================================================
# GET ASSIGNED RESOURCES
# ===================================================

def get_incident_assignments(
    incident_id
):

    connection = get_connection()


    rows = connection.execute(
        """
        SELECT

            assignment.incident_id,

            assignment.resource_id,

            assignment.assigned_at,

            assignment.status
                AS assignment_status,

            resource.name,

            resource.resource_type,

            resource.capacity,

            resource.location,

            resource.latitude,

            resource.longitude,

            resource.status
                AS resource_status,

            resource.current_assignment

        FROM
            incident_resource_assignments
            AS assignment

        JOIN
            resources AS resource

        ON
            resource.resource_id
            =
            assignment.resource_id

        WHERE
            assignment.incident_id = ?

        ORDER BY
            assignment.assigned_at ASC
        """,
        (incident_id,)
    ).fetchall()


    connection.close()


    assignments = []


    for row in rows:

        assignments.append(
            {
                "incident_id":
                    row["incident_id"],

                "resource_id":
                    row["resource_id"],

                "name":
                    row["name"],

                "resource_type":
                    row["resource_type"],

                "capacity":
                    row["capacity"],

                "location":
                    row["location"],

                "latitude":
                    row["latitude"],

                "longitude":
                    row["longitude"],

                "assignment_status":
                    row[
                        "assignment_status"
                    ],

                "resource_status":
                    row[
                        "resource_status"
                    ],

                "current_assignment":
                    row[
                        "current_assignment"
                    ],

                "assigned_at":
                    row["assigned_at"],
            }
        )


    return assignments