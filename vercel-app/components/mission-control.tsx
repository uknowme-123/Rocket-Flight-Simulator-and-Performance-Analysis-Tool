"use client";

import { useEffect, useState } from 'react';
import {
  EDUCATIONAL_DISCLAIMER,
  buildComparisonRows,
  getRocketByName,
  getRocketNames,
  mapVehicleToSimulatorParameters,
  type RocketRecord,
} from '../lib/rocket-library';
import type { SimulationResult } from '../lib/simulation';

type SimulationResponse = {
  vehicleName: string;
  result: SimulationResult;
};

const vehicleNames = getRocketNames();
const comparisonRows = buildComparisonRows();

export function MissionControlDashboard() {
  const [vehicleName, setVehicleName] = useState('Falcon 9');
  const [customInputs, setCustomInputs] = useState({
    dry_mass: 3,
    fuel_mass: 2,
    thrust: 300,
    burn_time: 8,
    drag_coefficient: 0.45,
    cross_sectional_area: 0.02,
  });
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedVehicle = vehicleName === 'Custom Rocket' ? null : getRocketByName(vehicleName);
  const simulatorInputs = selectedVehicle ? mapVehicleToSimulatorParameters(selectedVehicle) : customInputs;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vehicleName,
        custom: vehicleName === 'Custom Rocket' ? customInputs : undefined,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Simulation request failed.');
        }
        return (await response.json()) as SimulationResponse;
      })
      .then((payload) => {
        if (active) {
          setResult(payload.result);
        }
      })
      .catch((simulationError: unknown) => {
        if (active) {
          setError(simulationError instanceof Error ? simulationError.message : 'Unknown error');
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [vehicleName, customInputs]);

  return (
    <main className="container">
      <section className="panel p-8 mb-8">
        <p className="text-xs tracking-[0.28em] uppercase text-sky-300">Rocket Flight Simulator</p>
        <h1 className="mt-3 text-4xl font-bold text-white">Vercel-Compatible Mission Control</h1>
        <p className="mt-4 max-w-3xl text-slate-300">
          Select a launch vehicle, inspect its simplified specifications, and run a lightweight simulation that can be deployed on Vercel.
        </p>
        <p className="mt-4 text-sm text-amber-200">{EDUCATIONAL_DISCLAIMER}</p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="panel p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Launch Vehicle Selector</h2>
              <p className="mt-2 text-sm text-slate-300">Choose a predefined launch vehicle or switch to custom rocket input.</p>
            </div>
            <select
              className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none"
              value={vehicleName}
              onChange={(event) => setVehicleName(event.target.value)}
            >
              {vehicleNames.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          {vehicleName === 'Custom Rocket' ? (
            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Object.entries(customInputs).map(([key, value]) => (
                <label key={key} className="rounded-2xl border border-slate-700 bg-slate-950/50 p-4 text-sm text-slate-200">
                  <span className="block text-xs uppercase tracking-[0.2em] text-slate-400">{key.replaceAll('_', ' ')}</span>
                  <input
                    className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white outline-none"
                    type="number"
                    value={value}
                    step="0.01"
                    onChange={(event) =>
                      setCustomInputs((current) => ({
                        ...current,
                        [key]: Number(event.target.value),
                      }))
                    }
                  />
                </label>
              ))}
            </div>
          ) : null}

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {(selectedVehicle ? [selectedVehicle] : []).map((rocket) => (
              <InfoCard
                key={rocket.organization}
                title={rocket.organization}
                value={`${rocket.country} • ${rocket.stages} stages`}
              />
            ))}
            {selectedVehicle ? (
              <>
                <InfoCard title="Height" value={`${selectedVehicle.height_m} m`} />
                <InfoCard title="Payload LEO" value={`${selectedVehicle.payload_leo_kg} kg`} />
                <InfoCard title="Thrust" value={`${selectedVehicle.thrust_kn} kN`} />
              </>
            ) : null}
          </div>
        </div>

        <div className="panel p-6">
          <h2 className="text-xl font-semibold text-white">Mission Summary</h2>
          <p className="mt-2 text-sm text-slate-300">
            This preview simulates the selected vehicle using the same educational modeling approach as the simulator.
          </p>
          {loading ? <p className="mt-4 text-sky-300">Running simulation...</p> : null}
          {error ? <p className="mt-4 text-red-300">{error}</p> : null}
          {result ? (
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <Metric label="Max Altitude" value={`${result.summary.maximum_altitude_m.toFixed(1)} m`} />
              <Metric label="Max Velocity" value={`${result.summary.maximum_velocity_mps.toFixed(1)} m/s`} />
              <Metric label="Apogee Time" value={`${result.summary.apogee_time_s.toFixed(1)} s`} />
              <Metric label="Landing Velocity" value={`${result.summary.landing_velocity_mps.toFixed(1)} m/s`} />
            </div>
          ) : null}
        </div>
      </section>

      <section className="panel mt-8 p-6 overflow-x-auto">
        <h2 className="text-xl font-semibold text-white">Rocket Comparison</h2>
        <table className="mt-4 w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="py-2">Rocket</th>
              <th>Country</th>
              <th>Height</th>
              <th>Stages</th>
              <th>Mass</th>
              <th>Payload</th>
              <th>Thrust</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row) => (
              <tr key={row.Rocket} className="border-t border-slate-800 text-slate-200">
                <td className="py-2">{row.Rocket}</td>
                <td>{row.Country}</td>
                <td>{row.Height} m</td>
                <td>{row.Stages}</td>
                <td>{row.Mass} kg</td>
                <td>{row.Payload} kg</td>
                <td>{row.Thrust} kN</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}

function InfoCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-sky-500/20 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{title}</p>
      <p className="mt-2 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-sky-500/20 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-sky-300">{value}</p>
    </div>
  );
}
