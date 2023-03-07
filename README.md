# Tile38 and FastAPI Presentation

## Presentation
The presentation slides are in `/this/location/tile38-fastapi/presentation/presentation.pdf`.

## Preparing environment

Set up virtual environment for the APIs and filling the databases.
```bash
mkvirtualenv tile38-fastapi
cd /this/location/tile38-fastapi
pip install -r requirements.txt
```

## Generate sample data
A script is included to generate sample data, which are pretend parking locations in Munich.
They are drawn with the approximate length of parking locations, 
but are randomly placed and don't follow the road network. 

```bash
python ./tile38_fastapi/generate_data.py
```

It will generate two files, by default:
* `./data/random-locations.csv`
* `./data/random-locations.geojson`

## Fill the databases
```bash
# in one terminal, run the following that will launch Tile38 and PostGIS
docker-compose up

# in another run this which will fill the databases with data
python ./tile38_fastapi/filler.py
```

## Run the API

```bash
workon tile38-fastapi
cd /this/location/tile38-fastapi

# Most basic example
python tile38_fastapi/api_v1.py

# Same as above, but adds filtering of free locations and additional validation
python tile38_fastapi/api_v2.py

# A more fully featured version that is used for benchmarking the datasets
python tile38_fastapi/api_v3.py
```

## Inspecting databases directly

### Tile38
The following instructions are for Linux, 
for installation on other platforms see [here](https://github.com/tidwall/tile38/releases/tag/1.30.2)

Download and extract Tile38 service and cli binaries
```bash
curl -L  https://github.com/tidwall/tile38/releases/download/1.30.2/tile38-1.30.2-linux-amd64.tar.gz -o tile38-1.30.2-linux-amd64.tar.gz
tar xzvf tile38-1.30.2-linux-amd64.tar.gz
cd tile38-1.30.2-linux-amd64
```

Launch the Tile38 client with `./tile38-client`. 
As long as you have already started the tile38 server using docker-compose this should connect.

### PostGIS

Install a postgres client. Following is for Ubuntu or derivative.
```bash
sudo apt install postgresql
```

To connect to the database, when prompted the password is "the_password"
```bash
psql parking -U the_user -W -p 5432 -h localhost
```

## Benchmarking
The benchmarking commands use [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html). 
To install on Ubuntu and derivatives:
```bash
sudo apt install apache2-utils
```

Commands to run benchmarks. 
```bash
# Tile38 - 100 serial requests
ab -c 1 -n 100 'http://localhost:8000/nearby-parking-locations?latitude=48.245&longitude=11.5729&distance_meters=250&free_only=false&database=tile38'

# PostGIS - 100 serial requests
ab -c 1 -n 100 'http://localhost:8000/nearby-parking-locations?latitude=48.245&longitude=11.5729&distance_meters=250&free_only=false&database=postgis'

# Tile38 - 100 concurrent requests
ab -c 100 -n 100 'http://localhost:8000/nearby-parking-locations?latitude=48.245&longitude=11.5729&distance_meters=250&free_only=false&database=tile38'

# PostGIS - 100 concurrent requests
ab -c 100 -n 100 'http://localhost:8000/nearby-parking-locations?latitude=48.245&longitude=11.5729&distance_meters=250&free_only=false&database=postgis'
```

Make sure you have started the databases and run the filler script beforehand run the filler script beforehand. 
To check the query, try replacing `ab -c X -n 100`  with  `curl` and make sure locations are being found.
