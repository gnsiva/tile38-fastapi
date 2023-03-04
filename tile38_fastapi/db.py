"""File containing additional code for working with MySQL and PostGIS"""
from geoalchemy2 import Geography as GeoalchemyGeography
from psycopg2.errors import DuplicateTable
from sqlalchemy import Engine, create_engine, Column, Integer, NullPool
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base


def create_postgis_engine(pool: bool) -> Engine:
    if pool:
        pool_kwargs = {
            "pool_size": 25,
            "max_overflow": 100,
        }
    else:
        pool_kwargs = {
            "poolclass": NullPool
        }

    return create_engine(
        "postgresql+psycopg2://the_user:the_password@localhost:5432/parking",
        **pool_kwargs,
    )


Base = declarative_base()


class ParkingLocationsPostGis(Base):
    __tablename__ = "parking_locations"

    parking_location_id = Column(Integer, primary_key=True, nullable=False)
    price = Column(Integer, nullable=False)
    geometry = Column(GeoalchemyGeography("LineString", srid=4326), nullable=False)

    @classmethod
    def create_table(cls) -> None:
        """Create table if exists"""
        engine = create_postgis_engine()
        try:
            cls.__table__.create(bind=engine)
        except (DuplicateTable, ProgrammingError):
            pass
        engine.dispose()
