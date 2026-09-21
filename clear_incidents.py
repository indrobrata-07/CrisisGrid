from database import get_connection


def clear_incidents():

    connection = get_connection()

    try:

        connection.execute(
            "BEGIN IMMEDIATE"
        )

        # ------------------------------------------------
        # 1. Remove incident-resource assignment records
        # ------------------------------------------------

        connection.execute(
            """
            DELETE FROM incident_resource_assignments
            """
        )


        # ------------------------------------------------
        # 2. Release resources that were assigned/busy
        # ------------------------------------------------

        connection.execute(
            """
            UPDATE resources

            SET
                status = CASE
                    WHEN status IN ('assigned', 'busy')
                    THEN 'available'
                    ELSE status
                END,

                current_assignment = NULL

            WHERE current_assignment IS NOT NULL
            """
        )


        # ------------------------------------------------
        # 3. Delete all incidents
        # ------------------------------------------------

        connection.execute(
            """
            DELETE FROM incidents
            """
        )


        connection.commit()

        print()
        print("✅ All incidents cleared.")
        print("✅ Assignments cleared.")
        print("✅ Assigned/busy resources released.")
        print("✅ Resources themselves were kept.")
        print()


    except Exception as error:

        connection.rollback()

        print()
        print("❌ Could not clear incidents:")
        print(error)
        print()


    finally:

        connection.close()


if __name__ == "__main__":
    clear_incidents()