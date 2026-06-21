"""Main flight simulation engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import MAX_SIMULATION_TIME, TIME_STEP
from physics import calculate_acceleration, calculate_drag, calculate_gravity, calculate_net_force, calculate_thrust
from rocket import Rocket
from telemetry import TelemetryLogger


@dataclass
class SimulationResult:
    telemetry: pd.DataFrame
    logger: TelemetryLogger


class RocketSimulator:
    """Simulate a vertically launched single-stage rocket."""

    def __init__(self, rocket: Rocket, time_step: float = TIME_STEP, max_time: float = MAX_SIMULATION_TIME) -> None:
        self.rocket = rocket
        self.time_step = time_step
        self.max_time = max_time
        self.logger = TelemetryLogger()

    def run(self) -> SimulationResult:
        time_s = 0.0
        altitude_m = 0.0
        velocity_mps = 0.0
        acceleration_mps2 = 0.0
        burn_rate = self.rocket.fuel_mass / self.rocket.burn_time if self.rocket.burn_time > 0 else 0.0

        while time_s <= self.max_time:
            burn_active = time_s < self.rocket.burn_time and self.rocket.get_remaining_fuel() > 0
            mass = self.rocket.get_current_mass()
            gravity_force = calculate_gravity(mass)
            drag_force = calculate_drag(
                velocity=velocity_mps,
                drag_coefficient=self.rocket.drag_coefficient,
                cross_sectional_area=self.rocket.cross_sectional_area,
            )
            thrust_force = calculate_thrust(self.rocket.thrust, burn_active)
            net_force = calculate_net_force(thrust_force, drag_force, gravity_force, velocity_mps)
            acceleration_mps2 = calculate_acceleration(net_force, mass)

            velocity_mps += acceleration_mps2 * self.time_step
            altitude_m += velocity_mps * self.time_step

            if altitude_m < 0:
                altitude_m = 0.0
                velocity_mps = 0.0

            if burn_active and burn_rate > 0:
                self.rocket.consume_fuel(burn_rate * self.time_step)

            self.logger.record(
                time_s=time_s,
                altitude_m=altitude_m,
                velocity_mps=velocity_mps,
                acceleration_mps2=acceleration_mps2,
                fuel_remaining_kg=self.rocket.get_remaining_fuel(),
            )

            if time_s > 0 and altitude_m <= 0 and velocity_mps <= 0 and not burn_active:
                break

            time_s += self.time_step

        return SimulationResult(telemetry=self.logger.to_dataframe(), logger=self.logger)
