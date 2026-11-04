"""Mission analysis helpers for simulation results."""

from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_mission(telemetry: pd.DataFrame) -> dict[str, Any]:
    """Calculate headline mission performance metrics from telemetry."""

    if telemetry.empty:
        return {
            "maximum_altitude_m": 0.0,
            "maximum_velocity_mps": 0.0,
            "maximum_acceleration_mps2": 0.0,
            "burnout_time_s": 0.0,
            "apogee_time_s": 0.0,
            "total_flight_duration_s": 0.0,
            "landing_velocity_mps": 0.0,
            "flight_duration_s": 0.0,
        }

    apogee_index = telemetry["altitude_m"].idxmax()
    powered_samples = pd.DataFrame()
    if "thrust_n" in telemetry:
        powered_samples = telemetry[telemetry["thrust_n"] > 0.0]
    burnout_time_s = 0.0
    if not powered_samples.empty:
        burnout_time_s = float(powered_samples["time_s"].iloc[-1])

    flight_duration_s = float(telemetry["time_s"].iloc[-1])
    return {
        "maximum_altitude_m": float(telemetry["altitude_m"].max()),
        "maximum_velocity_mps": float(telemetry["velocity_mps"].abs().max()),
        "maximum_acceleration_mps2": float(telemetry["acceleration_mps2"].abs().max()),
        "burnout_time_s": burnout_time_s,
        "apogee_time_s": float(telemetry.loc[apogee_index, "time_s"]),
        "total_flight_duration_s": flight_duration_s,
        "landing_velocity_mps": float(telemetry["velocity_mps"].iloc[-1]),
        "flight_duration_s": flight_duration_s,
    }


def build_phase_timeline(telemetry: pd.DataFrame) -> list[dict[str, Any]]:
    """Return first and last time stamps for each recorded flight phase."""

    if telemetry.empty or "flight_phase" not in telemetry:
        return []

    timeline: list[dict[str, Any]] = []
    for phase, samples in telemetry.groupby("flight_phase", sort=False):
        start_time_s = float(samples["time_s"].iloc[0])
        end_time_s = float(samples["time_s"].iloc[-1])
        timeline.append(
            {
                "flight_phase": phase,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
                "duration_s": end_time_s - start_time_s,
            }
        )
    return timeline
