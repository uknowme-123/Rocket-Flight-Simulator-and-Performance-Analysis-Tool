"""
Synthetic Avionics Sensor Generation Module.

This module converts the simulator's ground-truth flight data into realistic
simulated avionics sensor measurements. All generated values are SYNTHETIC
and clearly identified as such - they are not actual physical sensor readings.

Sensor models implemented:
- Accelerometer (3-axis, measures specific force including gravity)
- Gyroscope (3-axis, measures angular rate)
- Barometric Altimeter (pressure altitude)
- GPS Altitude (geometric altitude)
- GPS Velocity (3D velocity vector)

Each sensor supports configurable noise, bias, sampling rate, and dropout.
All sensors derive measurements from the existing simulator's ground-truth data.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Literal, ClassVar
import random
import math
import warnings

import numpy as np
import pandas as pd

from .telemetry_schema import TelemetryFieldType, TelemetryValidity, TELEMETRY_SCHEMA_BY_NAME


# =============================================================================
# Sensor Types and Configuration
# =============================================================================

class SensorType(str, Enum):
    """Supported synthetic sensor types."""
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    BAROMETRIC_ALTIMETER = "barometric_altimeter"
    GPS_ALTITUDE = "gps_altitude"
    GPS_VELOCITY = "gps_velocity"


class SensorValidity(str, Enum):
    """Validity status for individual sensor measurements."""
    VALID = "valid"
    INVALID = "invalid"
    DROPOUT = "dropout"      # Sensor failed to produce reading
    DISABLED = "disabled"    # Sensor not enabled in configuration


class PacketValidity(str, Enum):
    """Overall validity status for a sensor packet."""
    VALID = "valid"
    DEGRADED = "degraded"    # Some sensors invalid/dropped out
    INVALID = "invalid"      # Critical sensors missing or all sensors failed


@dataclass(frozen=True)
class SensorConfig:
    """
    Configuration for a single synthetic sensor.

    Attributes:
        sensor_type: Type of sensor
        enabled: Whether sensor is active
        sample_rate_hz: Output sample rate (must divide evenly into simulator rate)
        noise_std: Standard deviation of Gaussian measurement noise (in sensor units)
        bias: Constant additive bias (in sensor units)
        dropout_prob: Probability of sensor dropout per sample [0, 1]
        axis_misalignment_deg: Axis misalignment angle in degrees (for IMU sensors)
    """
    sensor_type: SensorType
    enabled: bool = True
    sample_rate_hz: float = 10.0
    noise_std: float = 0.0
    bias: float = 0.0
    dropout_prob: float = 0.0
    axis_misalignment_deg: float = 0.0

    def __post_init__(self) -> None:
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.noise_std < 0:
            raise ValueError("noise_std must be non-negative")
        if not 0.0 <= self.dropout_prob <= 1.0:
            raise ValueError("dropout_prob must be in [0, 1]")
        if self.axis_misalignment_deg < 0:
            raise ValueError("axis_misalignment_deg must be non-negative")


@dataclass(frozen=True)
class SensorSuiteConfig:
    """
    Complete sensor suite configuration.

    All sensors share the same random seed for reproducibility.
    """
    accelerometer: SensorConfig = field(default_factory=lambda: SensorConfig(
        sensor_type=SensorType.ACCELEROMETER,
        sample_rate_hz=10.0,
        noise_std=0.05,       # ~0.05 m/s^2 (5 mg) typical MEMS noise
        bias=0.0,
        dropout_prob=0.0,
    ))
    gyroscope: SensorConfig = field(default_factory=lambda: SensorConfig(
        sensor_type=SensorType.GYROSCOPE,
        sample_rate_hz=10.0,
        noise_std=0.001,      # ~0.001 rad/s typical MEMS noise
        bias=0.0,
        dropout_prob=0.0,
    ))
    barometric_altimeter: SensorConfig = field(default_factory=lambda: SensorConfig(
        sensor_type=SensorType.BAROMETRIC_ALTIMETER,
        sample_rate_hz=10.0,
        noise_std=1.0,        # ~1 m typical barometric noise
        bias=0.0,
        dropout_prob=0.0,
    ))
    gps_altitude: SensorConfig = field(default_factory=lambda: SensorConfig(
        sensor_type=SensorType.GPS_ALTITUDE,
        sample_rate_hz=5.0,   # GPS typically slower
        noise_std=3.0,        # ~3 m typical GPS altitude noise
        bias=0.0,
        dropout_prob=0.01,
    ))
    gps_velocity: SensorConfig = field(default_factory=lambda: SensorConfig(
        sensor_type=SensorType.GPS_VELOCITY,
        sample_rate_hz=5.0,
        noise_std=0.05,       # ~0.05 m/s typical GPS velocity noise
        bias=0.0,
        dropout_prob=0.01,
    ))

    # Global settings
    seed: int | None = 42
    simulator_rate_hz: float = 10.0  # Base simulator sample rate

    def __post_init__(self) -> None:
        # Validate sample rates divide evenly into simulator rate
        for sensor_config in [self.accelerometer, self.gyroscope,
                              self.barometric_altimeter, self.gps_altitude,
                              self.gps_velocity]:
            if sensor_config.enabled:
                ratio = self.simulator_rate_hz / sensor_config.sample_rate_hz
                if not math.isclose(ratio, round(ratio), rel_tol=1e-9):
                    warnings.warn(
                        f"{sensor_config.sensor_type.value} sample rate "
                        f"{sensor_config.sample_rate_hz} Hz does not evenly divide "
                        f"simulator rate {self.simulator_rate_hz} Hz. "
                        f"Downsampling may be approximate.",
                        UserWarning,
                        stacklevel=2,
                    )


# =============================================================================
# Sensor Output Data Structures
# =============================================================================

@dataclass
class SensorReading:
    """
    A single sensor measurement with validity.

    All values are SYNTHETIC - generated from ground truth with noise/bias.
    """
    sensor_type: SensorType
    value: float | tuple[float, float, float]  # Scalar or 3-axis vector
    unit: str
    validity: SensorValidity
    timestamp_s: float
    sequence: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.validity == SensorValidity.VALID

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = {
            "sensor_type": self.sensor_type.value,
            "unit": self.unit,
            "validity": self.validity.value,
            "timestamp_s": self.timestamp_s,
            "sequence": self.sequence,
            "metadata": self.metadata,
        }
        if isinstance(self.value, tuple):
            d["value_x"] = self.value[0]
            d["value_y"] = self.value[1]
            d["value_z"] = self.value[2]
        else:
            d["value"] = self.value
        return d


@dataclass
class SensorPacket:
    """
    Complete sensor packet for one timestep.

    Contains readings from all enabled sensors at a given timestamp.
    Suitable for serialization and transmission to embedded hardware.
    """
    timestamp_s: float
    sequence: int
    readings: dict[SensorType, SensorReading]
    packet_validity: PacketValidity
    is_synthetic: bool = True  # Always True - these are simulated readings
    simulator_time_s: float = 0.0  # Corresponding simulator ground-truth time

    def get_reading(self, sensor_type: SensorType) -> SensorReading | None:
        """Get reading for a specific sensor type."""
        return self.readings.get(sensor_type)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization (JSON, CBOR, etc.)."""
        return {
            "timestamp_s": self.timestamp_s,
            "sequence": self.sequence,
            "packet_validity": self.packet_validity.value,
            "is_synthetic": self.is_synthetic,
            "simulator_time_s": self.simulator_time_s,
            "readings": {st.value: r.to_dict() for st, r in self.readings.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SensorPacket":
        """Reconstruct from dictionary."""
        readings = {}
        for st_str, rd in data.get("readings", {}).items():
            sensor_type = SensorType(st_str)
            if "value" in rd:
                value = rd["value"]
            else:
                value = (rd["value_x"], rd["value_y"], rd["value_z"])
            readings[sensor_type] = SensorReading(
                sensor_type=sensor_type,
                value=value,
                unit=rd["unit"],
                validity=SensorValidity(rd["validity"]),
                timestamp_s=rd["timestamp_s"],
                sequence=rd["sequence"],
                metadata=rd.get("metadata", {}),
            )
        return cls(
            timestamp_s=data["timestamp_s"],
            sequence=data["sequence"],
            readings=readings,
            packet_validity=PacketValidity(data["packet_validity"]),
            is_synthetic=data.get("is_synthetic", True),
            simulator_time_s=data.get("simulator_time_s", 0.0),
        )


# =============================================================================
# Sensor Models
# =============================================================================

class BaseSensor:
    """Base class for synthetic sensors."""

    def __init__(self, config: SensorConfig, rng: random.Random):
        self.config = config
        self.rng = rng
        self._sequence = 0

    def _should_dropout(self) -> bool:
        return self.config.dropout_prob > 0 and self.rng.random() < self.config.dropout_prob

    def _apply_noise(self, value: float) -> float:
        if self.config.noise_std > 0:
            return value + self.rng.gauss(0.0, self.config.noise_std)
        return value

    def _apply_bias(self, value: float) -> float:
        return value + self.config.bias

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        """Generate a sensor reading from ground truth. Override in subclasses."""
        raise NotImplementedError


class AccelerometerSensor(BaseSensor):
    """
    Synthetic 3-axis accelerometer.

    Measures specific force (acceleration minus gravity) in the body frame.
    For this vertical flight simulator, we assume:
    - Vehicle flies vertically (no attitude change)
    - Body Z axis aligns with vertical
    - X and Y axes measure near-zero (with noise)
    """
    UNIT = "m/s^2"
    SENSOR_TYPE = SensorType.ACCELEROMETER

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        seq = self._next_sequence()

        if not self.config.enabled:
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(0.0, 0.0, 0.0),
                unit=self.UNIT,
                validity=SensorValidity.DISABLED,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"enabled": False},
            )

        if self._should_dropout():
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(float("nan"), float("nan"), float("nan")),
                unit=self.UNIT,
                validity=SensorValidity.DROPOUT,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"dropout": True},
            )

        # Ground truth acceleration (includes gravity, positive up)
        accel_truth = ground_truth.get("acceleration_mps2", 0.0)

        # In body frame (vertical flight): Z measures specific force = accel - gravity
        # But our ground truth already includes gravity. Specific force = a - g
        # For vertical flight with Z up: specific force_z = accel_truth - (-GRAVITY) = accel_truth + GRAVITY
        # Wait: ground truth acceleration_mps2 includes gravity (F_net/m).
        # Accelerometer measures specific force = proper acceleration = a - g
        # In ENU frame with Z up: g = (0, 0, -9.81)
        # So specific force = (0, 0, accel_truth) - (0, 0, -9.81) = (0, 0, accel_truth + 9.81)
        from .config import GRAVITY
        specific_force_z = accel_truth + GRAVITY

        # X and Y axes: near zero (vehicle assumed vertical)
        ax = self._apply_bias(self._apply_noise(0.0))
        ay = self._apply_bias(self._apply_noise(0.0))
        az = self._apply_bias(self._apply_noise(specific_force_z))

        # Apply axis misalignment (simple rotation around X for demo)
        if self.config.axis_misalignment_deg > 0:
            theta = math.radians(self.config.axis_misalignment_deg)
            ay, az = ay * math.cos(theta) - az * math.sin(theta), ay * math.sin(theta) + az * math.cos(theta)

        return SensorReading(
            sensor_type=self.SENSOR_TYPE,
            value=(ax, ay, az),
            unit=self.UNIT,
            validity=SensorValidity.VALID,
            timestamp_s=timestamp_s,
            sequence=seq,
            metadata={
                "ground_truth_accel_mps2": accel_truth,
                "ground_truth_specific_force_z": specific_force_z,
                "axis_misalignment_deg": self.config.axis_misalignment_deg,
            },
        )


