"""Command-line entry point for the rocket flight simulator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from mission import analyze_mission
from report_generator import generate_mission_report
from rocket import Rocket
from simulator import RocketSimulator
from visualization import generate_plots


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"


def load_rocket_parameters(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def build_rocket(parameters: dict[str, Any]) -> Rocket:
    return Rocket(
        dry_mass=float(parameters["dry_mass"]),
        fuel_mass=float(parameters["fuel_mass"]),
        thrust=float(parameters["thrust"]),
        burn_time=float(parameters["burn_time"]),
        drag_coefficient=float(parameters["drag_coefficient"]),
        cross_sectional_area=float(parameters["cross_sectional_area"]),
    )


def save_mission_summary(summary: dict[str, Any], file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}: {value}" for key, value in summary.items()]
    file_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parameters = load_rocket_parameters(DATA_DIR / "rocket_parameters.json")
    rocket = build_rocket(parameters)

    simulator = RocketSimulator(rocket)
    result = simulator.run()
    telemetry = result.telemetry

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    telemetry_path = DATA_DIR / "simulation_output.csv"
    telemetry.to_csv(telemetry_path, index=False)

    mission_summary = analyze_mission(telemetry)
    save_mission_summary(mission_summary, REPORTS_DIR / "mission_summary.txt")

    plot_paths = generate_plots(telemetry, str(SCREENSHOTS_DIR))
    generate_mission_report(
        output_path=str(REPORTS_DIR / "mission_report.pdf"),
        mission_summary=mission_summary,
        rocket_spec=parameters,
        plot_paths=plot_paths,
    )

    print("Mission Summary")
    for key, value in mission_summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print(f"Telemetry saved to: {telemetry_path}")
    print(f"Report saved to: {REPORTS_DIR / 'mission_report.pdf'}")


if __name__ == "__main__":
    main()
