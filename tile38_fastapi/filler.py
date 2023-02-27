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
from pathlib import Path

import redis
from shapely import wkt
from shapely.geometry import mapping

from tile38_fastapi import PARKING_LOCATIONS


def main(input_file: Path) -> None:

    c = redis.Redis(host="localhost", port=9851)

    with open(input_file, "r") as f:

        # skip the header row of CSV
        next(csv.reader(f))

        for row in csv.reader(f):

            # unpack data and create geojson object to insert into Tile38
            parking_location_id, geometry, price = row
            d = mapping(wkt.loads(geometry))
            d["price"] = price
            geojson_object = json.dumps(d)

            command = [
                "SET",
                PARKING_LOCATIONS,    # Tile38 key
                parking_location_id,  # Tile38 field
                "OBJECT",
                geojson_object,       # Tile38 value
            ]

            c.execute_command(*command)


if __name__ == "__main__":
    main(input_file=Path(__file__).parent.parent / "data/test-data.csv")
