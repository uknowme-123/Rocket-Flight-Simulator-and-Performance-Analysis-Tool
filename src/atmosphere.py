"""International Standard Atmosphere approximations for flight simulation."""

from __future__ import annotations

import math

SEA_LEVEL_TEMPERATURE_K = 288.15
SEA_LEVEL_PRESSURE_PA = 101_325.0
SEA_LEVEL_DENSITY_KG_M3 = 1.225
TROPOSPHERE_LAPSE_RATE_K_M = 0.0065
TROPOSPHERE_LIMIT_M = 11_000.0
GAS_CONSTANT_AIR_J_KG_K = 287.05
STANDARD_GRAVITY_MPS2 = 9.80665


def get_air_density(altitude: float) -> float:
    """Return air density in kg/m^3 using a simplified ISA model.

    The troposphere model cools linearly with altitude. Above 11 km this
    switches to an isothermal lower-stratosphere approximation, which is
    sufficient for this vertical flight simulator and avoids negative
    temperatures at high altitude.
    """

    altitude_m = max(float(altitude), 0.0)

    if altitude_m <= TROPOSPHERE_LIMIT_M:
        temperature_k = SEA_LEVEL_TEMPERATURE_K - (
            TROPOSPHERE_LAPSE_RATE_K_M * altitude_m
        )
        pressure_pa = SEA_LEVEL_PRESSURE_PA * (
            temperature_k / SEA_LEVEL_TEMPERATURE_K
        ) ** (
            STANDARD_GRAVITY_MPS2
            / (GAS_CONSTANT_AIR_J_KG_K * TROPOSPHERE_LAPSE_RATE_K_M)
        )
        return pressure_pa / (GAS_CONSTANT_AIR_J_KG_K * temperature_k)

    temperature_11km_k = SEA_LEVEL_TEMPERATURE_K - (
        TROPOSPHERE_LAPSE_RATE_K_M * TROPOSPHERE_LIMIT_M
    )
    pressure_11km_pa = SEA_LEVEL_PRESSURE_PA * (
        temperature_11km_k / SEA_LEVEL_TEMPERATURE_K
    ) ** (
        STANDARD_GRAVITY_MPS2
        / (GAS_CONSTANT_AIR_J_KG_K * TROPOSPHERE_LAPSE_RATE_K_M)
    )
    pressure_pa = pressure_11km_pa * math.exp(
        -STANDARD_GRAVITY_MPS2
        * (altitude_m - TROPOSPHERE_LIMIT_M)
        / (GAS_CONSTANT_AIR_J_KG_K * temperature_11km_k)
    )
    return pressure_pa / (GAS_CONSTANT_AIR_J_KG_K * temperature_11km_k)
