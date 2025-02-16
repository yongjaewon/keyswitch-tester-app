from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import enum

Base = declarative_base()

# Define MachineStateEnum
class MachineStateEnum(enum.Enum):
    on = "on"
    off = "off"
    disabled = "disabled"

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True)  # 1-4
    enabled = Column(Boolean, default=False)  # Managed by server, controls servo via Arduino
    current_cycles = Column(Integer, default=0)  # Counted by server
    motor_current = Column(Float, default=0.0)  # From Arduino, in Amps
    switch_current = Column(Float, default=0.0)  # From Arduino, in Amps
    motor_failures = Column(Integer, default=0)  # Calculated by server based on motor_current
    switch_failures = Column(Integer, default=0)  # Calculated by server based on switch_current
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Timestamp of last Arduino reading
    
    history = relationship("SystemHistory", back_populates="station")

class SystemState(Base):
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True)
    supply_voltage = Column(Float, default=13.2)  # From sensor
    timer_end_time = Column(DateTime, nullable=True)  # UTC timestamp when timer will end
    timer_active = Column(Boolean, default=False)  # Managed by server
    machine_state = Column(Enum(MachineStateEnum), default=MachineStateEnum.off, nullable=False)  # New field

class SystemHistory(Base):
    __tablename__ = "system_history"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    cycle_limit = Column(Integer)  # System setting at time of recording
    current_cycles = Column(Integer)  # Station's cycle count
    motor_failures = Column(Integer)  # Station's motor failures
    switch_failures = Column(Integer)  # Station's switch failures
    motor_current = Column(Float)  # Station's motor current from Arduino
    switch_current = Column(Float)  # Station's switch current from Arduino
    cycles_per_minute = Column(Integer)  # System setting at time of recording
    supply_voltage = Column(Float)  # System voltage from Arduino
    machine_state = Column(Enum(MachineStateEnum))  # System state at time of recording
    
    station = relationship("Station", back_populates="history")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    pin_code = Column(String(4), nullable=False)
    cycles_per_minute = Column(Integer, default=6)  # Controls servo timing
    cutoff_voltage = Column(Float, default=11.1)  # Threshold for Arduino voltage
    motor_current_threshold = Column(Float, default=100.0)  # Threshold for failure detection
    switch_current_threshold = Column(Float, default=5.0)   # Threshold for failure detection
    cycle_limit = Column(Integer, default=100000)  # Max cycles before auto-disable
    motor_failure_threshold = Column(Integer, default=10)  # Max failures before auto-disable
    switch_failure_threshold = Column(Integer, default=10)  # Max failures before auto-disable
