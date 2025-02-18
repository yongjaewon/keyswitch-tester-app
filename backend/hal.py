import json
import asyncio
import logging
import os
from dotenv import load_dotenv
import serial.tools.list_ports

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'WARNING')))

# Import Dynamixel SDK constants and classes
from dynamixel_sdk import PortHandler, PacketHandler, COMM_SUCCESS

# Dynamixel constants
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
LEN_GOAL_POSITION = 4
PROTOCOL_VERSION = 2.0
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Dynamixel control table addresses
ADDR_OPERATING_MODE     = 11    # Operating mode
ADDR_TORQUE_ENABLE     = 64    # Torque Enable
ADDR_LED               = 65    # LED
ADDR_GOAL_CURRENT      = 102   # Goal Current
ADDR_GOAL_POSITION     = 116   # Goal Position
ADDR_PRESENT_POSITION  = 132   # Present Position
ADDR_MOVING            = 122   # Moving Status

# Other Dynamixel constants
POSITION_RESOLUTION    = 4096   # XM430 position resolution (0-4095)
CURRENT_BASED_MODE     = 5      # Current-based position control mode
POSITION_MODE          = 3      # Position control mode
BAUDRATE              = 57600
MOVING_THRESHOLD      = 20

def find_dynamixel_port():
    """
    Attempt to find the Dynamixel controller port by checking available serial ports.
    Returns the first port that matches known Dynamixel USB-to-Serial converter characteristics.
    """
    # Common vendor IDs and product IDs for USB-to-Serial converters used with Dynamixel
    # You may need to add more IDs based on your specific hardware
    DYNAMIXEL_VENDORS = {
        "0403",  # FTDI
        "10c4",  # Silicon Labs
        "067b",  # Prolific
    }
    
    available_ports = list(serial.tools.list_ports.comports())
    
    # First, try to find a port with matching vendor ID
    for port in available_ports:
        if hasattr(port, 'vid') and port.vid and hex(port.vid)[2:].lower() in DYNAMIXEL_VENDORS:
            logger.info(f"Found likely Dynamixel controller on port {port.device}")
            return port.device
            
    # If no matching vendor ID found, return the first USB serial port as fallback
    for port in available_ports:
        if "USB" in port.device:
            logger.info(f"Using fallback USB serial port {port.device}")
            return port.device
            
    # If no USB serial ports found, try common port names based on OS
    if os.name == 'nt':  # Windows
        default_ports = ['COM3', 'COM4']
    else:  # Linux/Mac
        default_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/tty.usbserial-*']
        
    for port in default_ports:
        try:
            if serial.Serial(port).is_open:
                logger.info(f"Found working serial port {port}")
                return port
        except:
            continue
            
    logger.error("No suitable serial port found for Dynamixel controller")
    return None

class SensorModule:
    def __init__(self, config):
        self.config = config
        self.mode = self.config["phidgets"]["sensor_mode"]  # "event" or "polling"
        self.data_interval = self.config["phidgets"]["data_interval"]  # in milliseconds
        self.ports = self.config["phidgets"]["ports"]
        self.latest_readings = {}
        self.task = None
        self.sensor_instances = {}

    def _handle_voltage_change(self, sensor_name, voltage):
        if sensor_name == 'switch_current':
            # Convert voltage to current (amperes) using formula: (V - 2.5) / 0.0625
            current = (voltage - 2.5) / 0.0625
            self.latest_readings[sensor_name] = current
            logger.warning(f"{sensor_name}: {voltage:.3f}V = {current:.3f}A")
        elif sensor_name == 'motor_current':
            # TODO: Implement motor current conversion when needed
            self.latest_readings[sensor_name] = voltage  # Store raw voltage for now
        else:
            # For non-current sensors (like supply_voltage), store voltage as-is
            self.latest_readings[sensor_name] = voltage

    def _initialize_sensors(self):
        from Phidget22.Devices.VoltageInput import VoltageInput
        for sensor_name, port in self.ports.items():
            sensor = VoltageInput()
            sensor.setHubPort(port)
            sensor.setIsHubPortDevice(True)
            try:
                sensor.openWaitForAttachment(5000)
                logger.info(f"Sensor {sensor_name} attached on port {port}.")
            except Exception as e:
                logger.error(f"Failed to attach sensor {sensor_name} on port {port}: {e}")
                continue
            if self.mode == "event":
                # Attach event handler. The handler signature: (voltage_input, voltage)
                sensor.setOnVoltageChangeHandler(lambda voltage_input, voltage, sn=sensor_name: self._handle_voltage_change(sn, voltage))
            self.sensor_instances[sensor_name] = sensor

    async def start(self):
        # Initialize sensors using Phidgets API
        self._initialize_sensors()
        if self.mode == "polling":
            logger.info("Starting sensor polling loop.")
            self.task = asyncio.create_task(self._poll_loop())
        elif self.mode == "event":
            logger.info("Sensors are running in event mode.")
            # In event mode, sensors update readings via callbacks. No polling loop is needed.
        else:
            logger.error(f"Unknown sensor mode: {self.mode}")

    async def _poll_loop(self):
        while True:
            for sensor_name, sensor in self.sensor_instances.items():
                try:
                    voltage = sensor.getVoltage()
                    self._handle_voltage_change(sensor_name, voltage)
                except Exception as e:
                    logger.error(f"Error reading sensor {sensor_name}: {e}")
            await asyncio.sleep(self.data_interval / 1000.0)

    def get_latest(self):
        return self.latest_readings

    def stop(self):
        if self.task:
            self.task.cancel()
        for sensor_name, sensor in self.sensor_instances.items():
            try:
                sensor.close()
                logger.info(f"Sensor {sensor_name} closed.")
            except Exception as e:
                logger.error(f"Error closing sensor {sensor_name}: {e}")
        logger.info("Sensor module stopped.")