class GyroscopeSensor(BaseSensor):
    """
    Synthetic 3-axis gyroscope.

    Measures angular rate in body frame. For vertical flight with no attitude
    control, true angular rate is zero. This sensor only outputs noise and bias.
    """
    UNIT = "rad/s"
    SENSOR_TYPE = SensorType.GYROSCOPE

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        seq = self._next_sequence()

        if not self.config.enabled:
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(0.0, 0.0, 0.0),
                unit=self.UNIT,
                validity=SensorValidity.DISABLED,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"enabled": False},
            )

        if self._should_dropout():
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(float("nan"), float("nan"), float("nan")),
                unit=self.UNIT,
                validity=SensorValidity.DROPOUT,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"dropout": True},
            )

        # True angular rate is zero for vertical flight
        gx = self._apply_bias(self._apply_noise(0.0))
        gy = self._apply_bias(self._apply_noise(0.0))
        gz = self._apply_bias(self._apply_noise(0.0))

        return SensorReading(
            sensor_type=self.SENSOR_TYPE,
            value=(gx, gy, gz),
            unit=self.UNIT,
            validity=SensorValidity.VALID,
            timestamp_s=timestamp_s,
            sequence=seq,
            metadata={
                "ground_truth_angular_rate_rad_s": (0.0, 0.0, 0.0),
                "note": "Vertical flight assumed - no true rotation",
            },
        )


