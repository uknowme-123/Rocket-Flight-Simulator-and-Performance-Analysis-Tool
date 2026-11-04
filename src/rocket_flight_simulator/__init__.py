"""Rocket Flight Simulator and Performance Analysis Tool.

A physics-based aerospace simulation toolkit for modelling rocket flight dynamics,
trajectory analysis, altitude prediction, and mission performance evaluation.
"""

from .config import (
    GRAVITY,
    AIR_DENSITY,
    TIME_STEP,
    DEFAULT_DRAG_COEFFICIENT,
    DEFAULT_CROSS_SECTIONAL_AREA,
    MAX_SIMULATION_TIME,
    DEFAULT_PROPELLANT_FRACTION,
)

from .rocket import Rocket
from .simulator import RocketSimulator, SimulationResult
from .telemetry import TelemetryLogger
from .telemetry_schema import (
    TelemetryField,
    TelemetryFieldType,
    TelemetryValidity,
    TELEMETRY_SCHEMA,
    TELEMETRY_SCHEMA_BY_NAME,
    REQUIRED_FIELDS,
    CONDITIONAL_FIELDS,
    ALL_FIELDS,
    validate_telemetry_dataframe,
    get_schema_json,
    get_field_info,
    get_fields_by_validity,
    FLIGHT_PHASES,
)
from .mission import analyze_mission, build_phase_timeline
from .atmosphere import get_air_density
from .propulsion import (
    get_thrust,
    estimate_total_impulse,
    calculate_specific_impulse,
    calculate_mass_flow_rate,
)
from .physics import (
    calculate_gravity,
    calculate_drag,
    calculate_net_force,
    calculate_acceleration,
)
from .flight_phases import FlightPhase, detect_flight_phase
from .rocket_library import (
    load_rocket_library,
    get_rocket_names,
    get_rocket_by_name,
    return_vehicle_summary,
    map_vehicle_to_simulator_parameters,
    build_comparison_rows,
    RocketRecord,
)
from .visualization import generate_plots
from .report_generator import generate_mission_report
from .sensors import (
    SensorType,
    SensorValidity,
    PacketValidity,
    SensorConfig,
    SensorSuiteConfig,
    SensorReading,
    SensorPacket,
    SensorSuite,
    AccelerometerSensor,
    GyroscopeSensor,
    BarometricAltimeterSensor,
    GPSAltitudeSensor,
    GPSVelocitySensor,
    generate_sensor_packets,
    packets_to_dataframe,
    SENSOR_SCHEMA,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "GRAVITY",
    "AIR_DENSITY",
    "TIME_STEP",
    "DEFAULT_DRAG_COEFFICIENT",
    "DEFAULT_CROSS_SECTIONAL_AREA",
    "MAX_SIMULATION_TIME",
    "DEFAULT_PROPELLANT_FRACTION",
    # Core classes
    "Rocket",
    "RocketSimulator",
    "SimulationResult",
    "TelemetryLogger",
    # Telemetry schema
    "TelemetryField",
    "TelemetryFieldType",
    "TelemetryValidity",
    "TELEMETRY_SCHEMA",
    "TELEMETRY_SCHEMA_BY_NAME",
    "REQUIRED_FIELDS",
    "CONDITIONAL_FIELDS",
    "ALL_FIELDS",
    "validate_telemetry_dataframe",
    "get_schema_json",
    "get_field_info",
    "get_fields_by_validity",
    "FLIGHT_PHASES",
    # Mission analysis
    "analyze_mission",
    "build_phase_timeline",
    # Physics modules
    "get_air_density",
    "get_thrust",
    "estimate_total_impulse",
    "calculate_specific_impulse",
    "calculate_mass_flow_rate",
    "calculate_gravity",
    "calculate_drag",
    "calculate_net_force",
    "calculate_acceleration",
    "FlightPhase",
    "detect_flight_phase",
    # Rocket library
    "load_rocket_library",
    "get_rocket_names",
    "get_rocket_by_name",
    "return_vehicle_summary",
    "map_vehicle_to_simulator_parameters",
    "build_comparison_rows",
    "RocketRecord",
    # Visualization & reports
    "generate_plots",
    "generate_mission_report",
    # Sensors
    "SensorType",
    "SensorValidity",
    "PacketValidity",
    "SensorConfig",
    "SensorSuiteConfig",
    "SensorReading",
    "SensorPacket",
    "SensorSuite",
    "AccelerometerSensor",
    "GyroscopeSensor",
    "BarometricAltimeterSensor",
    "GPSAltitudeSensor",
    "GPSVelocitySensor",
    "generate_sensor_packets",
    "packets_to_dataframe",
    "SENSOR_SCHEMA",
]