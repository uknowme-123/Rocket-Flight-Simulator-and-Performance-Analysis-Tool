export type SimulationInputs = {
  dry_mass: number;
  fuel_mass: number;
  thrust: number;
  burn_time: number;
  drag_coefficient: number;
  cross_sectional_area: number;
};

export type TelemetryPoint = {
  time_s: number;
  altitude_m: number;
  velocity_mps: number;
  acceleration_mps2: number;
  mass_kg: number;
  fuel_remaining_kg: number;
  thrust_n: number;
  drag_force_n: number;
  flight_phase: string;
  air_density_kg_m3: number;
};

export type SimulationResult = {
  telemetry: TelemetryPoint[];
  summary: {
    maximum_altitude_m: number;
    maximum_velocity_mps: number;
    apogee_time_s: number;
    landing_velocity_mps: number;
  };
};

const GRAVITY = 9.81;
const TIME_STEP = 0.5;

function airDensity(altitude: number): number {
  return altitude <= 0 ? 1.225 : 1.225 * Math.exp(-altitude / 8500);
}

function phaseAt(time: number, burnTime: number, altitude: number, velocity: number): string {
  if (time <= 0) return 'PRE-LAUNCH';
  if (time < 1) return 'LIFTOFF';
  if (time <= burnTime) return 'POWERED_ASCENT';
  if (velocity > 0) return 'COASTING';
  if (velocity <= 0 && altitude > 0) return 'DESCENT';
  return 'LANDING';
}

export function runSimulation(inputs: SimulationInputs): SimulationResult {
  const telemetry: TelemetryPoint[] = [];
  let time = 0;
  let altitude = 0;
  let velocity = 0;
  let fuel = inputs.fuel_mass;
  let maxAltitude = 0;
  let maxVelocity = 0;
  let apogeeTime = 0;
  let landedVelocity = 0;

  for (let step = 0; step < 600; step += 1) {
    const thrustActive = time <= inputs.burn_time && fuel > 0;
    const thrust = thrustActive ? inputs.thrust : 0;
    const burnRate = thrustActive ? inputs.fuel_mass / Math.max(inputs.burn_time, 1) * TIME_STEP : 0;
    fuel = Math.max(0, fuel - burnRate);

    const mass = inputs.dry_mass + fuel;
    const density = airDensity(altitude);
    const dragForce = 0.5 * density * inputs.drag_coefficient * inputs.cross_sectional_area * velocity * velocity * Math.sign(velocity || 1);
    const netForce = thrust - mass * GRAVITY - dragForce;
    const acceleration = netForce / mass;

    velocity += acceleration * TIME_STEP;
    altitude = Math.max(0, altitude + velocity * TIME_STEP);

    if (altitude > maxAltitude) {
      maxAltitude = altitude;
      apogeeTime = time;
    }
    if (Math.abs(velocity) > Math.abs(maxVelocity)) {
      maxVelocity = velocity;
    }

    const flightPhase = phaseAt(time, inputs.burn_time, altitude, velocity);

    telemetry.push({
      time_s: time,
      altitude_m: altitude,
      velocity_mps: velocity,
      acceleration_mps2: acceleration,
      mass_kg: mass,
      fuel_remaining_kg: fuel,
      thrust_n: thrust,
      drag_force_n: Math.abs(dragForce),
      flight_phase: flightPhase,
      air_density_kg_m3: density,
    });

    landedVelocity = velocity;
    time += TIME_STEP;

    if (altitude <= 0 && time > 5 && thrust === 0 && velocity < 0) {
      break;
    }
  }

  return {
    telemetry,
    summary: {
      maximum_altitude_m: maxAltitude,
      maximum_velocity_mps: maxVelocity,
      apogee_time_s: apogeeTime,
      landing_velocity_mps: landedVelocity,
    },
  };
}