class BarometricAltimeterSensor(BaseSensor):
    """
    Synthetic barometric altimeter.

    Converts geometric altitude to pressure altitude using standard atmosphere.
    Adds noise and bias.
    """
    UNIT = "m"
    SENSOR_TYPE = SensorType.BAROMETRIC_ALTIMETER

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        seq = self._next_sequence()

        if not self.config.enabled:
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=0.0,
                unit=self.UNIT,
                validity=SensorValidity.DISABLED,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"enabled": False},
            )

        if self._should_dropout():
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=float("nan"),
                unit=self.UNIT,
                validity=SensorValidity.DROPOUT,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"dropout": True},
            )

        altitude_truth = ground_truth.get("altitude_m", 0.0)

        # For small altitudes, pressure altitude ≈ geometric altitude
        # (Real implementation would use ISA pressure model)
        pressure_altitude = altitude_truth

        measured = self._apply_bias(self._apply_noise(pressure_altitude))
        # Barometric altitude cannot be negative
        measured = max(0.0, measured)

        return SensorReading(
            sensor_type=self.SENSOR_TYPE,
            value=measured,
            unit=self.UNIT,
            validity=SensorValidity.VALID,
            timestamp_s=timestamp_s,
            sequence=seq,
            metadata={
                "ground_truth_altitude_m": altitude_truth,
                "model": "pressure_altitude_approx",
            },
        )


