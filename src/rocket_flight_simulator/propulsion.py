"""Solid rocket motor thrust curve and fuel-flow utilities."""

from __future__ import annotations

from .config import GRAVITY


def get_thrust(time: float, peak_thrust: float = 300.0, burn_time: float = 8.0) -> float:
    """Return motor thrust in newtons from a five-phase burn curve.

    The curve approximates a small solid motor: brief ignition, ramp-up to
    chamber pressure, near-peak thrust, a sustained burn, and final tail-off.
    """

    if time < 0.0 or peak_thrust <= 0.0 or burn_time <= 0.0:
        return 0.0

    normalized_time = time / burn_time
    if normalized_time >= 1.0:
        return 0.0

    ignition_end = 0.05
    ramp_end = 0.15
    peak_end = 0.35
    sustain_end = 0.85
    ignition_fraction = 0.20
    sustain_fraction = 0.78

    if normalized_time < ignition_end:
        phase_progress = normalized_time / ignition_end
        return peak_thrust * ignition_fraction * phase_progress

    if normalized_time < ramp_end:
        phase_progress = (normalized_time - ignition_end) / (
            ramp_end - ignition_end
        )
        thrust_fraction = ignition_fraction + (
            (1.0 - ignition_fraction) * phase_progress
        )
        return peak_thrust * thrust_fraction

    if normalized_time < peak_end:
        return peak_thrust

    if normalized_time < sustain_end:
        phase_progress = (normalized_time - peak_end) / (
            sustain_end - peak_end
        )
        thrust_fraction = 1.0 - ((1.0 - sustain_fraction) * phase_progress)
        return peak_thrust * thrust_fraction

    phase_progress = (normalized_time - sustain_end) / (1.0 - sustain_end)
    return peak_thrust * sustain_fraction * (1.0 - phase_progress)


def estimate_total_impulse(
    peak_thrust: float,
    burn_time: float,
    samples: int = 500,
) -> float:
    """Estimate total impulse in newton-seconds from the thrust curve."""

    if peak_thrust <= 0.0 or burn_time <= 0.0:
        return 0.0

    sample_count = max(samples, 2)
    time_step = burn_time / (sample_count - 1)
    impulse_ns = 0.0

    for index in range(sample_count - 1):
        t0 = index * time_step
        t1 = (index + 1) * time_step
        impulse_ns += 0.5 * (
            get_thrust(t0, peak_thrust, burn_time)
            + get_thrust(t1, peak_thrust, burn_time)
        ) * time_step

    return impulse_ns


def calculate_specific_impulse(
    peak_thrust: float,
    burn_time: float,
    propellant_mass: float,
) -> float:
    """Return curve-calibrated specific impulse in seconds."""

    if propellant_mass <= 0.0:
        return 0.0

    total_impulse_ns = estimate_total_impulse(peak_thrust, burn_time)
    return total_impulse_ns / (propellant_mass * GRAVITY)


def calculate_mass_flow_rate(thrust: float, specific_impulse: float) -> float:
    """Return propellant mass flow in kg/s from thrust and specific impulse."""

    if thrust <= 0.0 or specific_impulse <= 0.0:
        return 0.0
    return thrust / (specific_impulse * GRAVITY)
