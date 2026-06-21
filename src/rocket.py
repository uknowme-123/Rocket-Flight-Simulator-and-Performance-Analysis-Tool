"""Rocket model and mass bookkeeping utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rocket:
    """Represent a single-stage vertically launched rocket."""

    dry_mass: float
    fuel_mass: float
    thrust: float
    burn_time: float
    drag_coefficient: float
    cross_sectional_area: float

    def get_total_mass(self) -> float:
        return self.dry_mass + self.fuel_mass

    def get_remaining_fuel(self) -> float:
        return max(self.fuel_mass, 0.0)

    def consume_fuel(self, amount: float) -> float:
        consumed = max(min(amount, self.fuel_mass), 0.0)
        self.fuel_mass -= consumed
        return consumed

    def get_current_mass(self) -> float:
        return self.dry_mass + self.get_remaining_fuel()
