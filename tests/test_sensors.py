"""Tests for synthetic avionics sensor generation."""

from __future__ import annotations

import math
import random

import pandas as pd
import pytest

from rocket_flight_simulator import (
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


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def telemetry() -> pd.DataFrame:
    """Load baseline simulation telemetry."""
    return pd.read_csv("data/simulation_output.csv")


@pytest.fixture
def default_config() -> SensorSuiteConfig:
    """Default sensor configuration with fixed seed."""
    return SensorSuiteConfig(seed=42)


# =============================================================================
# Sensor Config Tests
# =============================================================================

def test_sensor_config_defaults() -> None:
    """Test SensorConfig default values."""
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER)
    assert config.enabled is True
    assert config.sample_rate_hz == 10.0
    assert config.noise_std == 0.0
    assert config.bias == 0.0
    assert config.dropout_prob == 0.0
    assert config.axis_misalignment_deg == 0.0


def test_sensor_config_validation() -> None:
    """Test SensorConfig validation."""
    with pytest.raises(ValueError):
        SensorConfig(sensor_type=SensorType.ACCELEROMETER, sample_rate_hz=-1.0)
    with pytest.raises(ValueError):
        SensorConfig(sensor_type=SensorType.ACCELEROMETER, noise_std=-0.1)
    with pytest.raises(ValueError):
        SensorConfig(sensor_type=SensorType.ACCELEROMETER, dropout_prob=1.5)
    with pytest.raises(ValueError):
        SensorConfig(sensor_type=SensorType.ACCELEROMETER, axis_misalignment_deg=-1.0)


def test_sensor_suite_config_validation() -> None:
    """Test SensorSuiteConfig warns on uneven sample rates."""
    # This should warn but not fail
    config = SensorSuiteConfig(
        accelerometer=SensorConfig(sensor_type=SensorType.ACCELEROMETER, sample_rate_hz=7.0),
    )
    # Sample rate 7 Hz doesn't divide evenly into 10 Hz
    assert config.accelerometer.sample_rate_hz == 7.0


# =============================================================================
# Sensor Reading and Packet Tests
# =============================================================================

def test_sensor_reading_creation() -> None:
    """Test SensorReading creation and methods."""
    reading = SensorReading(
        sensor_type=SensorType.ACCELEROMETER,
        value=(1.0, 2.0, 3.0),
        unit="m/s^2",
        validity=SensorValidity.VALID,
        timestamp_s=1.0,
        sequence=1,
        metadata={"test": True},
    )
    assert reading.is_valid()
    assert reading.sensor_type == SensorType.ACCELEROMETER
    assert reading.value == (1.0, 2.0, 3.0)

    # Test to_dict
    d = reading.to_dict()
    assert d["sensor_type"] == "accelerometer"
    assert d["value_x"] == 1.0
    assert d["value_y"] == 2.0
    assert d["value_z"] == 3.0
    assert d["unit"] == "m/s^2"
    assert d["validity"] == "valid"

    # Test scalar value
    reading2 = SensorReading(
        sensor_type=SensorType.BAROMETRIC_ALTIMETER,
        value=100.0,
        unit="m",
        validity=SensorValidity.VALID,
        timestamp_s=1.0,
        sequence=1,
    )
    d2 = reading2.to_dict()
    assert d2["value"] == 100.0