class GPSAltitudeSensor(BaseSensor):
    """
    Synthetic GPS altitude sensor.

    Provides geometric altitude with typical GPS noise characteristics.
    Lower sample rate than IMU/barometer.
    """
    UNIT = "m"
    SENSOR_TYPE = SensorType.GPS_ALTITUDE

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        seq = self._next_sequence()

        if not self.config.enabled:
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=0.0,
                unit=self.UNIT,
                validity=SensorValidity.DISABLED,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"enabled": False},
            )

        if self._should_dropout():
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=float("nan"),
                unit=self.UNIT,
                validity=SensorValidity.DROPOUT,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"dropout": True},
            )

        altitude_truth = ground_truth.get("altitude_m", 0.0)
        measured = self._apply_bias(self._apply_noise(altitude_truth))
        measured = max(0.0, measured)

        return SensorReading(
            sensor_type=self.SENSOR_TYPE,
            value=measured,
            unit=self.UNIT,
            validity=SensorValidity.VALID,
            timestamp_s=timestamp_s,
            sequence=seq,
            metadata={
                "ground_truth_altitude_m": altitude_truth,
                "note": "Geometric altitude from GPS",
            },
        )


class GPSVelocitySensor(BaseSensor):
    """
    Synthetic GPS velocity sensor.

    Provides 3D velocity vector. For vertical flight, only Z component is non-zero.
    """
    UNIT = "m/s"
    SENSOR_TYPE = SensorType.GPS_VELOCITY

    def generate(self, timestamp_s: float, ground_truth: dict[str, float]) -> SensorReading:
        seq = self._next_sequence()

        if not self.config.enabled:
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(0.0, 0.0, 0.0),
                unit=self.UNIT,
                validity=SensorValidity.DISABLED,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"enabled": False},
            )

        if self._should_dropout():
            return SensorReading(
                sensor_type=self.SENSOR_TYPE,
                value=(float("nan"), float("nan"), float("nan")),
                unit=self.UNIT,
                validity=SensorValidity.DROPOUT,
                timestamp_s=timestamp_s,
                sequence=seq,
                metadata={"dropout": True},
            )

        velocity_truth = ground_truth.get("velocity_mps", 0.0)
        # Vertical flight: X=0, Y=0, Z=velocity (ENU frame, up positive)
        vx = self._apply_bias(self._apply_noise(0.0))
        vy = self._apply_bias(self._apply_noise(0.0))
        vz = self._apply_bias(self._apply_noise(velocity_truth))

        return SensorReading(
            sensor_type=self.SENSOR_TYPE,
            value=(vx, vy, vz),
            unit=self.UNIT,
            validity=SensorValidity.VALID,
            timestamp_s=timestamp_s,
            sequence=seq,
            metadata={
                "ground_truth_velocity_mps": velocity_truth,
                "frame": "ENU",
            },
        )


