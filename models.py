''' database models (SQLAlchemy)'''

from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(String)
    station_id = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    aod = Column(Float)
    hotspots = Column(Integer)
    traffic_index = Column(Float)
    industry_index = Column(Float)
    temp_c = Column(Float)
    rh = Column(Float)
    wind_speed = Column(Float)
    pm25 = Column(Float)
    stubble_frac = Column(Float)
    traffic_frac = Column(Float)
    industry_frac = Column(Float)