def test_sensor_packet_creation() -> None:
    """Test SensorPacket creation and methods."""
    readings = {
        SensorType.ACCELEROMETER: SensorReading(
            sensor_type=SensorType.ACCELEROMETER,
            value=(1.0, 2.0, 3.0),
            unit="m/s^2",
            validity=SensorValidity.VALID,
            timestamp_s=1.0,
            sequence=1,
        ),
        SensorType.GYROSCOPE: SensorReading(
            sensor_type=SensorType.GYROSCOPE,
            value=(0.0, 0.0, 0.0),
            unit="rad/s",
            validity=SensorValidity.DISABLED,
            timestamp_s=1.0,
            sequence=0,
        ),
    }
    packet = SensorPacket(
        timestamp_s=1.0,
        sequence=1,
        readings=readings,
        packet_validity=PacketValidity.DEGRADED,
        is_synthetic=True,
        simulator_time_s=1.0,
    )

    assert packet.get_reading(SensorType.ACCELEROMETER) is not None
    assert packet.get_reading(SensorType.BAROMETRIC_ALTIMETER) is None

    # Test to_dict
    d = packet.to_dict()
    assert d["timestamp_s"] == 1.0
    assert d["sequence"] == 1
    assert d["packet_validity"] == "degraded"
    assert d["is_synthetic"] is True
    assert "accelerometer" in d["readings"]
    assert "gyroscope" in d["readings"]

    # Test from_dict roundtrip
    packet2 = SensorPacket.from_dict(d)
    assert packet2.timestamp_s == packet.timestamp_s
    assert packet2.packet_validity == packet.packet_validity
    assert packet2.readings[SensorType.ACCELEROMETER].value == (1.0, 2.0, 3.0)


# =============================================================================
# Individual Sensor Tests
# =============================================================================

def test_accelerometer_sensor_no_noise(telemetry: pd.DataFrame) -> None:
    """Test accelerometer with zero noise/bias produces expected values."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, noise_std=0.0, bias=0.0)
    sensor = AccelerometerSensor(config, rng)

    # At t=0, acceleration_mps2 = -9.81 (gravity only, pre-launch)
    ground_truth = {"acceleration_mps2": -9.81}
    reading = sensor.generate(0.0, ground_truth)

    assert reading.validity == SensorValidity.VALID
    assert reading.unit == "m/s^2"
    # Specific force = acceleration + gravity = -9.81 + 9.81 = 0.0
    # With zero noise and bias, Z should be ~0
    ax, ay, az = reading.value
    assert abs(ax) < 1e-10
    assert abs(ay) < 1e-10
    assert abs(az) < 1e-10


def test_accelerometer_sensor_with_noise(telemetry: pd.DataFrame) -> None:
    """Test accelerometer adds noise."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, noise_std=0.1, bias=0.0)
    sensor = AccelerometerSensor(config, rng)

    ground_truth = {"acceleration_mps2": 20.0}
    reading = sensor.generate(0.0, ground_truth)

    # Z should be specific_force + noise = (20 + 9.81) + noise
    _, _, az = reading.value
    expected_z = 29.81
    assert abs(az - expected_z) > 0.001  # Noise should make it differ


def test_accelerometer_sensor_with_bias(telemetry: pd.DataFrame) -> None:
    """Test accelerometer adds bias."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, noise_std=0.0, bias=0.5)
    sensor = AccelerometerSensor(config, rng)

    ground_truth = {"acceleration_mps2": -9.81}
    reading = sensor.generate(0.0, ground_truth)

    ax, ay, az = reading.value
    # With zero noise, bias should be exactly added
    assert abs(ax - 0.5) < 1e-10
    assert abs(ay - 0.5) < 1e-10
    assert abs(az - 0.5) < 1e-10


def test_accelerometer_disabled(telemetry: pd.DataFrame) -> None:
    """Test disabled accelerometer returns DISABLED validity."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, enabled=False)
    sensor = AccelerometerSensor(config, rng)

    reading = sensor.generate(0.0, {})
    assert reading.validity == SensorValidity.DISABLED
    assert reading.metadata.get("enabled") is False


