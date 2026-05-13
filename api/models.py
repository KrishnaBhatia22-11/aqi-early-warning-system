from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float,
    Index, Integer, String, UniqueConstraint, func,
)
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


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    email      = Column(String(256), nullable=False)
    city       = Column(String(64), nullable=False)
    threshold  = Column(Integer, nullable=False, default=150)
    active     = Column(Boolean, default=True)
    token      = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_fired = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("email", "city", name="uq_alert_email_city"),
    )
