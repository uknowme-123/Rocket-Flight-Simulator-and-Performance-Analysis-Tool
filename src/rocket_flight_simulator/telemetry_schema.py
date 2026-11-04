"""Telemetry schema definitions with units, types, and metadata.

This module provides a centralized definition of all telemetry fields including:
- Field names and data types
- Physical units
- Descriptions
- Sampling information
- Validity requirements
- Required/optional field definitions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class TelemetryFieldType(str, Enum):
    """Supported telemetry field data types."""

    FLOAT = "float"
    INT = "int"
    STRING = "string"
    ENUM = "enum"
    BOOL = "bool"


class TelemetryValidity(str, Enum):
    """Validity requirements for telemetry fields."""

    REQUIRED = "required"          # Must always be present
    CONDITIONAL = "conditional"    # Present when applicable (e.g., thrust during burn)
    OPTIONAL = "optional"          # May be absent


@dataclass(frozen=True)
class TelemetryField:
    """Definition of a single telemetry field."""

    name: str
    dtype: TelemetryFieldType
    unit: str
    description: str
    sample_rate_hz: float
    validity: TelemetryValidity = TelemetryValidity.REQUIRED
    enum_values: tuple[str, ...] | None = None
    min_value: float | None = None
    max_value: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.dtype == TelemetryFieldType.ENUM and not self.enum_values:
            raise ValueError(f"Enum field {self.name} must have enum_values")


# Flight phase enumeration values
FLIGHT_PHASES: tuple[str, ...] = (
    "PRE-LAUNCH",
    "LIFTOFF",
    "POWERED_ASCENT",
    "COASTING",
    "APOGEE",
    "DESCENT",
    "LANDING",
)


# Core telemetry schema - ordered by typical acquisition sequence
TELEMETRY_SCHEMA: tuple[TelemetryField, ...] = (
    TelemetryField(
        name="time_s",
        dtype=TelemetryFieldType.FLOAT,
        unit="s",
        description="Mission elapsed time since simulation start / T-0",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"is_timestamp": True, "reference": "T-0"},
    ),
    TelemetryField(
        name="altitude_m",
        dtype=TelemetryFieldType.FLOAT,
        unit="m",
        description="Vehicle altitude above launch site (geometric)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"sensor": "barometer/GPS", "frame": "ENU launch site"},
    ),
    TelemetryField(
        name="velocity_mps",
        dtype=TelemetryFieldType.FLOAT,
        unit="m/s",
        description="Vertical velocity (positive = upward)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        metadata={"sensor": "barometer/GPS/IMU", "frame": "ENU launch site", "sign_convention": "up_positive"},
    ),
    TelemetryField(
        name="acceleration_mps2",
        dtype=TelemetryFieldType.FLOAT,
        unit="m/s^2",
        description="Total acceleration including gravity (positive = upward)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        metadata={"sensor": "IMU accelerometer", "frame": "body/ENU", "includes_gravity": True},
    ),
    TelemetryField(
        name="mass_kg",
        dtype=TelemetryFieldType.FLOAT,
        unit="kg",
        description="Total vehicle mass (dry + remaining propellant)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"source": "mass_bookkeeping", "updates_on": "mass_flow"},
    ),
    TelemetryField(
        name="fuel_remaining_kg",
        dtype=TelemetryFieldType.FLOAT,
        unit="kg",
        description="Remaining propellant mass",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"source": "mass_bookkeeping", "depletes_during": "burn"},
    ),
    TelemetryField(
        name="thrust_n",
        dtype=TelemetryFieldType.FLOAT,
        unit="N",
        description="Motor thrust force (zero when not burning)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.CONDITIONAL,
        min_value=0.0,
        metadata={"source": "thrust_curve", "active_when": "burning", "curve": "5-phase_solid_motor"},
    ),
    TelemetryField(
        name="drag_force_n",
        dtype=TelemetryFieldType.FLOAT,
        unit="N",
        description="Aerodynamic drag magnitude (always >= 0)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"source": "aero_model", "direction": "opposes_velocity"},
    ),
    TelemetryField(
        name="flight_phase",
        dtype=TelemetryFieldType.ENUM,
        unit="enum",
        description="Current mission phase from state machine",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        enum_values=FLIGHT_PHASES,
        metadata={"source": "phase_detection", "type": "state_machine"},
    ),
    TelemetryField(
        name="air_density_kg_m3",
        dtype=TelemetryFieldType.FLOAT,
        unit="kg/m^3",
        description="Atmospheric density at current altitude (ISA model)",
        sample_rate_hz=10.0,
        validity=TelemetryValidity.REQUIRED,
        min_value=0.0,
        metadata={"model": "ISA_troposphere_stratosphere", "source": "atmosphere_model"},
    ),
)


# Schema indexed by field name for fast lookup
TELEMETRY_SCHEMA_BY_NAME: dict[str, TelemetryField] = {
    field.name: field for field in TELEMETRY_SCHEMA
}

# Required fields (for validation)
REQUIRED_FIELDS: frozenset[str] = frozenset(
    f.name for f in TELEMETRY_SCHEMA if f.validity == TelemetryValidity.REQUIRED
)

# Conditional fields
CONDITIONAL_FIELDS: frozenset[str] = frozenset(
    f.name for f in TELEMETRY_SCHEMA if f.validity == TelemetryValidity.CONDITIONAL
)

# All field names
ALL_FIELDS: frozenset[str] = frozenset(f.name for f in TELEMETRY_SCHEMA)


def validate_telemetry_dataframe(df: "pd.DataFrame") -> list[str]:
    """Validate a telemetry DataFrame against the schema.

    Returns a list of validation error messages (empty if valid).
    """
    errors: list[str] = []

    # Check required fields present
    missing = REQUIRED_FIELDS - set(df.columns)
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    # Check no unknown fields
    unknown = set(df.columns) - ALL_FIELDS
    if unknown:
        errors.append(f"Unknown fields: {sorted(unknown)}")

    # Check enum values
    if "flight_phase" in df.columns:
        invalid_phases = set(df["flight_phase"].unique()) - set(FLIGHT_PHASES)
        if invalid_phases:
            errors.append(f"Invalid flight phases: {sorted(invalid_phases)}")

    # Check numeric bounds
    for field_def in TELEMETRY_SCHEMA:
        if field_def.name not in df.columns:
            continue
        if field_def.dtype in (TelemetryFieldType.FLOAT, TelemetryFieldType.INT):
            series = df[field_def.name]
            if field_def.min_value is not None:
                below_min = series[series < field_def.min_value]
                if not below_min.empty:
                    errors.append(
                        f"{field_def.name}: {len(below_min)} values below minimum {field_def.min_value} {field_def.unit}"
                    )
            if field_def.max_value is not None:
                above_max = series[series > field_def.max_value]
                if not above_max.empty:
                    errors.append(
                        f"{field_def.name}: {len(above_max)} values above maximum {field_def.max_value} {field_def.unit}"
                    )

    return errors


def get_schema_json() -> dict[str, Any]:
    """Return the telemetry schema as a JSON-serializable dictionary."""
    return {
        "version": "1.0",
        "sample_rate_hz": 10.0,
        "fields": [
            {
                "name": f.name,
                "type": f.dtype.value,
                "unit": f.unit,
                "description": f.description,
                "sample_rate_hz": f.sample_rate_hz,
                "validity": f.validity.value,
                "enum_values": list(f.enum_values) if f.enum_values else None,
                "min_value": f.min_value,
                "max_value": f.max_value,
                "metadata": f.metadata,
            }
            for f in TELEMETRY_SCHEMA
        ],
    }


def get_field_info(field_name: str) -> TelemetryField | None:
    """Get field definition by name."""
    return TELEMETRY_SCHEMA_BY_NAME.get(field_name)


def get_fields_by_validity(validity: TelemetryValidity) -> list[TelemetryField]:
    """Get all fields with a specific validity requirement."""
    return [f for f in TELEMETRY_SCHEMA if f.validity == validity]