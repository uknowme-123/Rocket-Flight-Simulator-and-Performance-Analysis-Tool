"""Launch vehicle library utilities for mission configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

from .config import DEFAULT_PROPELLANT_FRACTION


class RocketRecord(TypedDict):
    """Structured schema for one launch vehicle entry."""

    country: str
    organization: str
    height_m: float
    diameter_m: float
    stages: int
    liftoff_mass_kg: float
    payload_leo_kg: float
    thrust_kn: float
    burn_time_s: float
    drag_coefficient: float
    cross_section_area_m2: float
    description: str


ROCKET_LIBRARY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rocket_library.json"


@lru_cache(maxsize=1)
def load_rocket_library() -> dict[str, RocketRecord]:
    """Load launch vehicle records from the JSON library file.

    Returns an empty dictionary if the file cannot be read or parsed.
    """

    try:
        with ROCKET_LIBRARY_PATH.open("r", encoding="utf-8") as file_handle:
            raw_data = json.load(file_handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    if not isinstance(raw_data, dict):
        return {}

    library: dict[str, RocketRecord] = {}
    for name, values in raw_data.items():
        if not isinstance(name, str) or not isinstance(values, dict):
            continue
        try:
            library[name] = RocketRecord(
                country=str(values["country"]),
                organization=str(values["organization"]),
                height_m=float(values["height_m"]),
                diameter_m=float(values["diameter_m"]),
                stages=int(values["stages"]),
                liftoff_mass_kg=float(values["liftoff_mass_kg"]),
                payload_leo_kg=float(values["payload_leo_kg"]),
                thrust_kn=float(values["thrust_kn"]),
                burn_time_s=float(values["burn_time_s"]),
                drag_coefficient=float(values["drag_coefficient"]),
                cross_section_area_m2=float(values["cross_section_area_m2"]),
                description=str(values["description"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return library


def get_rocket_names() -> list[str]:
    """Return sorted launch vehicle names available in the library."""

    return sorted(load_rocket_library().keys())


def get_rocket_by_name(name: str) -> RocketRecord | None:
    """Return one launch vehicle record by name, if found."""

    vehicle = load_rocket_library().get(name)
    if vehicle is None:
        return None
    return RocketRecord(**vehicle)


def return_vehicle_summary(name: str) -> str:
    """Return a compact one-line summary for the selected launch vehicle."""

    vehicle = get_rocket_by_name(name)
    if vehicle is None:
        return f"No launch vehicle found for '{name}'."

    return (
        f"{name} | {vehicle['country']} | {vehicle['organization']} | "
        f"Height {vehicle['height_m']:.1f} m | Payload LEO {vehicle['payload_leo_kg']:.0f} kg"
    )


def map_vehicle_to_simulator_parameters(vehicle: RocketRecord) -> dict[str, float]:
    """Convert library fields into simulator input parameters.

    The simulator requires dry/fuel mass fields. This mapping uses a fixed
    propellant fraction approximation for educational scenarios.
    """

    liftoff_mass = max(float(vehicle["liftoff_mass_kg"]), 1.0)
    propellant_fraction = DEFAULT_PROPELLANT_FRACTION
    fuel_mass = liftoff_mass * propellant_fraction
    dry_mass = liftoff_mass - fuel_mass

    return {
        "dry_mass": dry_mass,
        "fuel_mass": fuel_mass,
        "thrust": float(vehicle["thrust_kn"]) * 1000.0,
        "burn_time": float(vehicle["burn_time_s"]),
        "drag_coefficient": float(vehicle["drag_coefficient"]),
        "cross_sectional_area": float(vehicle["cross_section_area_m2"]),
    }


def build_comparison_rows() -> list[dict[str, Any]]:
    """Return sortable rows for the dashboard rocket comparison table."""

    rows: list[dict[str, Any]] = []
    for name in get_rocket_names():
        vehicle = get_rocket_by_name(name)
        if not vehicle:
            continue
        rows.append(
            {
                "Rocket": name,
                "Country": vehicle["country"],
                "Height": vehicle["height_m"],
                "Stages": vehicle["stages"],
                "Mass": vehicle["liftoff_mass_kg"],
                "Payload": vehicle["payload_leo_kg"],
                "Thrust": vehicle["thrust_kn"],
            }
        )
    return rows
