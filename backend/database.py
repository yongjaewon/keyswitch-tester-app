# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import os

from .models import Base, Station, SystemSettings, StationStatus

# Create database URL
DATABASE_URL = "sqlite:///./keyswitch_tester.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database with tables and default data"""
    Base.metadata.create_all(bind=engine)
    
    # Create initial data
    db = SessionLocal()
    try:
        # Check if we need to initialize data
        if db.query(Station).count() == 0:
            # Create the 4 stations
            for station_num in range(1, 5):
                station = Station(
                    station_number=station_num,
                    status=StationStatus.STOPPED
                )
                db.add(station)
        
        # Create default system settings if they don't exist
        if db.query(SystemSettings).count() == 0:
            settings = SystemSettings(
                pin_code="1234",  # Default PIN
                cycles_per_minute=6
            )
            db.add(settings)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 