"""Mission analysis helpers for simulation results."""

from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_mission(telemetry: pd.DataFrame) -> dict[str, Any]:
    if telemetry.empty:
        return {
            "maximum_altitude_m": 0.0,
            "maximum_velocity_mps": 0.0,
            "maximum_acceleration_mps2": 0.0,
            "flight_duration_s": 0.0,
            "apogee_time_s": 0.0,
        }

    apogee_index = telemetry["altitude_m"].idxmax()
    return {
        "maximum_altitude_m": float(telemetry["altitude_m"].max()),
        "maximum_velocity_mps": float(telemetry["velocity_mps"].max()),
        "maximum_acceleration_mps2": float(telemetry["acceleration_mps2"].max()),
        "flight_duration_s": float(telemetry["time_s"].iloc[-1]),
        "apogee_time_s": float(telemetry.loc[apogee_index, "time_s"]),
    }
