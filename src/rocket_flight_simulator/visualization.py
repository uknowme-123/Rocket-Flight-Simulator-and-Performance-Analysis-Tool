"""Matplotlib engineering plots for rocket telemetry."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _save_plot(x, y, title: str, x_label: str, y_label: str, output_path: Path) -> None:
    """Save a single line plot with consistent engineering styling."""

    plt.figure(figsize=(9, 5))
    plt.plot(x, y, linewidth=2.0)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def generate_plots(telemetry: pd.DataFrame, output_dir: str) -> dict[str, str]:
    """Generate all mission performance plots and return their file paths."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    plots = {
        "altitude_plot": output_path / "altitude_plot.png",
        "velocity_plot": output_path / "velocity_plot.png",
        "acceleration_plot": output_path / "acceleration_plot.png",
        "mass_plot": output_path / "mass_plot.png",
        "thrust_plot": output_path / "thrust_plot.png",
    }

    _save_plot(
        telemetry["time_s"],
        telemetry["altitude_m"],
        "Altitude vs Time",
        "Time (s)",
        "Altitude (m)",
        plots["altitude_plot"],
    )
    _save_plot(
        telemetry["time_s"],
        telemetry["velocity_mps"],
        "Velocity vs Time",
        "Time (s)",
        "Velocity (m/s)",
        plots["velocity_plot"],
    )
    _save_plot(
        telemetry["time_s"],
        telemetry["acceleration_mps2"],
        "Acceleration vs Time",
        "Time (s)",
        "Acceleration (m/s^2)",
        plots["acceleration_plot"],
    )
    _save_plot(
        telemetry["time_s"],
        telemetry["mass_kg"],
        "Mass vs Time",
        "Time (s)",
        "Mass (kg)",
        plots["mass_plot"],
    )
    _save_plot(
        telemetry["time_s"],
        telemetry["thrust_n"],
        "Thrust vs Time",
        "Time (s)",
        "Thrust (N)",
        plots["thrust_plot"],
    )

    return {name: str(path) for name, path in plots.items()}