# =============================================================================
# Sensor Suite Generator
# =============================================================================

@dataclass
class SensorSuite:
    """
    Generates synchronized sensor packets from simulator ground-truth data.

    This is the main entry point for generating synthetic sensor data from
    a completed simulation run.
    """
    config: SensorSuiteConfig

    def __post_init__(self) -> None:
        # Initialize RNG
        self.rng = random.Random(self.config.seed)
        # Use separate RNGs for each sensor for independence
        self.sensor_rngs = {
            SensorType.ACCELEROMETER: random.Random(self.rng.getrandbits(64)),
            SensorType.GYROSCOPE: random.Random(self.rng.getrandbits(64)),
            SensorType.BAROMETRIC_ALTIMETER: random.Random(self.rng.getrandbits(64)),
            SensorType.GPS_ALTITUDE: random.Random(self.rng.getrandbits(64)),
            SensorType.GPS_VELOCITY: random.Random(self.rng.getrandbits(64)),
        }

        # Create sensor instances
        self.sensors = {
            SensorType.ACCELEROMETER: AccelerometerSensor(
                self.config.accelerometer, self.sensor_rngs[SensorType.ACCELEROMETER]
            ),
            SensorType.GYROSCOPE: GyroscopeSensor(
                self.config.gyroscope, self.sensor_rngs[SensorType.GYROSCOPE]
            ),
            SensorType.BAROMETRIC_ALTIMETER: BarometricAltimeterSensor(
                self.config.barometric_altimeter, self.sensor_rngs[SensorType.BAROMETRIC_ALTIMETER]
            ),
            SensorType.GPS_ALTITUDE: GPSAltitudeSensor(
                self.config.gps_altitude, self.sensor_rngs[SensorType.GPS_ALTITUDE]
            ),
            SensorType.GPS_VELOCITY: GPSVelocitySensor(
                self.config.gps_velocity, self.sensor_rngs[SensorType.GPS_VELOCITY]
            ),
        }

        # Calculate downsampling intervals
        self.simulator_dt = 1.0 / self.config.simulator_rate_hz
        self.sample_intervals = {}
        for st, sensor in self.sensors.items():
            if sensor.config.enabled:
                interval = self.config.simulator_rate_hz / sensor.config.sample_rate_hz
                self.sample_intervals[st] = max(1, round(interval))
            else:
                self.sample_intervals[st] = None

        self._packet_sequence = 0

    def _get_ground_truth_at_time(self, telemetry: pd.DataFrame, time_s: float) -> dict[str, float]:
        """Interpolate ground truth at given time (nearest sample for now)."""
        # Find closest time index
        idx = (telemetry["time_s"] - time_s).abs().idxmin()
        row = telemetry.iloc[idx]
        return row.to_dict()

    def _compute_packet_validity(self, readings: dict[SensorType, SensorReading]) -> PacketValidity:
        """Determine overall packet validity from individual sensor validities."""
        valid_count = sum(1 for r in readings.values() if r.validity == SensorValidity.VALID)
        enabled_count = sum(1 for s in self.sensors.values() if s.config.enabled)

        if valid_count == 0:
            return PacketValidity.INVALID
        elif valid_count < enabled_count:
            return PacketValidity.DEGRADED
        return PacketValidity.VALID

    def generate_packet(self, telemetry: pd.DataFrame, sim_index: int) -> SensorPacket:
        """
        Generate a sensor packet for the simulator timestep at sim_index.

        Args:
            telemetry: Full simulation telemetry DataFrame
            sim_index: Index in telemetry DataFrame

        Returns:
            SensorPacket with readings from all sensors
        """
        self._packet_sequence += 1

        sim_time = telemetry.iloc[sim_index]["time_s"]
        ground_truth = self._get_ground_truth_at_time(telemetry, sim_time)

        readings = {}
        for sensor_type, sensor in self.sensors.items():
            # Check if this sensor should sample at this timestep
            interval = self.sample_intervals[sensor_type]
            if not sensor.config.enabled:
                # Sensor disabled - add DISABLED reading
                readings[sensor_type] = SensorReading(
                    sensor_type=sensor_type,
                    value=(0.0, 0.0, 0.0) if sensor_type in (SensorType.ACCELEROMETER,
                                                             SensorType.GYROSCOPE,
                                                             SensorType.GPS_VELOCITY) else 0.0,
                    unit=sensor.UNIT,
                    validity=SensorValidity.DISABLED,
                    timestamp_s=sim_time,
                    sequence=0,
                    metadata={"enabled": False},
                )
            elif interval is not None and sim_index % interval == 0:
                readings[sensor_type] = sensor.generate(sim_time, ground_truth)
            else:
                # Sensor enabled but not sampling this timestep - mark as invalid
                readings[sensor_type] = SensorReading(
                    sensor_type=sensor_type,
                    value=(0.0, 0.0, 0.0) if sensor_type in (SensorType.ACCELEROMETER,
                                                             SensorType.GYROSCOPE,
                                                             SensorType.GPS_VELOCITY) else 0.0,
                    unit=sensor.UNIT,
                    validity=SensorValidity.INVALID,
                    timestamp_s=sim_time,
                    sequence=0,
                    metadata={"not_sampled": True, "interval": interval},
                )

        packet_validity = self._compute_packet_validity(readings)

        return SensorPacket(
            timestamp_s=sim_time,
            sequence=self._packet_sequence,
            readings=readings,
            packet_validity=packet_validity,
            is_synthetic=True,
            simulator_time_s=sim_time,
        )

    def generate_all_packets(self, telemetry: pd.DataFrame) -> list[SensorPacket]:
        """
        Generate sensor packets for all simulation timesteps.

        Args:
            telemetry: Simulation output DataFrame

        Returns:
            List of SensorPacket, one per simulator timestep
        """
        self._packet_sequence = 0
        return [self.generate_packet(telemetry, i) for i in range(len(telemetry))]


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_sensor_packets(
    telemetry: pd.DataFrame,
    config: SensorSuiteConfig | None = None,
) -> list[SensorPacket]:
    """
    Generate synthetic sensor packets from simulation telemetry.

    Args:
        telemetry: Simulation output DataFrame (from RocketSimulator.run())
        config: Sensor suite configuration (uses defaults if None)

    Returns:
        List of SensorPacket objects
    """
    if config is None:
        config = SensorSuiteConfig()
    suite = SensorSuite(config)
    return suite.generate_all_packets(telemetry)


