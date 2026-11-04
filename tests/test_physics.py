"""Tests for physics and atmosphere modules."""

from __future__ import annotations

import pytest

from rocket_flight_simulator import (
    get_air_density,
    calculate_acceleration,
    calculate_drag,
    calculate_gravity,
    calculate_net_force,
    get_thrust,
)


def test_gravity_calculation() -> None:
    assert calculate_gravity(10.0) == 98.10000000000001


def test_drag_calculation() -> None:
    drag = calculate_drag(10.0, 0.45, 0.02)
    assert drag == pytest.approx(0.55125)


def test_net_force_calculation() -> None:
    net_force = calculate_net_force(300.0, 10.0, 98.1, 12.0)
    assert net_force < 202.0


def test_acceleration_calculation() -> None:
    assert calculate_acceleration(100.0, 5.0) == 20.0


def test_isa_air_density_decreases_with_altitude() -> None:
    assert round(get_air_density(0.0), 3) == 1.225
    assert round(get_air_density(1000.0), 3) == 1.112
    assert round(get_air_density(5000.0), 3) == 0.736
    assert round(get_air_density(10000.0), 3) == 0.413
    assert get_air_density(10000.0) < get_air_density(5000.0)


def test_thrust_curve_has_realistic_burn_shape() -> None:
    ignition_thrust = get_thrust(0.2, 300.0, 8.0)
    peak_thrust = get_thrust(2.0, 300.0, 8.0)
    tailoff_thrust = get_thrust(7.5, 300.0, 8.0)

    assert 0.0 < ignition_thrust < peak_thrust
    assert peak_thrust == 300.0
    assert 0.0 < tailoff_thrust < peak_thrust
    assert get_thrust(8.0, 300.0, 8.0) == 0.0