import os

import requests
from dotenv import load_dotenv


# ---------------------------------------------------
# LOAD API KEY
# ---------------------------------------------------

load_dotenv()


API_KEY = os.getenv(
    "GRAPHHOPPER_API_KEY"
)


if not API_KEY:
    raise RuntimeError(
        "GRAPHHOPPER_API_KEY was not found. "
        "Check your .env file."
    )


# ---------------------------------------------------
# GRAPHHOPPER CONFIG
# ---------------------------------------------------

BASE_URL = (
    "https://graphhopper.com/api/1/route"
)


# Reuse the HTTP connection instead of
# creating a new one for every route request.
session = requests.Session()


# ---------------------------------------------------
# GET ROUTE
# ---------------------------------------------------

def get_route(
    start_latitude,
    start_longitude,
    destination_latitude,
    destination_longitude,
):

    # -----------------------------------------------
    # Make sure coordinates actually exist
    # -----------------------------------------------

    if (
        start_latitude is None
        or start_longitude is None
        or destination_latitude is None
        or destination_longitude is None
    ):

        raise ValueError(
            "Both the resource and incident "
            "must have latitude and longitude."
        )


    # -----------------------------------------------
    # GraphHopper expects:
    #
    # latitude,longitude
    #
    # Example:
    # 22.5726,88.3639
    # -----------------------------------------------

    params = [

        (
            "point",
            f"{start_latitude},"
            f"{start_longitude}"
        ),

        (
            "point",
            f"{destination_latitude},"
            f"{destination_longitude}"
        ),

        (
            "profile",
            "car"
        ),

        (
            "locale",
            "en"
        ),

        (
            "instructions",
            "true"
        ),

        (
            "calc_points",
            "true"
        ),

        (
            "points_encoded",
            "false"
        ),

        (
            "key",
            API_KEY
        ),
    ]


    # -----------------------------------------------
    # Call GraphHopper
    # -----------------------------------------------

    response = session.get(
        BASE_URL,
        params=params,
        timeout=15
    )


    # Raise error for things like:
    # 401 / 403 / 429 / 500
    response.raise_for_status()


    data = response.json()


    # -----------------------------------------------
    # Validate response
    # -----------------------------------------------

    if (
        "paths" not in data
        or not data["paths"]
    ):

        raise ValueError(
            "GraphHopper could not find a route."
        )


    path = data["paths"][0]


    # -----------------------------------------------
    # Convert units
    #
    # GraphHopper:
    # distance -> meters
    # time     -> milliseconds
    # -----------------------------------------------

    distance_km = round(
        path["distance"] / 1000,
        2
    )


    eta_minutes = round(
        path["time"] / 60000,
        1
    )


    # -----------------------------------------------
    # TURN-BY-TURN INSTRUCTIONS
    # -----------------------------------------------

    instructions = []


    for instruction in path.get(
        "instructions",
        []
    ):

        instructions.append({

            "text":
                instruction.get(
                    "text"
                ),

            "distance_meters":
                round(
                    instruction.get(
                        "distance",
                        0
                    ),
                    1
                ),

            "time_seconds":
                round(
                    instruction.get(
                        "time",
                        0
                    ) / 1000,
                    1
                ),
        })


    # -----------------------------------------------
    # RETURN CLEAN RESQ ROUTE DATA
    # -----------------------------------------------

    return {

        "distance_km":
            distance_km,

        "eta_minutes":
            eta_minutes,

        "route_geometry":
            path.get(
                "points"
            ),

        "instructions":
            instructions,
    }