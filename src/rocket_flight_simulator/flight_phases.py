"""Flight phase detection for vertical rocket missions."""

from __future__ import annotations

from enum import Enum


class FlightPhase(str, Enum):
    """Named mission phases stored in telemetry."""

    PRE_LAUNCH = "PRE-LAUNCH"
    LIFTOFF = "LIFTOFF"
    POWERED_ASCENT = "POWERED_ASCENT"
    COASTING = "COASTING"
    APOGEE = "APOGEE"
    DESCENT = "DESCENT"
    LANDING = "LANDING"

    def __str__(self) -> str:
        return self.value


def detect_flight_phase(
    altitude_m: float,
    velocity_mps: float,
    previous_velocity_mps: float,
    thrust_n: float,
    has_lifted_off: bool,
    apogee_detected: bool,
    landed: bool,
) -> FlightPhase:
    """Classify the current sample into a mission phase.

    Upward velocity is positive. Apogee is detected on the first transition
    from upward motion to downward motion after liftoff.
    """

    if landed:
        return FlightPhase.LANDING

    if not has_lifted_off and altitude_m <= 0.0 and velocity_mps <= 0.0:
        return FlightPhase.PRE_LAUNCH

    if not has_lifted_off and (altitude_m > 0.0 or velocity_mps > 0.0 or thrust_n > 0.0):
        return FlightPhase.LIFTOFF

    if thrust_n > 0.0 and velocity_mps >= 0.0:
        return FlightPhase.POWERED_ASCENT

    if (
        has_lifted_off
        and not apogee_detected
        and previous_velocity_mps > 0.0
        and velocity_mps <= 0.0
    ):
        return FlightPhase.APOGEE

    if velocity_mps >= 0.0:
        return FlightPhase.COASTING

    return FlightPhase.DESCENT
