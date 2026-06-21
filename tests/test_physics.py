import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from physics import calculate_acceleration, calculate_drag, calculate_gravity, calculate_net_force


def test_gravity_calculation() -> None:
    assert calculate_gravity(10.0) == 98.10000000000001


def test_drag_calculation() -> None:
    drag = calculate_drag(10.0, 0.45, 0.02)
    assert round(drag, 4) == 0.5512


def test_net_force_calculation() -> None:
    net_force = calculate_net_force(300.0, 10.0, 98.1, 12.0)
    assert net_force < 202.0


def test_acceleration_calculation() -> None:
    assert calculate_acceleration(100.0, 5.0) == 20.0
