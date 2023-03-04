"""This script generates test data that can be inserted into Tile38 and PostGIS by filler.py"""
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import geopy
from geopy.distance import GeodesicDistance
from shapely import LineString
from shapely import wkt
from shapely.geometry import mapping


def generate_random_float_creator(low: float, high: float) -> Callable[[], float]:
    def f():
        v = random.random()
        diff = high - low
        return v * diff + low
    return f


@dataclass
class RandomInputs:
    start: geopy.Point
    bearing: float
    length: float


def main(
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        n_to_generate: int,
        output_csv: Optional[str] = None,
        output_geojson: Optional[str] = None,
) -> None:
    # =========================================
    # Create random lines to represent on-street parking
    random_lat = generate_random_float_creator(min_lat, max_lat)
    random_lng = generate_random_float_creator(min_lng, max_lng)
    random_bearing = generate_random_float_creator(0, 360)
    random_parking_location_length = generate_random_float_creator(5, 250)

    random_inputs = [
        RandomInputs(
            start=geopy.Point(latitude=random_lat(), longitude=random_lng()),
            bearing=random_bearing(),
            length=random_parking_location_length(),
        )
        for _ in range(n_to_generate)
    ]

    end_points = [
        GeodesicDistance(meters=x.length).destination(x.start, x.bearing)
        for x in random_inputs
    ]

    lines = [
        LineString(coordinates=[
            (inputs.start.longitude, inputs.start.latitude),
            (end.longitude, end.latitude),
        ])
        for inputs, end in zip(random_inputs, end_points)
    ]

    # =========================================
    # Create random prices and ids
    prices = [random.randint(0, 10) for _ in range(n_to_generate)]
    ids = range(n_to_generate)

    # =========================================
    # Save output to CSV
    if output_csv is None:
        output_csv = Path(__file__).parent.parent / "data/random-locations.csv"

    wkt_lines = [wkt.dumps(line, rounding_precision=6) for line in lines]

    with open(output_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["parking_location_id", "geometry", "price"])
        writer.writerows(zip(ids, lines, prices))

    # =========================================
    # Save output to GeoJSON
    if output_geojson is None:
        output_geojson = Path(__file__).parent.parent / "data/random-locations.geojson"

    output_d = {
        "type": "FeatureCollection",
        "features": [],
    }
    for id_, line, price in zip(ids, lines, prices):
        d = {
            "geometry": mapping(line),
            "price": price,
            "parking_location_id": id_,
        }
        output_d["features"].append(d)

    with open(output_geojson, "w") as f:
        json.dump(output_d, f)


if __name__ == "__main__":
    main(
        min_lat=48.022,
        max_lat=48.245,
        min_lng=11.35,
        max_lng=11.78,
        n_to_generate=30_000,
    )