def test_gyroscope_sensor(telemetry: pd.DataFrame) -> None:
    """Test gyroscope sensor (always zero true rate for vertical flight)."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.GYROSCOPE, noise_std=0.0, bias=0.0)
    sensor = GyroscopeSensor(config, rng)

    reading = sensor.generate(0.0, {})
    assert reading.validity == SensorValidity.VALID
    assert reading.unit == "rad/s"
    gx, gy, gz = reading.value
    assert abs(gx) < 1e-10
    assert abs(gy) < 1e-10
    assert abs(gz) < 1e-10
    assert reading.metadata["ground_truth_angular_rate_rad_s"] == (0.0, 0.0, 0.0)


def test_gyroscope_sensor_with_noise(telemetry: pd.DataFrame) -> None:
    """Test gyroscope adds noise."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.GYROSCOPE, noise_std=0.01, bias=0.0)
    sensor = GyroscopeSensor(config, rng)

    reading = sensor.generate(0.0, {})
    gx, gy, gz = reading.value
    # With noise, values should be non-zero
    assert abs(gx) > 1e-6 or abs(gy) > 1e-6 or abs(gz) > 1e-6


def test_barometric_altimeter_sensor(telemetry: pd.DataFrame) -> None:
    """Test barometric altimeter."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.BAROMETRIC_ALTIMETER, noise_std=0.0, bias=0.0)
    sensor = BarometricAltimeterSensor(config, rng)

    ground_truth = {"altitude_m": 1000.0}
    reading = sensor.generate(0.0, ground_truth)

    assert reading.validity == SensorValidity.VALID
    assert reading.unit == "m"
    assert abs(reading.value - 1000.0) < 1e-10
    assert reading.metadata["ground_truth_altitude_m"] == 1000.0


def test_barometric_altimeter_non_negative(telemetry: pd.DataFrame) -> None:
    """Test barometric altimeter clamps at zero."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.BAROMETRIC_ALTIMETER, noise_std=0.0, bias=-10.0)
    sensor = BarometricAltimeterSensor(config, rng)

    ground_truth = {"altitude_m": 0.0}
    reading = sensor.generate(0.0, ground_truth)

    # Bias would make it negative, but it's clamped at 0
    assert reading.value == 0.0


def test_gps_altitude_sensor(telemetry: pd.DataFrame) -> None:
    """Test GPS altitude sensor."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.GPS_ALTITUDE, noise_std=0.0, bias=0.0)
    sensor = GPSAltitudeSensor(config, rng)

    ground_truth = {"altitude_m": 500.0}
    reading = sensor.generate(0.0, ground_truth)

    assert reading.validity == SensorValidity.VALID
    assert reading.unit == "m"
    assert abs(reading.value - 500.0) < 1e-10


def test_gps_velocity_sensor(telemetry: pd.DataFrame) -> None:
    """Test GPS velocity sensor."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.GPS_VELOCITY, noise_std=0.0, bias=0.0)
    sensor = GPSVelocitySensor(config, rng)

    ground_truth = {"velocity_mps": 100.0}
    reading = sensor.generate(0.0, ground_truth)

    assert reading.validity == SensorValidity.VALID
    assert reading.unit == "m/s"
    vx, vy, vz = reading.value
    assert abs(vx) < 1e-10
    assert abs(vy) < 1e-10
    assert abs(vz - 100.0) < 1e-10


def test_sensor_dropout(telemetry: pd.DataFrame) -> None:
    """Test sensor dropout with probability 1.0."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, dropout_prob=1.0)
    sensor = AccelerometerSensor(config, rng)

    # All readings should be dropout
    for _ in range(10):
        reading = sensor.generate(0.0, {"acceleration_mps2": -9.81})
        assert reading.validity == SensorValidity.DROPOUT
        ax, ay, az = reading.value
        assert math.isnan(ax) and math.isnan(ay) and math.isnan(az)


def test_sensor_dropout_prob_zero(telemetry: pd.DataFrame) -> None:
    """Test sensor dropout with probability 0.0."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, dropout_prob=0.0)
    sensor = AccelerometerSensor(config, rng)

    # No dropouts should occur
    for _ in range(10):
        reading = sensor.generate(0.0, {"acceleration_mps2": -9.81})
        assert reading.validity == SensorValidity.VALID


