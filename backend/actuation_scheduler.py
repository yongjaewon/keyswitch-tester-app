#!/usr/bin/env python3
"""Background task to schedule servo actuation cycles based on database settings and hardware configuration."""

import asyncio
import logging
from contextlib import asynccontextmanager

from database import get_db
from models import Station, SystemSettings, SystemState, MachineStateEnum

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set base level to WARNING

@asynccontextmanager
async def get_db_context():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

async def actuation_scheduler(app):
    """Continuously check system settings and execute servo actuation cycles in a non-blocking way."""
    while True:
        async with get_db_context() as db:
            try:
                settings = db.query(SystemSettings).first()
                if not settings:
                    logger.error("SystemSettings not found in database.")
                    await asyncio.sleep(1)
                    continue

                # Check machine state
                system_state = db.query(SystemState).first()
                if not system_state or system_state.machine_state != MachineStateEnum.on:
                    if not app.state.hal.actuator_module.safe_state_reached:
                        logger.warning(f"Machine state is {system_state.machine_state if system_state else 'unknown'}. Setting safe state.")
                        await app.state.hal.set_safe_state()
                    await asyncio.sleep(1)
                    continue

                # Check enabled stations
                stations = db.query(Station).all()
                enabled_stations = [s for s in stations if s.enabled]
                if len(enabled_stations) == 0:
                    if not app.state.hal.actuator_module.safe_state_reached:
                        logger.warning("No stations enabled. Setting safe state.")
                        await app.state.hal.set_safe_state()
                    await asyncio.sleep(1)
                    continue

                # Calculate actuation interval
                actuation_interval = 60.0 / settings.cycles_per_minute / len(enabled_stations)
                logger.warning(f"Starting actuation cycle. Interval: {actuation_interval:.2f} seconds")

                # Reset safe state if needed
                if app.state.hal.actuator_module.safe_state_reached:
                    logger.warning("Resetting safe state to enable servo movement.")
                    await app.state.hal.reset_safe_state()

                # Use the sensor polling interval from hardware configuration
                sensor_poll_interval = app.state.hal.config.get("phidgets", {}).get("data_interval", 10) / 1000.0

                # Cycle through enabled stations
                for station in enabled_stations:
                    # Check machine state before starting each station
                    system_state = db.query(SystemState).first()
                    if not system_state or system_state.machine_state != MachineStateEnum.on:
                        logger.warning("Machine state changed during cycle. Going to safe state.")
                        await app.state.hal.set_safe_state()
                        break

                    cycle_start = asyncio.get_event_loop().time()
                    logger.warning(f"Starting cycle for station {station.id}")

                    # Start current measurement
                    peak_current = 0.0
                    cycle_duration = app.state.hal.config["servo"]["cycle_duration"]
                    press_duration = app.state.hal.config["servo"]["press_duration"]
                    return_duration = app.state.hal.config["servo"]["return_duration"]

                    async def measure_current():
                        nonlocal peak_current
                        end_time = asyncio.get_event_loop().time() + cycle_duration
                        while asyncio.get_event_loop().time() < end_time:
                            # Check machine state during measurement
                            system_state = db.query(SystemState).first()
                            if not system_state or system_state.machine_state != MachineStateEnum.on:
                                return False

                            sensor_data = app.state.hal.get_sensor_data()
                            if sensor_data and 'switch_current' in sensor_data:
                                current_val = sensor_data['switch_current']
                                if current_val > peak_current:
                                    peak_current = current_val
                            await asyncio.sleep(sensor_poll_interval)
                        return True

                    measurement_task = asyncio.create_task(measure_current())

                    # Execute actuation cycle
                    logger.warning(f"Moving station {station.id} to 100 degrees")
                    await app.state.hal.command_servo(station.id, target_angle=100)
                    await asyncio.sleep(press_duration)
                    
                    # Check machine state after first movement
                    system_state = db.query(SystemState).first()
                    if not system_state or system_state.machine_state != MachineStateEnum.on:
                        logger.warning("Machine state changed during cycle. Going to safe state.")
                        await app.state.hal.set_safe_state()
                        break
                    
                    logger.warning(f"Moving station {station.id} back to 0 degrees")
                    await app.state.hal.command_servo(station.id, target_angle=0)
                    await asyncio.sleep(return_duration)

                    measurement_complete = await measurement_task
                    if not measurement_complete:
                        logger.warning("Machine state changed during measurement. Going to safe state.")
                        await app.state.hal.set_safe_state()
                        break

                    # Update station data
                    station.switch_current = peak_current
                    if peak_current < settings.switch_current_threshold:
                        station.switch_failures += 1
                        logger.warning(f"Station {station.id}: Peak current {peak_current:.2f} below threshold {settings.switch_current_threshold}. Failures: {station.switch_failures}")

                    # Increment cycle count regardless of success/failure
                    station.current_cycles += 1
                    logger.warning(f"Station {station.id}: Completed cycle {station.current_cycles}")

                    if station.switch_failures >= settings.switch_failure_threshold:
                        station.enabled = False
                        logger.warning(f"Station {station.id} disabled due to excessive failures.")

                    db.commit()

                    # Wait for next cycle
                    elapsed = asyncio.get_event_loop().time() - cycle_start
                    remaining = actuation_interval - elapsed
                    if remaining > 0:
                        # Check machine state during the wait period
                        for _ in range(int(remaining / 0.1)):  # Check every 100ms
                            system_state = db.query(SystemState).first()
                            if not system_state or system_state.machine_state != MachineStateEnum.on:
                                logger.warning("Machine state changed during cycle wait. Going to safe state.")
                                await app.state.hal.set_safe_state()
                                break
                            await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in actuation scheduler: {str(e)}")
                await asyncio.sleep(1)

        await asyncio.sleep(0) 