from routing_service import get_route


route = get_route(

    # Starting location
    22.575,
    88.42,

    # Incident location
    22.5726,
    88.3639,
)


print(
    "Distance:",
    route["distance_km"],
    "km"
)


print(
    "ETA:",
    route["eta_minutes"],
    "minutes"
)


print("\nDirections:")


for step in route["instructions"]:

    print(
        "-",
        step["text"]
    )