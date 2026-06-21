"""Telemetry logging and CSV export."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class TelemetryLogger:
    """Collect and persist flight telemetry samples."""

    samples: list[dict[str, float | str]] = field(default_factory=list)

    def record(
        self,
        time_s: float,
        altitude_m: float,
        velocity_mps: float,
        acceleration_mps2: float,
        mass_kg: float,
        fuel_remaining_kg: float,
        thrust_n: float,
        drag_force_n: float,
        flight_phase: str,
        air_density_kg_m3: float,
    ) -> None:
        """Append one telemetry sample to the mission log."""

        self.samples.append(
            {
                "time_s": time_s,
                "altitude_m": altitude_m,
                "velocity_mps": velocity_mps,
                "acceleration_mps2": acceleration_mps2,
                "mass_kg": mass_kg,
                "fuel_remaining_kg": fuel_remaining_kg,
                "thrust_n": thrust_n,
                "drag_force_n": drag_force_n,
                "flight_phase": flight_phase,
                "air_density_kg_m3": air_density_kg_m3,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.samples)

    def save_csv(self, file_path: str) -> None:
        dataframe = self.to_dataframe()
        dataframe.to_csv(file_path, index=False)
