"""Rocket model and mass bookkeeping utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from propulsion import calculate_specific_impulse


@dataclass
class Rocket:
    """Represent a single-stage vertically launched rocket."""

    dry_mass: float
    fuel_mass: float
    thrust: float
    burn_time: float
    drag_coefficient: float
    cross_sectional_area: float
    initial_fuel_mass: float = field(init=False)
    specific_impulse: float = field(init=False)

    def __post_init__(self) -> None:
        if self.dry_mass <= 0.0:
            raise ValueError("Dry mass must be positive.")
        if self.fuel_mass < 0.0:
            raise ValueError("Fuel mass cannot be negative.")
        if self.thrust < 0.0:
            raise ValueError("Thrust cannot be negative.")
        if self.burn_time < 0.0:
            raise ValueError("Burn time cannot be negative.")
        if self.drag_coefficient < 0.0 or self.cross_sectional_area <= 0.0:
            raise ValueError("Aerodynamic parameters must be physically valid.")

        self.initial_fuel_mass = self.fuel_mass
        self.specific_impulse = calculate_specific_impulse(
            self.thrust,
            self.burn_time,
            self.initial_fuel_mass,
        )

    def get_total_mass(self) -> float:
        return self.dry_mass + self.initial_fuel_mass

    def get_remaining_fuel(self) -> float:
        return max(self.fuel_mass, 0.0)

    def consume_fuel(self, amount: float) -> float:
        consumed = max(min(amount, self.fuel_mass), 0.0)
        self.fuel_mass -= consumed
        return consumed

    def get_current_mass(self) -> float:
        return self.dry_mass + self.get_remaining_fuel()
