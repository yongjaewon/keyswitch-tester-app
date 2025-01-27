# backend/uart_service.py

import serial
import json
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass

@dataclass
class ArduinoCommand:
    START_TEST = b'START\n'
    STOP_TEST = b'STOP\n'
    GET_STATUS = b'STATUS\n'
    SET_CYCLES = b'CYCLES:'  # Will append number and newline
    ENABLE_STATION = b'ENABLE:'  # Will append station number and newline
    DISABLE_STATION = b'DISABLE:'  # Will append station number and newline

class UARTService:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        """Establish connection with Arduino"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            return True
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            return False

    async def disconnect(self):
        """Close the serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()

    async def send_command(self, command: bytes) -> bool:
        """Send a command to Arduino"""
        if not self.serial or not self.serial.is_open:
            self.logger.error("Serial connection not established")
            return False
        
        try:
            self.serial.write(command)
            return True
        except serial.SerialException as e:
            self.logger.error(f"Failed to send command: {e}")
            return False

    async def read_status(self) -> Optional[Dict[str, Any]]:
        """Read and parse status response from Arduino"""
        if not self.serial or not self.serial.is_open:
            return None

        try:
            self.serial.write(ArduinoCommand.GET_STATUS)
            response = self.serial.readline().decode('utf-8').strip()
            return json.loads(response)
        except (serial.SerialException, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to read status: {e}")
            return None

    # High-level control methods
    async def start_test(self) -> bool:
        """Start the test on all enabled stations"""
        return await self.send_command(ArduinoCommand.START_TEST)

    async def stop_test(self) -> bool:
        """Stop the test on all stations"""
        return await self.send_command(ArduinoCommand.STOP_TEST)

    async def set_cycles_per_minute(self, cycles: int) -> bool:
        """Set the cycles per minute"""
        command = ArduinoCommand.SET_CYCLES + str(cycles).encode() + b'\n'
        return await self.send_command(command)

    async def enable_station(self, station_number: int) -> bool:
        """Enable a specific station"""
        command = ArduinoCommand.ENABLE_STATION + str(station_number).encode() + b'\n'
        return await self.send_command(command)

    async def disable_station(self, station_number: int) -> bool:
        """Disable a specific station"""
        command = ArduinoCommand.DISABLE_STATION + str(station_number).encode() + b'\n'
        return await self.send_command(command) 