class ActuatorModule:
    def __init__(self, config):
        self.config = config
        self.default_target_angle = self.config["servo"]["default_target_angle"]
        self.current_limit_percent = self.config["servo"]["current_limit_percent"]
        # Assuming servo IDs map directly: station 1 -> servo 1, etc.
        self.servo_ids = {1: 1, 2: 2, 3: 3, 4: 4}
        self.connected = False
        self.port_handler = None
        self.packet_handler = None
        self.safe_state_reached = False

    def _degrees_to_position(self, degrees):
        """Convert degrees to Dynamixel position value."""
        # Scale degrees (0-360) to position (0-4095)
        position = int((degrees * POSITION_RESOLUTION) / 360.0)
        return max(0, min(POSITION_RESOLUTION - 1, position))

    def _position_to_degrees(self, position):
        """Convert Dynamixel position value to degrees."""
        return (position * 360.0) / POSITION_RESOLUTION

    def _calculate_current_limit(self, percent):
        """Convert current limit percentage to Dynamixel value."""
        # XM430 current value range is 0-1193 (0% to 100%)
        max_current = 1193
        return int((percent * max_current) / 100.0)

    async def _setup_servo(self, servo_id):
        """Set up a servo for current-based position control."""
        try:
            # Disable torque to change operating mode
            result, error = self.packet_handler.write1ByteTxRx(
                self.port_handler, servo_id, ADDR_TORQUE_ENABLE, 0)
            if result != COMM_SUCCESS or error != 0:
                logger.error(f"Failed to disable torque on servo {servo_id}")
                return False

            # Set to current-based position control mode
            result, error = self.packet_handler.write1ByteTxRx(
                self.port_handler, servo_id, ADDR_OPERATING_MODE, CURRENT_BASED_MODE)
            if result != COMM_SUCCESS or error != 0:
                logger.error(f"Failed to set operating mode on servo {servo_id}")
                return False

            # Set current limit
            current_limit = self._calculate_current_limit(self.current_limit_percent)
            result, error = self.packet_handler.write2ByteTxRx(
                self.port_handler, servo_id, ADDR_GOAL_CURRENT, current_limit)
            if result != COMM_SUCCESS or error != 0:
                logger.error(f"Failed to set current limit on servo {servo_id}")
                return False

            # Enable torque
            result, error = self.packet_handler.write1ByteTxRx(
                self.port_handler, servo_id, ADDR_TORQUE_ENABLE, 1)
            if result != COMM_SUCCESS or error != 0:
                logger.error(f"Failed to enable torque on servo {servo_id}")
                return False

            logger.info(f"Successfully set up servo {servo_id} with current limit {self.current_limit_percent}%")
            return True

        except Exception as e:
            logger.error(f"Error setting up servo {servo_id}: {e}")
            return False

    async def connect(self):
        try:
            # Find and open port
            port = find_dynamixel_port()
            if not port:
                logger.error("No suitable port found for servo controller")
                return False

            self.port_handler = PortHandler(port)
            if not self.port_handler.openPort():
                logger.error(f"Failed to open port {port}")
                return False

            if not self.port_handler.setBaudRate(BAUDRATE):
                logger.error("Failed to set baudrate")
                return False

            self.packet_handler = PacketHandler(PROTOCOL_VERSION)
            
            # Set up each servo
            success = True
            for servo_id in self.servo_ids.values():
                if not await self._setup_servo(servo_id):
                    success = False
                    break

            if success:
                self.connected = True
                logger.info(f"Successfully connected and configured all servos on port {port}")
                return True
            else:
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Error during servo controller connection: {e}")
            return False

    async def disconnect(self):
        if self.connected and self.port_handler:
            # Disable torque on all servos
            for servo_id in self.servo_ids.values():
                try:
                    self.packet_handler.write1ByteTxRx(
                        self.port_handler, servo_id, ADDR_TORQUE_ENABLE, 0)
                except:
                    pass  # Ignore errors during disconnect
            self.port_handler.closePort()
            logger.info("Servo controller disconnected")
            self.connected = False

    async def command_servo(self, station_id, target_angle=None):
        if self.safe_state_reached:
            logger.warning("Cannot command servo because safe state is active")
            return False
        if not self.connected:
            logger.warning("Servo controller not connected")
            return False

        servo_id = self.servo_ids.get(station_id)
        if servo_id is None:
            logger.warning(f"No servo mapped for station {station_id}")
            return False

        if target_angle is None:
            target_angle = self.default_target_angle

        try:
            position = self._degrees_to_position(target_angle)
            
            result, error = self.packet_handler.write4ByteTxRx(
                self.port_handler, servo_id, ADDR_GOAL_POSITION, position)
            
            if result != COMM_SUCCESS or error != 0:
                logger.error(f"Failed to command servo {servo_id}: result={result}, error={error}")
                return False

            logger.warning(f"Commanded servo {servo_id} to {target_angle}° (pos: {position})")
            return True

        except Exception as e:
            logger.error(f"Error commanding servo {servo_id}: {e}")
            return False

    async def set_safe_state(self):
        if not self.connected:
            logger.warning("Servo controller not connected")
            return False

        if self.safe_state_reached:
            logger.warning("Safe state already reached")
            return True

        try:
            logger.warning("Setting safe state - moving servos to 0° and disabling torque")
            for servo_id in self.servo_ids.values():
                result, error = self.packet_handler.write4ByteTxRx(
                    self.port_handler, servo_id, ADDR_GOAL_POSITION, 0)
                if result != COMM_SUCCESS or error != 0:
                    logger.error(f"Failed to move servo {servo_id} to safe position")
                    continue

            await asyncio.sleep(1.0)

            for servo_id in self.servo_ids.values():
                result, error = self.packet_handler.write1ByteTxRx(
                    self.port_handler, servo_id, ADDR_TORQUE_ENABLE, 0)
                if result != COMM_SUCCESS or error != 0:
                    logger.error(f"Failed to disable torque on servo {servo_id}")
                    continue

            self.safe_state_reached = True
            logger.warning("Safe state reached: All servos at position 0 and torque disabled")
            return True

        except Exception as e:
            logger.error(f"Error setting safe state: {e}")
            return False

    async def reset_safe_state(self):
        if not self.connected:
            logger.warning("Servo controller not connected")
            return False

        try:
            logger.warning("Resetting safe state - reconfiguring servos for movement")
            success = True
            for servo_id in self.servo_ids.values():
                if not await self._setup_servo(servo_id):
                    success = False
                    break

            if success:
                self.safe_state_reached = False
                logger.warning("Safe state reset: All servos reconfigured and ready")
                return True
            else:
                logger.error("Failed to reset safe state: Error reconfiguring servos")
                return False

        except Exception as e:
            logger.error(f"Error resetting safe state: {e}")
            return False


