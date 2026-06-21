"""Main flight simulation engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from atmosphere import get_air_density
from config import MAX_SIMULATION_TIME, TIME_STEP
from flight_phases import FlightPhase, detect_flight_phase
from physics import calculate_acceleration, calculate_drag, calculate_gravity, calculate_net_force
from propulsion import calculate_mass_flow_rate, get_thrust
from rocket import Rocket
from telemetry import TelemetryLogger


@dataclass
class SimulationResult:
    telemetry: pd.DataFrame
    logger: TelemetryLogger


class RocketSimulator:
    """Simulate a vertically launched single-stage rocket."""

    def __init__(
        self,
        rocket: Rocket,
        time_step: float = TIME_STEP,
        max_time: float = MAX_SIMULATION_TIME,
    ) -> None:
        self.rocket = rocket
        self.time_step = time_step
        self.max_time = max_time
        self.logger = TelemetryLogger()

    def run(self) -> SimulationResult:
        time_s = 0.0
        altitude_m = 0.0
        velocity_mps = 0.0
        acceleration_mps2 = 0.0
        has_lifted_off = False
        apogee_detected = False
        previous_velocity_mps = 0.0

        while time_s <= self.max_time:
            was_lifted_off = has_lifted_off
            mass = self.rocket.get_current_mass()
            air_density = get_air_density(altitude_m)
            gravity_force = calculate_gravity(mass)
            drag_force = calculate_drag(
                velocity=velocity_mps,
                drag_coefficient=self.rocket.drag_coefficient,
                cross_sectional_area=self.rocket.cross_sectional_area,
                air_density=air_density,
            )
            thrust_force = get_thrust(time_s, self.rocket.thrust, self.rocket.burn_time)
            if self.rocket.get_remaining_fuel() <= 0.0:
                thrust_force = 0.0

            net_force = calculate_net_force(thrust_force, drag_force, gravity_force, velocity_mps)
            acceleration_mps2 = calculate_acceleration(net_force, mass)

            new_velocity_mps = velocity_mps + acceleration_mps2 * self.time_step
            new_altitude_m = altitude_m + new_velocity_mps * self.time_step
            landed = has_lifted_off and new_altitude_m <= 0.0 and new_velocity_mps < 0.0

            if not has_lifted_off and new_altitude_m <= 0.0:
                new_altitude_m = 0.0
                new_velocity_mps = 0.0

            if landed:
                new_altitude_m = 0.0

            mass_flow_rate = calculate_mass_flow_rate(
                thrust_force,
                self.rocket.specific_impulse,
            )
            if mass_flow_rate > 0.0:
                self.rocket.consume_fuel(mass_flow_rate * self.time_step)

            phase = detect_flight_phase(
                altitude_m=new_altitude_m,
                velocity_mps=new_velocity_mps,
                previous_velocity_mps=previous_velocity_mps,
                thrust_n=thrust_force,
                has_lifted_off=was_lifted_off,
                apogee_detected=apogee_detected,
                landed=landed,
            )
            if phase == FlightPhase.APOGEE:
                apogee_detected = True

            if new_altitude_m > 0.0:
                has_lifted_off = True

            self.logger.record(
                time_s=time_s,
                altitude_m=new_altitude_m,
                velocity_mps=new_velocity_mps,
                acceleration_mps2=acceleration_mps2,
                mass_kg=self.rocket.get_current_mass(),
                fuel_remaining_kg=self.rocket.get_remaining_fuel(),
                thrust_n=thrust_force,
                drag_force_n=drag_force,
                flight_phase=str(phase),
                air_density_kg_m3=air_density,
            )

            if landed:
                break

            if not has_lifted_off and time_s >= self.rocket.burn_time and thrust_force <= 0.0:
                break

            previous_velocity_mps = new_velocity_mps
            velocity_mps = new_velocity_mps
            altitude_m = new_altitude_m
            time_s += self.time_step

        return SimulationResult(telemetry=self.logger.to_dataframe(), logger=self.logger)
