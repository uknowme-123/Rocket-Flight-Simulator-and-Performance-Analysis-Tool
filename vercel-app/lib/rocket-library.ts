import rocketLibrary from '../data/rocket-library.json';
import { DEFAULT_PROPELLANT_FRACTION } from './constants';

export type RocketRecord = {
  country: string;
  organization: string;
  height_m: number;
  diameter_m: number;
  stages: number;
  liftoff_mass_kg: number;
  payload_leo_kg: number;
  thrust_kn: number;
  burn_time_s: number;
  drag_coefficient: number;
  cross_section_area_m2: number;
  description: string;
};

export const EDUCATIONAL_DISCLAIMER =
  'Vehicle specifications are simplified and adapted for educational simulation. The simulator does not reproduce real-world launch performance.';

export function loadRocketLibrary(): Record<string, RocketRecord> {
  return rocketLibrary as Record<string, RocketRecord>;
}

export function getRocketNames(): string[] {
  return ['Custom Rocket', ...Object.keys(loadRocketLibrary()).sort()];
}

export function getRocketByName(name: string): RocketRecord | null {
  return loadRocketLibrary()[name] ?? null;
}

export function returnVehicleSummary(name: string): string {
  const rocket = getRocketByName(name);
  if (!rocket) {
    return `No launch vehicle found for '${name}'.`;
  }

  return `${name} | ${rocket.country} | ${rocket.organization} | Height ${rocket.height_m} m | Payload LEO ${rocket.payload_leo_kg} kg`;
}

export function mapVehicleToSimulatorParameters(rocket: RocketRecord) {
  const liftoffMass = Math.max(rocket.liftoff_mass_kg, 1);
  const fuelMass = liftoffMass * DEFAULT_PROPELLANT_FRACTION;
  const dryMass = liftoffMass - fuelMass;

  return {
    dry_mass: dryMass,
    fuel_mass: fuelMass,
    thrust: rocket.thrust_kn * 1000,
    burn_time: rocket.burn_time_s,
    drag_coefficient: rocket.drag_coefficient,
    cross_sectional_area: rocket.cross_section_area_m2,
  };
}

export function buildComparisonRows() {
  return Object.entries(loadRocketLibrary()).map(([name, rocket]) => ({
    Rocket: name,
    Country: rocket.country,
    Height: rocket.height_m,
    Stages: rocket.stages,
    Mass: rocket.liftoff_mass_kg,
    Payload: rocket.payload_leo_kg,
    Thrust: rocket.thrust_kn,
  }));
}
