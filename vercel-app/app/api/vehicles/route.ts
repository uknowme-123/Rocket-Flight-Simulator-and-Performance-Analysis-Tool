import { NextResponse } from 'next/server';
import { buildComparisonRows, getRocketNames, getRocketByName } from '../../../lib/rocket-library';

export async function GET() {
  return NextResponse.json({
    rocketNames: getRocketNames(),
    vehicles: Object.fromEntries(
      getRocketNames()
        .filter((name) => name !== 'Custom Rocket')
        .map((name) => [name, getRocketByName(name)])
    ),
    comparison: buildComparisonRows(),
  });
}
