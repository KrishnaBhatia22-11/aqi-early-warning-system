from sqlalchemy import BigInteger, Column, DateTime, Float, Index, Integer, String, func
from api.database import Base


class AQIReading(Base):
    __tablename__ = "aqi_readings"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    city          = Column(String(64), nullable=False)
    aqi           = Column(Float, nullable=False)
    pm25          = Column(Float, nullable=True)
    pm10          = Column(Float, nullable=True)
    no2           = Column(Float, nullable=True)
    co            = Column(Float, nullable=True)
    so2           = Column(Float, nullable=True)
    o3            = Column(Float, nullable=True)
    station_count = Column(Integer, nullable=True)
    source        = Column(String(32), default="WAQI")
    timestamp     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_aqi_readings_city_timestamp", "city", "timestamp"),
    )
