# backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException, Depends, APIRouter, Path, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from camera import CameraManager
from actuation_scheduler import actuation_scheduler

from database import get_db, init_db
from models import Station, SystemSettings, SystemState, SystemHistory, MachineStateEnum
from hal import HardwareAbstractionLayer
from websocket_manager import WebSocketManager
from schemas import (
    StationStateUpdate,
    TimerSettings,
    SystemSettingsUpdate,
    StationResponse,
    SystemStatusResponse,
    SystemSettingsResponse,
    SuccessResponse,
    StationSettingsUpdate
)

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
UPDATE_FREQUENCY = float(os.getenv("UPDATE_FREQUENCY", "0.5"))
MAX_TIMER_HOURS = int(os.getenv("MAX_TIMER_HOURS", "24"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("BAUD_RATE", "115200"))

# Initialize FastAPI app
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    init_db()
    
    # Initialize HAL
    hal = HardwareAbstractionLayer()
    await hal.connect()
    app.state.hal = hal
    
    # Initialize WebSocket manager
    websocket_manager = WebSocketManager()
    app.state.websocket_manager = websocket_manager

    # Ensure database has required records
    async with get_db_context() as db:
        # Ensure system state exists
        system_state = db.query(SystemState).first()
        if not system_state:
            logger.info("Initializing system state")
            system_state = SystemState(
                supply_voltage=13.2,
                timer_active=False,
                timer_end_time=None,
                machine_state=MachineStateEnum.off
            )
            db.add(system_state)
            db.commit()

        # Ensure system settings exist
        settings = db.query(SystemSettings).first()
        if not settings:
            logger.info("Initializing system settings")
            settings = SystemSettings(
                cutoff_voltage=11.1,
                motor_current_threshold=100.0,
                switch_current_threshold=5.0,
                cycle_limit=100000,
                motor_failure_threshold=10,
                switch_failure_threshold=10,
                cycles_per_minute=6,
                pin_code="1234"
            )
            db.add(settings)
            db.commit()

        # Ensure stations exist
        stations = db.query(Station).all()
        if not stations:
            logger.info("Initializing stations")
            for station_id in range(1, 5):
                station = Station(
                    id=station_id,
                    enabled=False,
                    motor_failures=0,
                    switch_failures=0,
                    current_cycles=0,
                    motor_current=0.0,
                    switch_current=0.0
                )
                db.add(station)
            db.commit()

    # Start background tasks
    background_tasks.append(asyncio.create_task(monitor_status(app)))
    background_tasks.append(asyncio.create_task(send_hal_state()))
    background_tasks.append(asyncio.create_task(actuation_scheduler(app)))

    try:
        yield
    finally:
        # Cleanup
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        await hal.disconnect()

app = FastAPI(
    title="Keyswitch Tester API",
    version="1.0.0",
    description="API for controlling and monitoring the keyswitch tester system",
    lifespan=lifespan
)

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize services
ws_manager = WebSocketManager()

# Track low voltage state
voltage_monitor = {
    'low_voltage_start': None  # Timestamp when voltage first dropped below cutoff
}

@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

async def broadcast_status_update(db: Session):
    """Helper function to broadcast current system status to all clients"""
    try:
        system_state = db.query(SystemState).first()
        if not system_state:
            logger.error("System state not found when trying to broadcast status")
            system_state = SystemState(supply_voltage=13.2, timer_active=False, timer_end_time=None, machine_state=MachineStateEnum.off)
            db.add(system_state)
            db.commit()
        
        stations = db.query(Station).all()
        if not stations:
            logger.warning("No stations found when trying to broadcast status")
            # Initialize default stations if none exist
            stations = []
            for station_id in range(1, 5):
                station = Station(
                    id=station_id,
                    enabled=False,
                    motor_failures=0,
                    switch_failures=0,
                    current_cycles=0,
                    motor_current=0.0,
                    switch_current=0.0
                )
                db.add(station)
                stations.append(station)
            db.commit()
        
        # Format the timer end time in UTC without microseconds
        timer_end_time = None
        if system_state.timer_end_time:
            timer_end_time = system_state.timer_end_time.replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get and broadcast history
        history = db.query(SystemHistory).order_by(SystemHistory.id.desc()).all()
        history_update = {
            'type': 'history_update',
            'data': [
                {
                    "timestamp": entry.id,  # Using ID as timestamp for now
                    "station_id": entry.station_id,
                    "event": f"{'System' if not entry.station_id else f'Station {entry.station_id}'} update",
                    "details": (
                        f"Cycles: {entry.current_cycles}, "
                        f"Motor failures: {entry.motor_failures}, "
                        f"Switch failures: {entry.switch_failures}, "
                        f"Motor current: {entry.motor_current:.1f}A, "
                        f"Switch current: {entry.switch_current:.1f}A"
                    )
                }
                for entry in history
            ]
        }
        await ws_manager.broadcast(history_update)
        
        # Continue with existing status update broadcast
        status_update = {
            'type': 'status_update',
            'data': {
                'supply_voltage': system_state.supply_voltage,
                'machine_state': system_state.machine_state.value,
                'timer_active': system_state.timer_active,
                'timer_end_time': timer_end_time,
                'stations': [
                    {
                        'id': s.id,
                        'enabled': s.enabled,
                        'motor_failures': s.motor_failures,
                        'switch_failures': s.switch_failures,
                        'current_cycles': s.current_cycles,
                        'motor_current': s.motor_current,
                        'switch_current': s.switch_current
                    }
                    for s in stations
                ]
            }
        }
        
        logger.debug(f"Broadcasting status update: {status_update}")
        await ws_manager.broadcast(status_update)
    except Exception as e:
        logger.error(f"Error in broadcast_status_update: {str(e)}")
        # Don't raise the exception, as this is a background task

def calculate_end_time(hours: int, minutes: int) -> Optional[datetime]:
    """
    Calculate the UTC end time for a timer
    
    Args:
        hours: Number of hours for timer (0-MAX_TIMER_HOURS)
        minutes: Number of minutes for timer (0-59)
        
    Returns:
        datetime: UTC end time, or None if timer is being cleared
        
    Raises:
        ValueError: If hours or minutes are invalid
    """
    if hours < 0 or hours >= MAX_TIMER_HOURS:
        raise ValueError(f"Hours must be between 0 and {MAX_TIMER_HOURS}")
    if minutes < 0 or minutes >= 60:
        raise ValueError("Minutes must be between 0 and 59")
        
    if hours == 0 and minutes == 0:
        return None
        
    # Use UTC time for all calculations
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now + timedelta(hours=hours, minutes=minutes)

async def ensure_system_state(db: Session) -> SystemState:
    """
    Ensure system state exists in database
    
    Args:
        db: Database session
        
    Returns:
        SystemState: Current system state
        
    Raises:
        HTTPException: If system state cannot be created
    """
    try:
        system_state = db.query(SystemState).first()
        if not system_state:
            system_state = SystemState()
            db.add(system_state)
            db.commit()
        return system_state
    except Exception as e:
        logger.error(f"Error ensuring system state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to ensure system state")

# Authentication middleware
async def verify_pin(pin: str, db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if pin != settings.pin_code:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return True

# Background task for status monitoring
async def monitor_status(app: FastAPI):
    """Background task for monitoring system status"""
    try:
        while True:
            try:
                # Get latest reading from HAL (if connected)
                try:
                    sensor_data = app.state.hal.get_sensor_data()
                except Exception as e:
                    logger.debug(f"Could not get sensor data (development mode?): {e}")
                    sensor_data = {}
                
                async with get_db_context() as db:
                    system_state = await ensure_system_state(db)
                    settings = db.query(SystemSettings).first()
                    if not settings:
                        logger.error("System settings not found")
                        continue
                    
                    # Check if timer has expired
                    if system_state.timer_active and system_state.timer_end_time:
                        current_time = datetime.now(timezone.utc).replace(microsecond=0)
                        timer_end_time = system_state.timer_end_time.replace(tzinfo=timezone.utc)
                        logger.debug(f"Checking timer expiration - Current time: {current_time.isoformat()}, End time: {timer_end_time.isoformat()}")
                        if current_time >= timer_end_time:
                            logger.info("Timer expired, stopping system")
                            system_state.machine_state = MachineStateEnum.off
                            system_state.timer_active = False
                            system_state.timer_end_time = None
                            db.commit()
                            
                            try:
                                # Send stop command to HAL if connected
                                await app.state.hal.set_safe_state()
                            except Exception as e:
                                logger.debug(f"Could not set safe state (development mode?): {e}")
                            
                            # Broadcast the updated state
                            await broadcast_status_update(db)
                            continue
                        else:
                            logger.debug(f"Timer not expired yet. Time remaining: {(timer_end_time - current_time).total_seconds()} seconds")

                    # Process HAL data if available
                    if 'supply_voltage' in sensor_data:
                        system_state.supply_voltage = sensor_data['supply_voltage']
                        
                        # Check voltage against cutoff
                        if system_state.machine_state == "on" and system_state.supply_voltage < settings.cutoff_voltage:
                            current_time = datetime.now(timezone.utc)
                            
                            # If this is the first time voltage dropped below cutoff
                            if voltage_monitor['low_voltage_start'] is None:
                                voltage_monitor['low_voltage_start'] = current_time
                                logger.warning(f"Supply voltage dropped below cutoff: {system_state.supply_voltage}V < {settings.cutoff_voltage}V")
                            
                            # If voltage has been below cutoff for more than 5 seconds
                            elif (current_time - voltage_monitor['low_voltage_start']).total_seconds() >= 5:
                                logger.error(f"Supply voltage below cutoff for >5 seconds, stopping system")
                                system_state.machine_state = "off"
                                voltage_monitor['low_voltage_start'] = None  # Reset the timer
                                
                                # Send stop command to HAL if connected
                                await app.state.hal.set_safe_state()
                        else:
                            # Reset the low voltage timer if voltage is above cutoff
                            if voltage_monitor['low_voltage_start'] is not None:
                                logger.info(f"Supply voltage restored: {system_state.supply_voltage}V")
                                voltage_monitor['low_voltage_start'] = None
                            
                            db.commit()
                        
                        # Handle station current readings
                        if all(k in sensor_data for k in ['station_id', 'motor_current', 'switch_current']):
                            station = db.query(Station).filter_by(id=sensor_data['station_id']).first()
                            if station:
                                settings = db.query(SystemSettings).first()
                                if not settings:
                                    logger.error("System settings not found")
                                    continue
                                
                                # Update current readings
                                station.motor_current = sensor_data['motor_current']
                                station.switch_current = sensor_data['switch_current']
                                station.last_updated = datetime.now(timezone.utc)
                                station.current_cycles += 1
                                
                                # Check for failures
                                if station.motor_current > settings.motor_current_threshold:
                                    station.motor_failures += 1
                                    logger.warning(f"Station {station.id} motor failure detected")
                                if station.switch_current > settings.switch_current_threshold:
                                    station.switch_failures += 1
                                    logger.warning(f"Station {station.id} switch failure detected")
                                
                                # Auto-disable if limits reached
                                if (station.current_cycles >= settings.cycle_limit or
                                    station.motor_failures >= settings.motor_failure_threshold or
                                    station.switch_failures >= settings.switch_failure_threshold):
                                    station.enabled = False
                                    logger.info(f"Station {station.id} auto-disabled due to limits reached")
                                
                                db.commit()
                                
                                # Record history
                                history = SystemHistory(
                                    station_id=station.id,
                                    current_cycles=station.current_cycles,
                                    motor_failures=station.motor_failures,
                                    switch_failures=station.switch_failures,
                                    motor_current=station.motor_current,
                                    switch_current=station.switch_current,
                                    supply_voltage=system_state.supply_voltage,
                                    machine_state=system_state.machine_state,
                                    cycle_limit=settings.cycle_limit,
                                    cycles_per_minute=settings.cycles_per_minute
                                )
                                db.add(history)
                                db.commit()
                    
                    # Broadcast updates to all connected clients
                    await broadcast_status_update(db)
                    
            except asyncio.CancelledError:
                logger.info("Monitor status task cancelled")
                return  # Exit cleanly on cancellation
            except Exception as e:
                logger.error(f"Error in status monitoring: {str(e)}")
                await asyncio.sleep(1)  # Wait longer on error
            
            await asyncio.sleep(UPDATE_FREQUENCY)
    except asyncio.CancelledError:
        logger.info("Monitor status task cancelled")
        return  # Exit cleanly on cancellation

# Background task for sending state to HAL
async def send_hal_state():
    """Background task for sending system state to HAL"""
    try:
        while True:
            try:
                # Skip if HAL is not connected
                if not app.state.hal.connected:
                    await asyncio.sleep(UPDATE_FREQUENCY)
                    continue
                    
                async with get_db_context() as db:
                    system_state = db.query(SystemState).first()
                    settings = db.query(SystemSettings).first()
                    
                    if not all([system_state, settings]):
                        logger.error("Missing system state or settings")
                        await asyncio.sleep(1)
                        continue
                    
                    # Get list of enabled station IDs
                    enabled_stations = [
                        station.id 
                        for station in db.query(Station).filter_by(enabled=True).all()
                    ]
                    
                    # Send current state to HAL
                    await app.state.hal.send_state(
                        enabled_stations=enabled_stations,
                        speed=settings.cycles_per_minute,
                        machine_state=system_state.machine_state
                    )
                    
            except asyncio.CancelledError:
                logger.info("Send HAL state task cancelled")
                return  # Exit cleanly on cancellation
            except Exception as e:
                logger.error(f"Error sending state to HAL: {str(e)}")
                await asyncio.sleep(1)
            
            await asyncio.sleep(UPDATE_FREQUENCY)
    except asyncio.CancelledError:
        logger.info("Send HAL state task cancelled")
        return  # Exit cleanly on cancellation

# WebSocket endpoint - keep this at root level
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                logger.info("Client disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                break
    finally:
        await ws_manager.disconnect(websocket)

# API Routes
@api_router.post("/auth")
async def authenticate(pin: str, db: Session = Depends(get_db)):
    """Verify PIN code"""
    if await verify_pin(pin, db):
        return {"success": True}

@api_router.get("/settings", response_model=SystemSettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get current system settings"""
    settings = db.query(SystemSettings).first()
    if not settings:
        raise HTTPException(status_code=500, detail="System settings not found")
    return SystemSettingsResponse(
        cutoff_voltage=settings.cutoff_voltage,
        motor_current_threshold=settings.motor_current_threshold,
        switch_current_threshold=settings.switch_current_threshold,
        cycle_limit=settings.cycle_limit,
        motor_failure_threshold=settings.motor_failure_threshold,
        switch_failure_threshold=settings.switch_failure_threshold,
        cycles_per_minute=settings.cycles_per_minute
    )

@api_router.post("/settings", response_model=SuccessResponse)
async def update_settings(settings: SystemSettingsUpdate, db: Session = Depends(get_db)):
    """Update system settings"""
    current_settings = db.query(SystemSettings).first()
    for key, value in settings.dict().items():
        setattr(current_settings, key, value)
    db.commit()
    
    logger.info("System settings updated in database: %s", settings.dict())
    # Update HAL settings
    hal_result = await app.state.hal.update_settings(settings.dict())
    logger.info("HAL settings update result: %s", hal_result)
    return SuccessResponse(success=True)

@api_router.get("/status", response_model=SystemStatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """Get current system status"""
    system_state = db.query(SystemState).first()
    stations = db.query(Station).all()
    
    return SystemStatusResponse(
        machine_state=system_state.machine_state.value if system_state else "off",
        supply_voltage=system_state.supply_voltage if system_state else 13.2,
        timer_active=system_state.timer_active if system_state else False,
        timer_end_time=system_state.timer_end_time if system_state else None,
        stations=[
            StationResponse(
                id=station.id,
                enabled=station.enabled,
                motor_failures=station.motor_failures,
                switch_failures=station.switch_failures,
                current_cycles=station.current_cycles,
                motor_current=station.motor_current,
                switch_current=station.switch_current
            )
            for station in stations
        ]
    )

@api_router.post("/test/start", response_model=SuccessResponse)
async def start_test(db: Session = Depends(get_db)):
    """Start the testing system"""
    from models import MachineStateEnum
    system_state = db.query(SystemState).first()
    if system_state.machine_state.value == "disabled":
        raise HTTPException(status_code=400, detail="Machine is disabled due to low voltage.")
    await app.state.hal.reset_safe_state()
    system_state.machine_state = MachineStateEnum.on
    db.commit()

    await broadcast_status_update(db)
    return SuccessResponse(success=True)

@api_router.post("/test/stop", response_model=SuccessResponse)
async def stop_test(db: Session = Depends(get_db)):
    """Stop the testing system"""
    try:
        from models import MachineStateEnum
        system_state = db.query(SystemState).first()
        if not system_state:
            raise HTTPException(status_code=500, detail="System state not found")

        system_state.machine_state = MachineStateEnum.off
        # Clear timer if running
        if system_state.timer_active:
            system_state.timer_active = False
            system_state.timer_end_time = None

        db.commit()

        await app.state.hal.set_safe_state()
        await broadcast_status_update(db)
        return SuccessResponse(success=True)
    except Exception as e:
        logger.error(f"Error stopping test: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop test")

@api_router.post("/station/{station_id}/state", response_model=SuccessResponse)
async def set_station_state(
    station_id: int = Path(..., ge=1, le=4, description="Station ID (1-4)"),
    state: StationStateUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Set station enabled/disabled state"""
    station = db.query(Station).filter_by(id=station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
    
    system_state = db.query(SystemState).first()
    if not system_state:
        raise HTTPException(status_code=500, detail="System state not found")
    
    try:
        station.enabled = state.enabled
        db.commit()

        # Broadcast the updated state
        await broadcast_status_update(db)
        return SuccessResponse(success=True)
    except Exception as e:
        logger.error(f"Error updating station {station_id} state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update station state")

@api_router.post("/station/{station_id}/settings", response_model=SuccessResponse)
async def update_station_settings(
    station_id: int = Path(..., ge=1, le=4, description="Station ID (1-4)"),
    settings: StationSettingsUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Update station settings (cycles and failures)"""
    try:
        logger.info(f"Updating station {station_id} settings: {settings}")
        
        # Get station
        station = db.query(Station).filter_by(id=station_id).first()
        if not station:
            logger.error(f"Station {station_id} not found")
            raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
        
        # Get system settings
        system_settings = db.query(SystemSettings).first()
        if not system_settings:
            logger.error("System settings not found")
            raise HTTPException(status_code=500, detail="System settings not found")
        
        # Get system state
        system_state = db.query(SystemState).first()
        if not system_state:
            logger.error("System state not found")
            raise HTTPException(status_code=500, detail="System state not found")
        
        try:
            # Update station values
            station.current_cycles = settings.current_cycles
            station.motor_failures = settings.motor_failures
            station.switch_failures = settings.switch_failures
            
            # If any threshold is exceeded, disable the station
            if (station.motor_failures >= system_settings.motor_failure_threshold or
                station.switch_failures >= system_settings.switch_failure_threshold or
                station.current_cycles >= system_settings.cycle_limit):
                logger.info(f"Disabling station {station_id} due to exceeded thresholds")
                station.enabled = False
            
            db.commit()
            logger.info(f"Successfully updated station {station_id} values")

            try:
                # Record history
                history = SystemHistory(
                    station_id=station.id,
                    current_cycles=station.current_cycles,
                    motor_failures=station.motor_failures,
                    switch_failures=station.switch_failures,
                    motor_current=station.motor_current,
                    switch_current=station.switch_current,
                    supply_voltage=system_state.supply_voltage,
                    machine_state=system_state.machine_state,
                    cycle_limit=system_settings.cycle_limit,
                    cycles_per_minute=system_settings.cycles_per_minute
                )
                db.add(history)
                db.commit()
                logger.info(f"Successfully recorded history for station {station_id}")
            except Exception as history_error:
                logger.error(f"Error recording history: {str(history_error)}")
                # Don't raise here, as the main update was successful

            # Broadcast the updated state
            try:
                await broadcast_status_update(db)
                logger.info(f"Successfully broadcasted status update for station {station_id}")
            except Exception as broadcast_error:
                logger.error(f"Error broadcasting status: {str(broadcast_error)}")
                # Don't raise here, as the main update was successful

            return SuccessResponse(success=True)
            
        except Exception as update_error:
            logger.error(f"Error updating station values: {str(update_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update station values: {str(update_error)}")
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error updating station {station_id} settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@api_router.post("/timer", response_model=SuccessResponse)
async def set_timer(timer: TimerSettings, db: Session = Depends(get_db)):
    """Set system timer with hours and minutes. Setting both to 0 clears the timer."""
    system_state = db.query(SystemState).first()
    if not system_state:
        system_state = SystemState()
    await app.state.hal.reset_safe_state()
    
    # Calculate end time
    timer_end_time = calculate_end_time(timer.hours, timer.minutes)
    
    # If clearing timer (setting to 0), just clear timer state without affecting machine_state
    if timer_end_time is None:
        system_state.timer_end_time = None
        system_state.timer_active = False
    else:
        # Setting a new timer
        system_state.timer_end_time = timer_end_time
        system_state.timer_active = True
        # If setting a non-zero timer, ensure system is started
        if system_state.machine_state != "on":
            system_state.machine_state = "on"
            await app.state.hal.reset_safe_state()
    
    db.commit()

    # Broadcast the updated state
    await broadcast_status_update(db)
    
    return SuccessResponse(success=True)

@app.post("/api/webrtc/offer")
async def handle_offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"]["sdp"], type=params["sdp"]["type"])
    
    pc = RTCPeerConnection()
    camera_manager = CameraManager.get_instance()
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            await pc.close()
            camera_manager.stop_camera()
    
    # Add camera track
    pc.addTrack(camera_manager.get_track())
    
    # Set the remote description
    await pc.setRemoteDescription(offer)
    
    # Create and set local description
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {"sdp": pc.localDescription.dict()}

@api_router.get("/history", response_model=List[dict])
async def get_history(db: Session = Depends(get_db)):
    """Get system history"""
    history = db.query(SystemHistory).order_by(SystemHistory.id.desc()).all()
    return [
        {
            "timestamp": entry.id,  # Using ID as timestamp for now
            "station_id": entry.station_id,
            "event": f"{'System' if not entry.station_id else f'Station {entry.station_id}'} update",
            "details": (
                f"Cycles: {entry.current_cycles}, "
                f"Motor failures: {entry.motor_failures}, "
                f"Switch failures: {entry.switch_failures}, "
                f"Motor current: {entry.motor_current:.1f}A, "
                f"Switch current: {entry.switch_current:.1f}A"
            )
        }
        for entry in history
    ]

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    import signal
    
    # Configure uvicorn to handle signals properly
    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        log_level="debug",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.run() 