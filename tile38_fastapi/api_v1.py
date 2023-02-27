"""Most basic Tile38 and FastAPI API

Run the file, and visit the following for docs
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

Example query below
http://127.0.0.1:8000/nearby-parking-locations?latitude=11.7044525&longitude=48.0449558&distance_meters=1500
"""
import uvicorn
from fastapi import FastAPI, Query
import redis

from tile38_fastapi import PARKING_LOCATIONS


app = FastAPI()


@app.get("/nearby-parking-locations")
async def get_nearby(
        latitude: float = Query(ge=-90, le=90),
        longitude: float = Query(ge=-180, le=180),
        distance_meters: float = Query(
            ge=0.1,
            description="Distance from point to search for parking locations",
        ),
):
    c = redis.Redis(host="localhost", port=9851, single_connection_client=True)

    return c.execute_command(
        "NEARBY", PARKING_LOCATIONS, "POINT", longitude, latitude, distance_meters)


if __name__ == "__main__":
    uvicorn.run("tile38_fastapi.api_v1:app")
