"""Physics helpers for the rocket flight simulator."""

from __future__ import annotations

from config import AIR_DENSITY, GRAVITY


def calculate_gravity(mass: float) -> float:
    """Return the magnitude of gravitational force on the vehicle."""

    return mass * GRAVITY


def calculate_drag(
    velocity: float,
    drag_coefficient: float,
    cross_sectional_area: float,
    air_density: float | None = None,
) -> float:
    """Return aerodynamic drag magnitude in newtons.

    Drag grows with dynamic pressure, so velocity is squared. The signed
    direction is handled by ``calculate_net_force`` because drag always opposes
    the current direction of motion.
    """

    density = AIR_DENSITY if air_density is None else max(air_density, 0.0)
    if drag_coefficient < 0.0 or cross_sectional_area < 0.0:
        raise ValueError("Drag coefficient and area must be non-negative.")
    return 0.5 * density * drag_coefficient * cross_sectional_area * velocity * velocity


def calculate_net_force(
    thrust_force: float,
    drag_force: float,
    gravity_force: float,
    velocity: float,
) -> float:
    """Return signed net force using upward as positive."""

    drag_direction = -1.0 if velocity > 0.0 else 1.0
    drag_component = drag_force * drag_direction
    return thrust_force + drag_component - gravity_force


def calculate_acceleration(net_force: float, mass: float) -> float:
    """Return acceleration from Newton's second law."""

    if mass <= 0:
        raise ValueError("Mass must be positive for acceleration calculation.")
    return net_force / mass
