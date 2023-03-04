"""API used for benchmarking.

- Includes ability to query PostGIS or Tile38.
"""
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum

import geoalchemy2.functions as func
import redis
import uvicorn
from fastapi import FastAPI, Query
from sqlalchemy import Select
from sqlalchemy.orm import sessionmaker

from tile38_fastapi import PARKING_LOCATIONS
from tile38_fastapi.db import create_postgis_engine, ParkingLocationsPostGis

app = FastAPI(
    title="Tile38 and PostGIS - FastAPI",
)


class Database(str, Enum):
    POSTGIS = "postgis"
    TILE38 = "tile38"


@dataclass
class NearbyQuery:
    latitude: float
    longitude: float
    free_only: bool
    radius: float


class Retriever(ABCMeta):
    @abstractmethod
    def retrieve(self, query: NearbyQuery):
        pass


class Tile38Retriever:
    """This class can easily be improved by using a connection pool to Tile38 and async queries"""
    async def retrieve(self, query: NearbyQuery):
        conn = redis.Redis(host="localhost", port=9851, single_connection_client=True)
        return conn.execute_command(*[
            "INTERSECTS",
            PARKING_LOCATIONS,
            "LIMIT",
            10_000,
            "CIRCLE",
            query.latitude,
            query.longitude,
            query.radius,
        ])[1]


class PostGisRetriever:
    engine = create_postgis_engine(pool=False)

    def retrieve(self, query: NearbyQuery):
        query_geom2 = func.ST_Buffer(
            func.ST_GeogFromText(f"Point ( {query.longitude} {query.latitude} )"),
            query.radius,
            srid=4326,
        )

        sql_query = (
            Select(
                ParkingLocationsPostGis.parking_location_id,
                ParkingLocationsPostGis.price,
            )
            .select_from(ParkingLocationsPostGis)
            .where(func.ST_Intersects(query_geom2, ParkingLocationsPostGis.geometry))
        )

        session = sessionmaker(bind=self.engine)()
        results = session.execute(sql_query).all()

        return [
            {
                "parking_location_id": r.parking_location_id,
                "price": r.price,
            }
            for r in results
        ]


@app.get("/nearby-parking-locations")
async def get_nearby(
        latitude: float = Query(ge=-90, le=90, example=48.245),
        longitude: float = Query(ge=-180, le=180, example=11.5729),
        free_only: bool = Query(
            description="If True only return no payment necessary locations",
            default=False,
        ),
        database: Database = Query(Database.TILE38),
        distance_meters: float = Query(
            ge=0.1,
            description="Distance from point to search for parking locations",
            example=150,
        ),
):
    query = NearbyQuery(
        latitude=latitude,
        longitude=longitude,
        free_only=free_only,
        radius=distance_meters,
    )

    if database == "postgis":
        return PostGisRetriever().retrieve(query=query)
    elif database == "tile38":
        return await Tile38Retriever().retrieve(query=query)
    else:
        raise ValueError(f"Unknown database {database}")


@app.on_event("shutdown")
async def shutdown() -> None:
    PostGisRetriever.engine.dispose()

if __name__ == "__main__":
    uvicorn.run("api_v3:app")
