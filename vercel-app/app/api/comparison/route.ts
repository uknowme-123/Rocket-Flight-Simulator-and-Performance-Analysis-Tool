import { NextResponse } from 'next/server';
import { buildComparisonRows } from '../../../lib/rocket-library';

export async function GET() {
  return NextResponse.json({ comparison: buildComparisonRows() });
}
