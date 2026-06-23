import { NextResponse } from 'next/server';
import { mapVehicleToSimulatorParameters, getRocketByName } from '../../../lib/rocket-library';
import { runSimulation } from '../../../lib/simulation';

export async function POST(request: Request) {
  const body = (await request.json()) as {
    vehicleName?: string;
    custom?: {
      dry_mass: number;
      fuel_mass: number;
      thrust: number;
      burn_time: number;
      drag_coefficient: number;
      cross_sectional_area: number;
    };
  };

  const vehicleName = body.vehicleName ?? 'Custom Rocket';
  const vehicle = vehicleName === 'Custom Rocket' ? null : getRocketByName(vehicleName);
  const inputs = vehicle ? mapVehicleToSimulatorParameters(vehicle) : body.custom;

  if (!inputs) {
    return NextResponse.json({ error: 'Missing simulator inputs.' }, { status: 400 });
  }

  const result = runSimulation(inputs);
  return NextResponse.json({ vehicleName, result });
}
