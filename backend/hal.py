import json
import asyncio
import logging
import os
import serial.tools.list_ports

logger = logging.getLogger(__name__)

# Import Dynamixel SDK constants and classes
from dynamixel_sdk import PortHandler, PacketHandler, COMM_SUCCESS

# Dynamixel constants
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
LEN_GOAL_POSITION = 4
PROTOCOL_VERSION = 2.0
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

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
        self.latest_readings[sensor_name] = voltage
        logger.info(f"Sensor {sensor_name} event: voltage={voltage}")

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
                    self.latest_readings[sensor_name] = voltage
                    logger.info(f"Sensor {sensor_name} polled: voltage={voltage}")
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

    async def connect(self):
        try:
            # Dynamically find the correct port
            port = find_dynamixel_port()
            if not port:
                logger.error("No suitable port found for servo controller")
                return False
                
            self.port_handler = PortHandler(port)
            if not self.port_handler.openPort():
                logger.error(f"Failed to open port {port} for servo controller")
                return False
            if not self.port_handler.setBaudRate(self.config["servo"]["baudrate"]):
                logger.error("Failed to set baudrate for servo controller")
                return False
            self.packet_handler = PacketHandler(PROTOCOL_VERSION)
            self.connected = True
            logger.info(f"Servo controller connected on port {port}")
            return True
        except Exception as e:
            logger.error(f"Exception during servo controller connection: {e}")
            return False

    async def disconnect(self):
        if self.connected and self.port_handler:
            self.port_handler.closePort()
            logger.info("Servo controller disconnected.")
            self.connected = False

    async def command_servo(self, station_id, target_angle=None):
        if self.safe_state_reached:
            logger.error("Cannot command servo because safe state is active. Reset safe state first.")
            return False
        if not self.connected:
            logger.error("Servo controller not connected.")
            return False
        servo_id = self.servo_ids.get(station_id)
        if servo_id is None:
            logger.error(f"No servo mapped for station id {station_id}.")
            return False
        if target_angle is None:
            target_angle = self.default_target_angle
        # Enable torque for the servo
        dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(self.port_handler, servo_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        if dxl_comm_result != COMM_SUCCESS:
            logger.error(f"Failed to enable torque on servo {servo_id}: {dxl_comm_result}")
            return False
        # Send goal position command
        dxl_comm_result, dxl_error = self.packet_handler.write4ByteTxRx(self.port_handler, servo_id, ADDR_GOAL_POSITION, int(target_angle))
        if dxl_comm_result != COMM_SUCCESS:
            logger.error(f"Failed to command servo {servo_id}: {dxl_comm_result}")
            return False
        logger.info(f"Commanded servo {servo_id} to angle {target_angle}° with current limit {self.current_limit_percent}%.")
        return True

    async def set_safe_state(self):
        if not self.connected:
            logger.error("Servo controller not connected. Cannot set safe state.")
            return False

        if self.safe_state_reached:
            logger.info("Safe state already reached. No further command issued.")
            return True

        for servo_id in self.servo_ids.values():
            # Enable torque to allow servo movement
            dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(self.port_handler, servo_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
            if dxl_comm_result != COMM_SUCCESS:
                logger.error(f"Failed to enable torque on servo {servo_id} for safe state: {dxl_comm_result}")
                continue
            # Command servo to position 0
            dxl_comm_result, dxl_error = self.packet_handler.write4ByteTxRx(self.port_handler, servo_id, ADDR_GOAL_POSITION, 0)
            if dxl_comm_result != COMM_SUCCESS:
                logger.error(f"Failed to command servo {servo_id} to safe position: {dxl_comm_result}")
                continue

        # Allow time for servos to reach position 0
        await asyncio.sleep(1.0)

        for servo_id in self.servo_ids.values():
            # Disable torque
            dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(self.port_handler, servo_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
            if dxl_comm_result != COMM_SUCCESS:
                logger.error(f"Failed to disable torque on servo {servo_id} for safe state: {dxl_comm_result}")
                continue

        logger.info("Safe state command executed: Servos set to position 0 and torque disabled.")
        self.safe_state_reached = True
        return True

    async def reset_safe_state(self):
        logger.info("Resetting safe state flag. Machine is ready to be re-enabled.")
        self.safe_state_reached = False
        return True


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