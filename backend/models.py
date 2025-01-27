from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class StationStatus(enum.Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class Station(Base):
    __tablename__ = "stations"
    
    station_number = Column(Integer, primary_key=True)  # 1-4
    target_count = Column(Integer, default=1000000)
    current_count = Column(Integer, default=0)
    motor_failures = Column(Integer, default=0)
    switch_failures = Column(Integer, default=0)
    current_measurement = Column(Float, default=0.0)  # in Amps
    is_enabled = Column(Boolean, default=True)
    status = Column(Enum(StationStatus), default=StationStatus.STOPPED)
    
    history = relationship("SystemHistory", back_populates="station")

class SystemState(Base):
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    battery_voltage = Column(Float, default=0.0)
    master_enable = Column(Boolean, default=False)

class SystemHistory(Base):
    __tablename__ = "system_history"
    
    id = Column(Integer, primary_key=True)
    station_number = Column(Integer, ForeignKey("stations.station_number"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    target_count = Column(Integer)
    count = Column(Integer)
    motor_failures = Column(Integer)
    switch_failures = Column(Integer)
    current_measurement = Column(Float)
    status = Column(Enum(StationStatus))
    cycles_per_minute = Column(Integer)
    battery_voltage = Column(Float)
    master_enable = Column(Boolean)
    
    station = relationship("Station", back_populates="history")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    pin_code = Column(String(4), nullable=False)
    cycles_per_minute = Column(Integer, default=6)
