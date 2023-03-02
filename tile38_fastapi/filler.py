"""Script for filling Tile38 with test data

Reads a CSV with 3 columns, parking_location_id (int), geometry (wkt string), price (int)

If the test data is in Munich,
the following command could be run on Tile38 to check if there is data in Munich after running this script

Command key              type latitude   longitude  buffer radius
NEARBY parking-locations POINT 48.0357132 11.5939441 5000

The following command will list how many locations have been added,
"num_objects" refers to the number of parking locations inserted
STATS parking-locations
"""
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import redis
from geoalchemy2.elements import WKTElement
from shapely import wkt
from shapely.geometry import mapping
from sqlalchemy.orm import sessionmaker

from tile38_fastapi import PARKING_LOCATIONS
from tile38_fastapi.db import create_postgis_engine, ParkingLocations


@dataclass
class Row:
    parking_location_id: int
    geometry: str
    price: int

    def to_postgis(self) -> ParkingLocations:
        return ParkingLocations(
            parking_location_id=self.parking_location_id,
            price=self.price,
            geometry=WKTElement(self.geometry),
        )


def timer(name: str):
    def timer_(func: Callable):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            func(*args, **kwargs)
            diff = time.perf_counter() - start
            print(f"Completed writing to {name} in {diff:.1f} seconds")
        return wrapper
    return timer_


@timer(name="tile38")
def write_rows_to_tile38(rows: list[Row]) -> None:
    c = redis.Redis(host="localhost", port=9851, single_connection_client=True)
    for row in rows:
        d = mapping(wkt.loads(row.geometry))
        d["price"] = row.price

        command = [
            "SET",                    # The Tile38 operation to perform
            PARKING_LOCATIONS,        # Tile38 key
            row.parking_location_id,  # Tile38 field
            "OBJECT",                 # The type of data to store (GeoJSON object in this case)
            json.dumps(d),            # Tile38 value
        ]

        c.execute_command(*command)


@timer(name="postgis")
def write_rows_to_postgis(rows: list[Row]) -> None:
    engine = create_postgis_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # it may be faster to use sqlalchemy core here instead of orm
    # as the focus is the performance of data retrieval I'm leaving this as is
    session.add_all([
        row.to_postgis()
        for row in rows
    ])

    session.commit()
    session.close()


def main(input_file: Path) -> None:

    # create postgis table
    ParkingLocations.create_table()

    # load the test data from a file
    with open(input_file, "r") as f:

        # skip the header row of CSV
        next(csv.reader(f))

        # read the rest of the rows into a list of data classes
        rows = [Row(*row) for row in csv.reader(f)]

        write_rows_to_tile38(rows)

        write_rows_to_postgis(rows)


if __name__ == "__main__":
    main(input_file=Path(__file__).parent.parent / "data/test-data.csv")
