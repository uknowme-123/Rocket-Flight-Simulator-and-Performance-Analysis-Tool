"""Tests for rocket mass bookkeeping."""

from __future__ import annotations

from rocket_flight_simulator import Rocket


def test_rocket_mass_updates() -> None:
    rocket = Rocket(3.0, 2.0, 300.0, 8.0, 0.45, 0.02)
    assert rocket.get_total_mass() == 5.0
    consumed = rocket.consume_fuel(0.5)
    assert consumed == 0.5
    assert rocket.get_remaining_fuel() == 1.5
    assert rocket.get_current_mass() == 4.5