def packets_to_dataframe(packets: list[SensorPacket]) -> pd.DataFrame:
    """
    Convert list of sensor packets to a flat DataFrame for analysis.

    Each row is one sensor reading with columns:
    timestamp_s, sequence, sensor_type, validity, value_x, value_y, value_z, unit, ...
    """
    rows = []
    for packet in packets:
        for reading in packet.readings.values():
            row = {
                "packet_timestamp_s": packet.timestamp_s,
                "packet_sequence": packet.sequence,
                "packet_validity": packet.packet_validity.value,
                "sensor_type": reading.sensor_type.value,
                "sensor_validity": reading.validity.value,
                "sensor_timestamp_s": reading.timestamp_s,
                "sensor_sequence": reading.sequence,
                "unit": reading.unit,
            }
            if isinstance(reading.value, tuple):
                row["value_x"] = reading.value[0]
                row["value_y"] = reading.value[1]
                row["value_z"] = reading.value[2]
            else:
                row["value"] = reading.value
            row.update({f"meta_{k}": v for k, v in reading.metadata.items()})
            rows.append(row)
    return pd.DataFrame(rows)


# =============================================================================
# Sensor Schema for Documentation/Serialization
# =============================================================================

SENSOR_SCHEMA: dict[str, dict[str, Any]] = {
    "accelerometer": {
        "type": SensorType.ACCELEROMETER.value,
        "description": "3-axis accelerometer measuring specific force (proper acceleration)",
        "unit": "m/s^2",
        "axes": ["x", "y", "z"],
        "frame": "body",
        "measures": "specific_force = acceleration - gravity",
        "typical_noise_std": 0.05,
        "typical_bias": 0.0,
        "note": "SYNTHETIC - derived from simulator ground truth acceleration_mps2",
    },
    "gyroscope": {
        "type": SensorType.GYROSCOPE.value,
        "description": "3-axis gyroscope measuring angular rate",
        "unit": "rad/s",
        "axes": ["x", "y", "z"],
        "frame": "body",
        "measures": "angular_rate",
        "typical_noise_std": 0.001,
        "typical_bias": 0.0,
        "note": "SYNTHETIC - vertical flight assumed, true angular rate = 0",
    },
    "barometric_altimeter": {
        "type": SensorType.BAROMETRIC_ALTIMETER.value,
        "description": "Barometric pressure altitude",
        "unit": "m",
        "axes": ["altitude"],
        "frame": "pressure",
        "measures": "pressure_altitude",
        "typical_noise_std": 1.0,
        "typical_bias": 0.0,
        "note": "SYNTHETIC - approximated as geometric altitude for low altitudes",
    },
    "gps_altitude": {
        "type": SensorType.GPS_ALTITUDE.value,
        "description": "GPS geometric altitude",
        "unit": "m",
        "axes": ["altitude"],
        "frame": "WGS84/ENU",
        "measures": "geometric_altitude",
        "typical_noise_std": 3.0,
        "typical_bias": 0.0,
        "note": "SYNTHETIC - derived from simulator ground truth altitude_m",
    },
    "gps_velocity": {
        "type": SensorType.GPS_VELOCITY.value,
        "description": "GPS 3D velocity vector",
        "unit": "m/s",
        "axes": ["x", "y", "z"],
        "frame": "ENU",
        "measures": "velocity",
        "typical_noise_std": 0.05,
        "typical_bias": 0.0,
        "note": "SYNTHETIC - vertical flight assumed, X=Y=0, Z=velocity_mps",
    },
}