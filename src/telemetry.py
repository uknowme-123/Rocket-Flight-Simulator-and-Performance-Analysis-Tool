"""Telemetry logging and CSV export."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class TelemetryLogger:
    """Collect and persist flight telemetry samples."""

    samples: list[dict[str, float]] = field(default_factory=list)

    def record(self, time_s: float, altitude_m: float, velocity_mps: float, acceleration_mps2: float, fuel_remaining_kg: float) -> None:
        self.samples.append(
            {
                "time_s": time_s,
                "altitude_m": altitude_m,
                "velocity_mps": velocity_mps,
                "acceleration_mps2": acceleration_mps2,
                "fuel_remaining_kg": fuel_remaining_kg,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.samples)

    def save_csv(self, file_path: str) -> None:
        dataframe = self.to_dataframe()
        dataframe.to_csv(file_path, index=False)
