"""Same as v1, with filtering of free only spaces added, and more advanced validation."""
import uvicorn
from fastapi import FastAPI, Query
import redis

from tile38_fastapi import PARKING_LOCATIONS

app = FastAPI()


@app.get("/nearby-parking-locations")
async def get_nearby(
        latitude: float = Query(ge=-90, le=90),
        longitude: float = Query(ge=-180, le=180),
        free_only: bool = Query(
            description="If True only return no payment necessary locations",
            default=False,
        ),
        distance_meters: int = Query(
            ge=1,
            description="Distance from point to search for parking locations",
        ),
):
    if free_only:
        filters = ["WHERE", "properties.price == 0"]
    else:
        filters = []

    c = redis.Redis(host="localhost", port=9851, single_connection_client=True)

    return c.execute_command(
        "NEARBY", PARKING_LOCATIONS, *filters, "POINT", latitude, longitude, distance_meters)[1]


if __name__ == "__main__":
    uvicorn.run("api_v2:app")
