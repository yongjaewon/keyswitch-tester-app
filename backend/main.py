# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
from typing import Dict

from .database import get_db, init_db
from .models import Station, SystemSettings, SystemState, StationStatus
from .uart_service import UARTService
from .websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Keyswitch Tester")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize services
uart = UARTService()
ws_manager = WebSocketManager()

# Authentication middleware
async def verify_pin(pin: str, db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if pin != settings.pin_code:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return True

# Background task for status monitoring
async def monitor_status():
    while True:
        try:
            # Get status from Arduino
            status = await uart.read_status()
            if status:
                # Broadcast to all connected clients
                await ws_manager.broadcast(status)
            await asyncio.sleep(0.5)  # Wait 500ms before next check
        except Exception as e:
            logger.error(f"Error in status monitoring: {e}")
            await asyncio.sleep(1)  # Wait longer on error

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database
    init_db()
    # Connect to Arduino
    if not await uart.connect():
        logger.error("Failed to connect to Arduino!")
    # Start background monitoring
    asyncio.create_task(monitor_status())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await uart.disconnect()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Wait for messages (if needed in future)
            data = await websocket.receive_text()
    except:
        await ws_manager.disconnect(websocket)

# API Routes
@app.post("/auth")
async def authenticate(pin: str, db: Session = Depends(get_db)):
    """Verify PIN code"""
    if await verify_pin(pin, db):
        return {"success": True}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get current system status"""
    system_state = db.query(SystemState).order_by(SystemState.timestamp.desc()).first()
    stations = db.query(Station).all()
    return {
        "system": {
            "battery_voltage": system_state.battery_voltage if system_state else 0.0,
            "master_enable": system_state.master_enable if system_state else False,
            "cycles_per_minute": db.query(SystemSettings).first().cycles_per_minute
        },
        "stations": [
            {
                "number": station.station_number,
                "target_count": station.target_count,
                "current_count": station.current_count,
                "motor_failures": station.motor_failures,
                "switch_failures": station.switch_failures,
                "current_measurement": station.current_measurement,
                "is_enabled": station.is_enabled,
                "status": station.status.value
            }
            for station in stations
        ]
    }

@app.post("/system/start")
async def start_system(pin: str, db: Session = Depends(get_db)):
    """Start the testing system"""
    await verify_pin(pin, db)
    success = await uart.start_test()
    return {"success": success}

@app.post("/system/stop")
async def stop_system(pin: str, db: Session = Depends(get_db)):
    """Stop the testing system"""
    await verify_pin(pin, db)
    success = await uart.stop_test()
    return {"success": success}

@app.post("/system/cycles")
async def set_cycles(cycles: int, pin: str, db: Session = Depends(get_db)):
    """Set cycles per minute"""
    await verify_pin(pin, db)
    if not 1 <= cycles <= 60:
        raise HTTPException(status_code=400, detail="Cycles must be between 1 and 60")
    success = await uart.set_cycles_per_minute(cycles)
    if success:
        settings = db.query(SystemSettings).first()
        settings.cycles_per_minute = cycles
        db.commit()
    return {"success": success}

@app.post("/station/{station_number}/enable")
async def enable_station(
    station_number: int,
    pin: str,
    db: Session = Depends(get_db)
):
    """Enable a specific station"""
    await verify_pin(pin, db)
    if not 1 <= station_number <= 4:
        raise HTTPException(status_code=400, detail="Invalid station number")
    success = await uart.enable_station(station_number)
    if success:
        station = db.query(Station).filter_by(station_number=station_number).first()
        station.is_enabled = True
        db.commit()
    return {"success": success}

@app.post("/station/{station_number}/disable")
async def disable_station(
    station_number: int,
    pin: str,
    db: Session = Depends(get_db)
):
    """Disable a specific station"""
    await verify_pin(pin, db)
    if not 1 <= station_number <= 4:
        raise HTTPException(status_code=400, detail="Invalid station number")
    success = await uart.disable_station(station_number)
    if success:
        station = db.query(Station).filter_by(station_number=station_number).first()
        station.is_enabled = False
        db.commit()
    return {"success": success}

@app.post("/station/{station_number}/target")
async def set_target(
    station_number: int,
    target: int,
    pin: str,
    db: Session = Depends(get_db)
):
    """Set target count for a station"""
    await verify_pin(pin, db)
    if not 1 <= station_number <= 4:
        raise HTTPException(status_code=400, detail="Invalid station number")
    if target <= 0:
        raise HTTPException(status_code=400, detail="Target must be positive")
    station = db.query(Station).filter_by(station_number=station_number).first()
    station.target_count = target
    db.commit()
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 