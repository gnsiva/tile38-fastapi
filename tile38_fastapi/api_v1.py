"""Most basic Tile38 and FastAPI API

Run the file, and visit the following for docs
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

Example query below
http://127.0.0.1:8000/nearby-parking-locations?latitude=11.7044525&longitude=48.0449558&distance_meters=1500
"""
import uvicorn
from fastapi import FastAPI
import redis


app = FastAPI()


@app.get("/nearby-parking-locations")
async def get_nearby(
        latitude: float,
        longitude: float,
        distance_meters: int,
):
    c = redis.Redis(host="localhost", port=9851, single_connection_client=True)

    return c.execute_command(
        "NEARBY", "parking-locations", "POINT", latitude, longitude, distance_meters)


if __name__ == "__main__":
    uvicorn.run("api_v1:app")
