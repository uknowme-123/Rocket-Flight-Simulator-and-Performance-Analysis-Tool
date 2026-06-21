import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rocket import Rocket
from simulator import RocketSimulator


def test_simulation_execution() -> None:
    rocket = Rocket(3.0, 2.0, 300.0, 8.0, 0.45, 0.02)
    result = RocketSimulator(rocket).run()
    assert not result.telemetry.empty
    assert {
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
    }.issubset(result.telemetry.columns)


def test_simulation_records_new_physics_outputs() -> None:
    rocket = Rocket(3.0, 2.0, 300.0, 8.0, 0.45, 0.02)
    result = RocketSimulator(rocket).run()
    telemetry = result.telemetry

    assert telemetry["mass_kg"].iloc[-1] < telemetry["mass_kg"].iloc[0]
    assert telemetry["thrust_n"].max() > 0.0
    assert telemetry["drag_force_n"].max() >= 0.0
    assert "APOGEE" in set(telemetry["flight_phase"])