class HardwareAbstractionLayer:
    def __init__(self, config_file="hardware_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.sensor_module = SensorModule(self.config)
        self.actuator_module = ActuatorModule(self.config)
        self.connected = False  # Track connection state

    def _load_config(self):
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            logger.info(f"Hardware configuration loaded from {self.config_file}.")
            return config
        except Exception as e:
            logger.error(f"Failed to load hardware configuration: {e}")
            raise

    async def connect(self):
        try:
            await self.sensor_module.start()
            await self.actuator_module.connect()
            self.connected = True  # Set connected to True after successful connection
            logger.info("Hardware Abstraction Layer connected.")
        except Exception as e:
            logger.error(f"Error connecting HAL: {e}")
            self.connected = False  # Ensure connected is False if connection fails

    async def disconnect(self):
        try:
            self.sensor_module.stop()
            await self.actuator_module.disconnect()
            self.connected = False  # Set connected to False after disconnection
            logger.info("Hardware Abstraction Layer disconnected.")
        except Exception as e:
            logger.error(f"Error disconnecting HAL: {e}")

    def get_sensor_data(self):
        return self.sensor_module.get_latest()

    async def command_servo(self, station_id, target_angle=None):
        return await self.actuator_module.command_servo(station_id, target_angle)

    async def set_safe_state(self):
        return await self.actuator_module.set_safe_state()

    async def reset_safe_state(self):
        return await self.actuator_module.reset_safe_state()

    async def update_settings(self, new_settings: dict):
        logger.info(f"Updating hardware settings: {new_settings}")
        # Future implementation: update sensor_module or actuator_module settings if needed.
        return True

    async def send_state(self, enabled_stations, speed, machine_state):
        logger.info(f"Sending HAL state: enabled_stations={enabled_stations}, speed={speed}, machine_state={machine_state}")
        # Future implementation: send actual commands to sensor or actuator modules as needed.
        return True

    # Additional methods to update settings can be added here 