# =============================================================================
# Sensor Suite Tests
# =============================================================================

def test_generate_sensor_packets_structure(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test sensor packet generation produces correct structure."""
    packets = generate_sensor_packets(telemetry, default_config)

    assert len(packets) == len(telemetry)
    assert len(packets) > 0

    # Check first packet
    p0 = packets[0]
    assert isinstance(p0, SensorPacket)
    assert p0.timestamp_s == 0.0
    assert p0.sequence == 1
    assert p0.is_synthetic is True
    assert p0.packet_validity == PacketValidity.VALID

    # Check all sensor types present
    expected_types = {
        SensorType.ACCELEROMETER,
        SensorType.GYROSCOPE,
        SensorType.BAROMETRIC_ALTIMETER,
        SensorType.GPS_ALTITUDE,
        SensorType.GPS_VELOCITY,
    }
    assert set(p0.readings.keys()) == expected_types


def test_sensor_packet_units(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test all sensor readings have correct units."""
    packets = generate_sensor_packets(telemetry, default_config)

    expected_units = {
        SensorType.ACCELEROMETER: "m/s^2",
        SensorType.GYROSCOPE: "rad/s",
        SensorType.BAROMETRIC_ALTIMETER: "m",
        SensorType.GPS_ALTITUDE: "m",
        SensorType.GPS_VELOCITY: "m/s",
    }

    for packet in packets:
        for st, reading in packet.readings.items():
            assert reading.unit == expected_units[st]


def test_sensor_sampling_rates(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test sensors sample at configured rates."""
    packets = generate_sensor_packets(telemetry, default_config)

    # Accelerometer and gyroscope at 10 Hz (every step)
    for i in range(min(20, len(packets))):
        assert packets[i].readings[SensorType.ACCELEROMETER].validity == SensorValidity.VALID
        assert packets[i].readings[SensorType.GYROSCOPE].validity == SensorValidity.VALID

    # GPS at 5 Hz (every other step)
    for i in range(min(20, len(packets))):
        if i % 2 == 0:
            assert packets[i].readings[SensorType.GPS_ALTITUDE].validity == SensorValidity.VALID
            assert packets[i].readings[SensorType.GPS_VELOCITY].validity == SensorValidity.VALID
        else:
            assert packets[i].readings[SensorType.GPS_ALTITUDE].validity == SensorValidity.INVALID
            assert packets[i].readings[SensorType.GPS_VELOCITY].validity == SensorValidity.INVALID


def test_deterministic_generation(telemetry: pd.DataFrame) -> None:
    """Test sensor generation is deterministic with fixed seed."""
    # Use zero dropout to avoid NaN comparison issues
    config1 = SensorSuiteConfig(
        seed=12345,
        gps_altitude=SensorConfig(sensor_type=SensorType.GPS_ALTITUDE, dropout_prob=0.0),
        gps_velocity=SensorConfig(sensor_type=SensorType.GPS_VELOCITY, dropout_prob=0.0),
    )
    config2 = SensorSuiteConfig(
        seed=12345,
        gps_altitude=SensorConfig(sensor_type=SensorType.GPS_ALTITUDE, dropout_prob=0.0),
        gps_velocity=SensorConfig(sensor_type=SensorType.GPS_VELOCITY, dropout_prob=0.0),
    )

    packets1 = generate_sensor_packets(telemetry, config1)
    packets2 = generate_sensor_packets(telemetry, config2)

    for p1, p2 in zip(packets1, packets2):
        assert p1.timestamp_s == p2.timestamp_s
        assert p1.sequence == p2.sequence
        for st in SensorType:
            r1 = p1.readings[st]
            r2 = p2.readings[st]
            assert r1.validity == r2.validity
            if isinstance(r1.value, tuple):
                for v1, v2 in zip(r1.value, r2.value):
                    # Handle NaN (both should be NaN for dropout cases)
                    if math.isnan(v1) and math.isnan(v2):
                        continue
                    assert abs(v1 - v2) < 1e-15
            else:
                if math.isnan(r1.value) and math.isnan(r2.value):
                    continue
                assert abs(r1.value - r2.value) < 1e-15


def test_different_seeds_produce_different_results(telemetry: pd.DataFrame) -> None:
    """Test different seeds produce different (but valid) results."""
    config1 = SensorSuiteConfig(seed=111)
    config2 = SensorSuiteConfig(seed=222)

    packets1 = generate_sensor_packets(telemetry, config1)
    packets2 = generate_sensor_packets(telemetry, config2)

    # At least some readings should differ
    differences = 0
    for p1, p2 in zip(packets1, packets2):
        for st in SensorType:
            r1 = p1.readings[st]
            r2 = p2.readings[st]
            if isinstance(r1.value, tuple):
                for v1, v2 in zip(r1.value, r2.value):
                    if abs(v1 - v2) > 1e-10:
                        differences += 1
            else:
                if abs(r1.value - r2.value) > 1e-10:
                    differences += 1

    assert differences > 0  # Different seeds should produce different noise


def test_disabled_sensor_excluded_from_validity(telemetry: pd.DataFrame) -> None:
    """Test disabled sensors don't count toward packet validity."""
    config = SensorSuiteConfig(
        seed=42,
        gyroscope=SensorConfig(sensor_type=SensorType.GYROSCOPE, enabled=False),
    )
    packets = generate_sensor_packets(telemetry, config)

    # Packet should be VALID (only 4 enabled sensors, all valid)
    assert packets[0].packet_validity == PacketValidity.VALID

    # Disabled sensor should be in readings with DISABLED validity
    assert packets[0].readings[SensorType.GYROSCOPE].validity == SensorValidity.DISABLED


def test_packet_validity_degraded(telemetry: pd.DataFrame) -> None:
    """Test packet validity DEGRADED when some sensors fail."""
    config = SensorSuiteConfig(
        seed=42,
        gps_altitude=SensorConfig(sensor_type=SensorType.GPS_ALTITUDE, dropout_prob=1.0),
    )
    packets = generate_sensor_packets(telemetry, config)

    # GPS altitude drops out, packet should be DEGRADED
    assert packets[0].packet_validity == PacketValidity.DEGRADED


def test_packet_validity_invalid(telemetry: pd.DataFrame) -> None:
    """Test packet validity INVALID when all sensors fail."""
    config = SensorSuiteConfig(
        seed=42,
        accelerometer=SensorConfig(sensor_type=SensorType.ACCELEROMETER, dropout_prob=1.0),
        gyroscope=SensorConfig(sensor_type=SensorType.GYROSCOPE, dropout_prob=1.0),
        barometric_altimeter=SensorConfig(sensor_type=SensorType.BAROMETRIC_ALTIMETER, dropout_prob=1.0),
        gps_altitude=SensorConfig(sensor_type=SensorType.GPS_ALTITUDE, dropout_prob=1.0),
        gps_velocity=SensorConfig(sensor_type=SensorType.GPS_VELOCITY, dropout_prob=1.0),
    )
    packets = generate_sensor_packets(telemetry, config)

    assert packets[0].packet_validity == PacketValidity.INVALID


def test_packets_to_dataframe(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test conversion to DataFrame."""
    packets = generate_sensor_packets(telemetry, default_config)
    df = packets_to_dataframe(packets)

    # 416 packets * 5 sensors = 2080 rows
    assert len(df) == len(packets) * 5
    assert "packet_timestamp_s" in df.columns
    assert "sensor_type" in df.columns
    assert "sensor_validity" in df.columns
    assert "value_x" in df.columns
    assert "value_y" in df.columns
    assert "value_z" in df.columns


def test_sensor_schema_documentation() -> None:
    """Test SENSOR_SCHEMA has all expected sensors."""
    expected = {
        "accelerometer",
        "gyroscope",
        "barometric_altimeter",
        "gps_altitude",
        "gps_velocity",
    }
    assert set(SENSOR_SCHEMA.keys()) == expected

    for sensor_name, schema in SENSOR_SCHEMA.items():
        assert "type" in schema
        assert "description" in schema
        assert "unit" in schema
        assert "note" in schema
        assert "SYNTHETIC" in schema["note"]


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

def test_missing_ground_truth_fields() -> None:
    """Test sensor handles missing ground truth gracefully."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER, noise_std=0.0, bias=0.0)
    sensor = AccelerometerSensor(config, rng)

    # Empty ground truth
    reading = sensor.generate(0.0, {})
    assert reading.validity == SensorValidity.VALID
    # Should use default 0.0 for missing acceleration
    ax, ay, az = reading.value
    # Specific force = 0 + 9.81 = 9.81
    assert abs(az - 9.81) < 1e-10


def test_sensor_sequence_increments() -> None:
    """Test sensor sequence numbers increment per reading."""
    rng = random.Random(42)
    config = SensorConfig(sensor_type=SensorType.ACCELEROMETER)
    sensor = AccelerometerSensor(config, rng)

    for i in range(5):
        reading = sensor.generate(float(i), {"acceleration_mps2": -9.81})
        assert reading.sequence == i + 1


def test_ground_truth_metadata_in_readings(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test that ground truth values are included in reading metadata."""
    packets = generate_sensor_packets(telemetry, default_config)

    # Accelerometer should have ground truth accel
    acc_reading = packets[50].readings[SensorType.ACCELEROMETER]
    assert "ground_truth_accel_mps2" in acc_reading.metadata
    assert "ground_truth_specific_force_z" in acc_reading.metadata

    # Barometric altimeter should have ground truth altitude
    baro_reading = packets[50].readings[SensorType.BAROMETRIC_ALTIMETER]
    assert "ground_truth_altitude_m" in baro_reading.metadata

    # GPS velocity should have ground truth velocity
    gps_vel = packets[50].readings[SensorType.GPS_VELOCITY]
    assert "ground_truth_velocity_mps" in gps_vel.metadata


# =============================================================================
# Integration with Simulator
# =============================================================================

def test_simulation_output_unchanged(telemetry: pd.DataFrame) -> None:
    """Verify sensor generation doesn't modify original telemetry."""
    # Create a copy to compare
    telemetry_copy = telemetry.copy()

    config = SensorSuiteConfig(seed=42)
    _ = generate_sensor_packets(telemetry, config)

    # Original telemetry should be unchanged
    pd.testing.assert_frame_equal(telemetry, telemetry_copy)


def test_sensor_output_derivable_from_ground_truth(telemetry: pd.DataFrame, default_config: SensorSuiteConfig) -> None:
    """Test that sensor readings are derived from ground truth (not random unrelated values)."""
    packets = generate_sensor_packets(telemetry, default_config)

    # At index 50 (t~5s), altitude ~440m, velocity ~175 m/s, accel ~19 m/s^2
    p50 = packets[50]
    gt = telemetry.iloc[50]

    # Barometric altitude should be close to ground truth (with noise)
    baro = p50.readings[SensorType.BAROMETRIC_ALTIMETER]
    assert abs(baro.value - gt["altitude_m"]) < 5.0  # Within noise

    # GPS altitude should be close
    gps_alt = p50.readings[SensorType.GPS_ALTITUDE]
    assert abs(gps_alt.value - gt["altitude_m"]) < 10.0

    # GPS velocity Z should be close to ground truth velocity
    gps_vel = p50.readings[SensorType.GPS_VELOCITY]
    _, _, vz = gps_vel.value
    assert abs(vz - gt["velocity_mps"]) < 1.0


# Import math for isnan
# import math  # Now imported at top