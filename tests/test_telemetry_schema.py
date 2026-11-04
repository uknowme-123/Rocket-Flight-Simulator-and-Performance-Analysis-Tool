"""Tests for telemetry schema validation."""

from __future__ import annotations

import pandas as pd
import pytest

from rocket_flight_simulator import (
    TELEMETRY_SCHEMA,
    FLIGHT_PHASES,
    validate_telemetry_dataframe,
    get_schema_json,
    get_field_info,
    REQUIRED_FIELDS,
    CONDITIONAL_FIELDS,
    ALL_FIELDS,
    TelemetryFieldType,
    TelemetryValidity,
)


def test_schema_structure() -> None:
    """Verify schema has expected structure."""
    assert len(TELEMETRY_SCHEMA) == 10

    field_names = [f.name for f in TELEMETRY_SCHEMA]
    expected = [
        "time_s",
        "altitude_m",
        "velocity_mps",
        "acceleration_mps2",
        "mass_kg",
        "fuel_remaining_kg",
        "thrust_n",
        "drag_force_n",
        "flight_phase",
        "air_density_kg_m3",
    ]
    assert field_names == expected


def test_required_fields() -> None:
    """Verify required fields classification."""
    required = {f.name for f in TELEMETRY_SCHEMA if f.validity == TelemetryValidity.REQUIRED}
    assert "time_s" in required
    assert "altitude_m" in required
    assert "thrust_n" not in required  # conditional

    assert REQUIRED_FIELDS == required


def test_conditional_fields() -> None:
    """Verify conditional fields classification."""
    conditional = {f.name for f in TELEMETRY_SCHEMA if f.validity == TelemetryValidity.CONDITIONAL}
    assert "thrust_n" in conditional
    assert CONDITIONAL_FIELDS == conditional


def test_all_fields() -> None:
    """Verify all fields set."""
    assert len(ALL_FIELDS) == 10


def test_flight_phases_enum() -> None:
    """Verify flight phase enum values."""
    expected = (
        "PRE-LAUNCH",
        "LIFTOFF",
        "POWERED_ASCENT",
        "COASTING",
        "APOGEE",
        "DESCENT",
        "LANDING",
    )
    assert FLIGHT_PHASES == expected

    phase_field = get_field_info("flight_phase")
    assert phase_field is not None
    assert phase_field.dtype == TelemetryFieldType.ENUM
    assert phase_field.enum_values == FLIGHT_PHASES


def test_field_metadata() -> None:
    """Verify field metadata is present."""
    time_field = get_field_info("time_s")
    assert time_field is not None
    assert time_field.metadata.get("is_timestamp") is True
    assert time_field.metadata.get("reference") == "T-0"

    altitude_field = get_field_info("altitude_m")
    assert altitude_field is not None
    assert altitude_field.metadata.get("sensor") == "barometer/GPS"


def test_schema_json() -> None:
    """Verify JSON schema generation."""
    schema = get_schema_json()
    assert schema["version"] == "1.0"
    assert schema["sample_rate_hz"] == 10.0
    assert len(schema["fields"]) == 10

    # Check field structure
    for field_def in schema["fields"]:
        assert "name" in field_def
        assert "type" in field_def
        assert "unit" in field_def
        assert "description" in field_def
        assert "validity" in field_def


def test_validate_valid_telemetry() -> None:
    """Test validation passes for valid simulation output."""
    df = pd.read_csv("data/simulation_output.csv")
    errors = validate_telemetry_dataframe(df)
    assert errors == []


def test_validate_missing_required_field() -> None:
    """Test validation catches missing required field."""
    df = pd.read_csv("data/simulation_output.csv").drop(columns=["altitude_m"])
    errors = validate_telemetry_dataframe(df)
    assert any("Missing required fields" in e for e in errors)
    assert "altitude_m" in str(errors)


def test_validate_unknown_field() -> None:
    """Test validation catches unknown field."""
    df = pd.read_csv("data/simulation_output.csv").copy()
    df["unknown_field"] = 1.0
    errors = validate_telemetry_dataframe(df)
    assert any("Unknown fields" in e for e in errors)
    assert "unknown_field" in str(errors)


def test_validate_invalid_flight_phase() -> None:
    """Test validation catches invalid flight phase."""
    df = pd.read_csv("data/simulation_output.csv").copy()
    df.loc[0, "flight_phase"] = "INVALID_PHASE"
    errors = validate_telemetry_dataframe(df)
    assert any("Invalid flight phases" in e for e in errors)
    assert "INVALID_PHASE" in str(errors)


def test_validate_bounds() -> None:
    """Test validation checks min/max bounds."""
    df = pd.read_csv("data/simulation_output.csv").copy()
    df.loc[0, "mass_kg"] = -1.0  # Below minimum
    errors = validate_telemetry_dataframe(df)
    assert any("below minimum" in e for e in errors)
    assert "mass_kg" in str(errors)