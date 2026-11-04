# Rocket Flight Simulator and Performance Analysis Tool - Repository Audit Report

**Date:** 2026-10-31  
**Auditor:** Senior Aerospace Software Engineer  
**Scope:** Complete repository audit for V2 avionics integration planning

---

## 1. Repository Architecture Report

### 1.1 Project Structure Overview

```
Rocket-Flight-Simulator-and-Performance-Analysis-Tool/
├── README.md                              # Project documentation
├── requirements.txt                       # Python dependencies
├── LICENSE
├── src/                                   # Core Python simulation engine
│   ├── __init__.py                        # (missing - needs creation)
│   ├── main.py                            # CLI entry point
│   ├── config.py                          # Global constants
│   ├── atmosphere.py                      # ISA atmospheric model
│   ├── propulsion.py                      # Thrust curve & mass flow
│   ├── physics.py                         # Force/acceleration calculations
│   ├── rocket.py                          # Rocket dataclass & mass bookkeeping
│   ├── flight_phases.py                   # Flight phase state machine
│   ├── telemetry.py                       # Telemetry logging & CSV export
│   ├── simulator.py                       # Main simulation loop
│   ├── mission.py                         # Mission analysis & metrics
│   ├── visualization.py                   # Matplotlib plotting
│   ├── report_generator.py                # PDF report generation
│   └── rocket_library.py                  # Launch vehicle library
├── dashboard/                             # Streamlit Mission Control
│   ├── app.py                             # Main dashboard application
│   ├── ui_components.py                   # Reusable UI components & CSS
│   ├── audio_system.py                    # Event-driven audio alerts
│   └── assets/                            # Audio files (.mp3)
├── data/                                  # Input data & output
│   ├── rocket_parameters.json             # Default custom rocket config
│   ├── rocket_library.json                # 9 launch vehicles (full)
│   ├── sample_mission.json                # Mission metadata (unused)
│   └── simulation_output.csv              # Generated telemetry
├── reports/                               # Generated outputs
│   ├── mission_report.pdf
│   └── mission_summary.txt
├── screenshots/                           # Generated plots
├── tests/                                 # Unit tests (12 tests, all passing)
│   ├── test_rocket.py
│   ├── test_physics.py
│   ├── test_rocket_library.py
│   └── test_simulator.py
└── vercel-app/                            # Next.js/Vercel deployment
    ├── package.json
    ├── tsconfig.json
    ├── next.config.mjs
    ├── vercel.json
    ├── app/
    │   ├── page.tsx                       # Main page
    │   ├── layout.tsx
    │   ├── globals.css
    │   └── api/
    │       ├── simulate/route.ts          # Simulation API
    │       ├── vehicles/route.ts          # Vehicle library API
    │       └── comparison/route.ts        # Comparison table API
    ├── components/
    │   └── mission-control.tsx            # React dashboard component
    ├── lib/
    │   ├── simulation.ts                  # TypeScript simulation engine
    │   └── rocket-library.ts              # TypeScript vehicle library
    └── data/
        └── rocket-library.json            # 5 vehicles (subset)
```

### 1.2 Architecture Patterns

| Layer | Python (src/) | TypeScript (vercel-app/) | Notes |
|-------|--------------|-------------------------|-------|
| **Configuration** | `config.py` - global constants | Embedded in `simulation.ts` | Python uses module-level constants |
| **Atmosphere** | `atmosphere.py` - ISA troposphere + stratosphere | `simulation.ts:airDensity()` - exponential decay | **Different models** |
| **Propulsion** | `propulsion.py` - 5-phase thrust curve | `simulation.ts` - constant thrust | **Different models** |
| **Physics** | `physics.py` - modular force functions | Inline in `runSimulation()` | Python more modular |
| **Phase Detection** | `flight_phases.py` - state machine with flags | `simulation.ts:phaseAt()` - simple heuristics | **Different logic** |
| **Rocket Model** | `rocket.py` - dataclass with mass tracking | Inline in `runSimulation()` | Python has proper encapsulation |
| **Telemetry** | `telemetry.py` - structured logging | Inline array push | Python more sophisticated |
| **Vehicle Library** | `rocket_library.py` - full featured | `rocket-library.ts` - equivalent | **Duplicated logic** |
| **Visualization** | `visualization.py` - Matplotlib | Altair in React | Different tech stacks |
| **Reports** | `report_generator.py` - ReportLab PDF | Not implemented in TS | Python only |

---

## 2. Existing Test Results

### 2.1 Python Unit Tests (pytest)

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
collected 12 items

tests/test_physics.py::test_gravity_calculation PASSED
tests/test_physics.py::test_drag_calculation PASSED
tests/test_physics.py::test_net_force_calculation PASSED
tests/test_physics.py::test_acceleration_calculation PASSED
tests/test_physics.py::test_isa_air_density_decreases_with_altitude PASSED
tests/test_physics.py::test_thrust_curve_has_realistic_burn_shape PASSED
tests/test_rocket.py::test_rocket_mass_updates PASSED
tests/test_rocket_library.py::test_library_loads_known_vehicles PASSED
tests/test_rocket_library.py::test_lookup_and_mapping_for_simulator PASSED
tests/test_rocket_library.py::test_summary_and_comparison_rows PASSED
tests/test_simulator.py::test_simulation_execution PASSED
tests/test_simulator.py::test_simulation_records_new_physics_outputs PASSED

============================= 12 passed in 5.04s ==============================
```

**Result:** All 12 tests pass. Coverage includes:
- Gravity calculations
- Drag calculations (with altitude-dependent density)
- Net force calculations (with velocity-dependent drag direction)
- Acceleration calculations
- ISA air density model validation
- Thrust curve shape validation
- Rocket mass bookkeeping
- Rocket library loading, lookup, mapping, and comparison
- Simulation execution and telemetry column validation
- Physics outputs (mass depletion, thrust, drag, apogee detection)

### 2.2 Next.js Build Test

```
✓ Compiled successfully
✓ Generating static pages (7/7)
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    2.64 kB        89.7 kB
├ ○ /_not-found                          873 B            88 kB
├ ○ /api/comparison                      0 B                0 B
├ ƒ /api/simulate                        0 B                0 B
└ ○ /api/vehicles                        0 B                0 B
+ First Load JS shared by all            87.1 kB
```

**Result:** Build succeeds. Three API routes are server-rendered (dynamic).

---

## 3. Files Requiring Modification

### 3.1 Critical Issues (Must Fix)

| File | Issue | Priority |
|------|-------|----------|
| `src/__init__.py` | **Missing** - package not importable without sys.path hack | HIGH |
| `dashboard/app.py:14-17` | Uses `sys.path.insert` to import `src` | HIGH |
| `vercel-app/data/rocket-library.json` | Missing 4 vehicles (Falcon Heavy, Saturn V, Soyuz, Ariane 5) | MEDIUM |
| `src/rocket_library.py:107` / `vercel-app/lib/rocket-library.ts:44` | Hardcoded `0.85` propellant fraction - duplicated | MEDIUM |

### 3.2 Architectural Issues (Should Fix)

| File | Issue | Priority |
|------|-------|----------|
| `src/config.py` | `AIR_DENSITY = 1.225` constant unused (atmosphere.py used instead) | LOW |
| `src/physics.py:5` | Imports `AIR_DENSITY` from config but overrides with parameter | LOW |
| `vercel-app/lib/simulation.ts` | Simplified physics (constant thrust, exponential atmosphere, simple phases) | MEDIUM |
| `vercel-app/lib/simulation.ts:34` | `TIME_STEP = 0.5` vs Python's `0.1` - different resolution | MEDIUM |
| `dashboard/app.py:130` | `inspect.signature()` runtime check for report generator params | LOW |

### 3.3 Missing Features (For V2 Consideration)

| File | Missing Capability |
|------|-------------------|
| `src/simulator.py` | No event hooks/callbacks for real-time sensor simulation |
| `src/telemetry.py` | No metadata schema (units, descriptions, sampling rate) |
| `src/rocket.py` | No stage separation support (single-stage only) |
| `src/mission.py` | No Monte Carlo or uncertainty analysis |
| `vercel-app/lib/simulation.ts` | No telemetry streaming/WebSocket support |

---

## 4. New Files Required for V2 (Avionics Integration)

### 4.1 Core Avionics Module (New)

```
src/avionics/
├── __init__.py
├── sensors.py              # Sensor models (IMU, barometer, GPS, etc.)
├── sensor_simulation.py    # Noise, bias, drift models
├── telemetry_bus.py        # Pub/sub for real-time data distribution
├── packet_protocol.py      # Binary packet encoding/decoding (COBS, etc.)
├── event_detector.py       # Apogee, burnout, staging events
└── health_monitor.py       # Subsystem health & fault detection
```

### 4.2 Telemetry Enhancement (New)

```
src/telemetry/
├── __init__.py
├── schema.py               # Telemetry metadata (units, rates, descriptions)
├── streaming.py            # Real-time telemetry streaming (WebSocket, MQTT)
├── recorder.py             # High-frequency binary logging
└── replay.py               # Post-flight replay with time synchronization
```

### 4.3 Hardware Interface (New)

```
src/hardware/
├── __init__.py
├── esp32_interface.py      # ESP32 serial/Bluetooth communication
├── flight_computer.py      # Flight computer abstraction layer
├── gpio_driver.py          # GPIO/pin control for pyro events
└── storage.py              # SD card / flash logging
```

### 4.4 Integration Layer (Modified)

```
src/
├── simulator.py            # ADD: callback hooks, event emission
├── telemetry.py            # ADD: schema validation, streaming support
├── rocket.py               # ADD: multi-stage support, stage events
└── mission.py              # ADD: avionics mission modes, abort criteria
```

### 4.5 Frontend Enhancements (vercel-app)

```
vercel-app/
├── components/
│   ├── avionics-panel.tsx      # Real-time sensor display
│   ├── telemetry-stream.tsx    # WebSocket telemetry consumer
│   └── health-monitor.tsx      # Subsystem health dashboard
├── lib/
│   ├── telemetry-schema.ts     # TypeScript telemetry types
│   └── websocket-client.ts     # Real-time data connection
└── app/api/
    ├── telemetry/route.ts      # Telemetry streaming endpoint
    └── health/route.ts         # Health check endpoint
```

---

## 5. Identified Technical Risks

### 5.1 High Risk

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Physics model divergence** between Python and TypeScript | Simulation results won't match across platforms | HIGH | Create shared physics specification; consider WASM port of Python engine |
| **No telemetry schema/metadata** | Cannot validate sensor data; units ambiguous | HIGH | Implement telemetry schema with units, sample rates, descriptions |
| **Single-stage only** | Cannot simulate real launch vehicles | HIGH | Design multi-stage architecture in V2 |
| **Hardcoded propellant fraction (0.85)** | Inaccurate mass modeling for different vehicle types | MEDIUM | Move to vehicle-specific data or configurable parameter |

### 5.2 Medium Risk

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Different atmosphere models** (ISA vs exponential) | Different drag, different apogee | MEDIUM | Unify on ISA model in both implementations |
| **Different phase detection logic** | Phase transitions at different times | MEDIUM | Port Python state machine to TypeScript |
| **No real-time simulation capability** | Cannot support hardware-in-the-loop | MEDIUM | Add callback hooks and streaming telemetry |
| **Missing `__init__.py` in src/** | Import fragility, not a proper package | MEDIUM | Add proper package structure |
| **Dashboard sys.path hack** | Brittle deployment, not PEP 561 compliant | MEDIUM | Install package in editable mode or fix imports |
| **Duplicated rocket library data** | Data inconsistency between Python and TS | MEDIUM | Single source of truth (JSON) with build-time sync |

### 5.3 Low Risk

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `sample_mission.json` unused | Dead code, confusion | LOW | Remove or integrate into mission planning |
| `config.AIR_DENSITY` unused | Dead constant | LOW | Remove |
| No ESLint in vercel-app | Code quality drift | LOW | Configure ESLint with Next.js recommended |
| Audio files as MP3 | Web Audio API prefers WAV/OGG | LOW | Convert or add fallbacks |

---

## 6. Recommended Implementation Order for V2

### Phase 1: Foundation (Week 1-2) - **No Physics Changes**

1. **Add `src/__init__.py`** - Make `src` a proper package
2. **Fix dashboard imports** - Use editable install or proper relative imports
3. **Create telemetry schema** (`src/telemetry/schema.py`) - Define units, sample rates, descriptions for all telemetry fields
4. **Sync rocket library data** - Update `vercel-app/data/rocket-library.json` to match `data/rocket_library.json` (9 vehicles)
5. **Extract propellant fraction constant** - Single definition shared by Python and TS

### Phase 2: Avionics Core (Week 3-4)

6. **Add callback hooks to simulator** (`src/simulator.py`) - Pre-step, post-step, phase-change, event callbacks
7. **Implement sensor models** (`src/avionics/sensors.py`) - IMU (accel, gyro), barometer, GPS, magnetometer
8. **Implement noise models** (`src/avionics/sensor_simulation.py`) - Bias, noise, drift, quantization
9. **Add telemetry streaming** (`src/telemetry/streaming.py`) - WebSocket server for real-time data

### Phase 3: Event & Health System (Week 5)

10. **Event detector** (`src/avionics/event_detector.py`) - Apogee, burnout, staging, landing detection with timestamps
11. **Health monitor** (`src/avionics/health_monitor.py`) - Subsystem health, limit checking, fault detection
12. **Telemetry recorder** (`src/telemetry/recorder.py`) - High-frequency binary logging with metadata

### Phase 4: Frontend Integration (Week 6)

13. **Telemetry WebSocket client** (`vercel-app/lib/websocket-client.ts`)
14. **Avionics dashboard panel** (`vercel-app/components/avionics-panel.tsx`) - Real-time sensor display
15. **Health monitor UI** (`vercel-app/components/health-monitor.tsx`)
16. **Sync physics models** - Port Python atmosphere, propulsion, phase detection to TypeScript (or use WASM)

### Phase 5: Hardware Interface (Week 7-8)

17. **ESP32 interface** (`src/hardware/esp32_interface.py`) - Serial/Bluetooth communication protocol
18. **Flight computer abstraction** (`src/hardware/flight_computer.py`)
19. **Packet protocol** (`src/avionics/packet_protocol.py`) - Binary encoding for radio telemetry
20. **Integration testing** - Hardware-in-the-loop validation

---

## 7. Telemetry Data Assessment for Avionics Integration

### 7.1 Current Telemetry Columns (from simulation_output.csv)

| Column | Units | Timestamp | Notes |
|--------|-------|-----------|-------|
| `time_s` | seconds | ✓ Primary timestamp | 0.1s resolution |
| `altitude_m` | meters | ✓ | ISA model derived |
| `velocity_mps` | m/s | ✓ | Signed (up=positive) |
| `acceleration_mps2` | m/s² | ✓ | Includes gravity |
| `mass_kg` | kg | ✓ | Depletes with fuel |
| `fuel_remaining_kg` | kg | ✓ | |
| `thrust_n` | newtons | ✓ | 5-phase curve |
| `drag_force_n` | newtons | ✓ | Magnitude only |
| `flight_phase` | enum string | ✓ | 7 phases |
| `air_density_kg_m3` | kg/m³ | ✓ | ISA model |

### 7.2 Assessment for Sensor Simulation

✅ **Sufficient for basic sensor simulation:**
- Regular 0.1s timestamps (10 Hz)
- All classic IMU/barometer/GPS quantities present
- Clear units in column names (`_m`, `_mps`, `_mps2`, `_kg`, `_n`, `_kg_m3`)
- Flight phase context for event-triggered logging

⚠️ **Gaps for realistic avionics:**
- No angular rates (gyro), attitude (quaternion/Euler)
- No magnetometer data
- No GPS position (lat/lon/alt), only altitude
- No sensor noise, bias, or drift models
- Drag force is magnitude only (no vector components)
- No timestamp metadata (sample rate, sync source)
- No packet structure for radio telemetry

### 7.3 Required Enhancements for V2 Avionics

| Enhancement | Purpose |
|-------------|---------|
| Add attitude state (quaternion) | IMU simulation, guidance |
| Add angular velocity | Gyro simulation |
| Add 3D position/velocity | GPS simulation |
| Add magnetic field vector | Magnetometer simulation |
| Sensor noise/bias/drift models | Realistic sensor simulation |
| Telemetry packet encoder | Radio downlink simulation |
| Event timestamps with microsecond precision | Flight computer event logging |
| Health/status bitfields | Subsystem monitoring |

---

## 8. Module Reusability Assessment for V2

| Module | Reusable? | Changes Needed |
|--------|-----------|----------------|
| `atmosphere.py` | ✅ YES | None - excellent ISA model |
| `propulsion.py` | ✅ YES | None - good thrust curve |
| `physics.py` | ✅ YES | None - clean force functions |
| `rocket.py` | ⚠️ PARTIAL | Add multi-stage, stage separation events |
| `flight_phases.py` | ✅ YES | None - solid state machine |
| `telemetry.py` | ⚠️ PARTIAL | Add schema, streaming, binary recording |
| `simulator.py` | ⚠️ PARTIAL | Add callback hooks, event emission |
| `mission.py` | ✅ YES | Add avionics mission modes |
| `report_generator.py` | ✅ YES | None |
| `visualization.py` | ✅ YES | None |
| `rocket_library.py` | ✅ YES | None |
| `dashboard/app.py` | ⚠️ PARTIAL | Fix imports, add avionics tabs |
| `vercel-app/lib/simulation.ts` | ❌ REWRITE | Physics divergence - unify with Python |
| `vercel-app/lib/rocket-library.ts` | ✅ YES | Sync data from JSON source |

---

## 9. Summary & Approval Request

### Key Findings

1. **Python engine is solid** - Well-structured, tested, physics-based, with good separation of concerns
2. **Streamlit dashboard is feature-rich** - Mission control, telemetry, analytics, comparison, reports, audio
3. **TypeScript port has physics divergence** - Simplified models that will produce different results
4. **No telemetry schema** - Critical gap for avionics integration
5. **Single-stage limitation** - Must be addressed for realistic vehicle simulation
6. **Duplicated logic** - Propellant fraction, vehicle data, phase detection exist in both Python and TS
7. **Import fragility** - Missing `__init__.py`, sys.path hacks in dashboard

### Ready for V2 Implementation

The codebase is **ready for V2 avionics integration** with the following conditions:
- Do not modify physics engine during audit (confirmed - no changes made)
- Do not delete existing features (confirmed)
- Foundation fixes (Phase 1) should be done first to enable clean integration

### Request for Approval

Please approve proceeding with **Phase 1: Foundation** implementation:

1. Add `src/__init__.py` 
2. Fix dashboard imports (remove sys.path hack)
3. Create telemetry schema with units/metadata
4. Sync vehicle library data (9 vehicles in vercel-app)
5. Extract shared constants (propellant fraction)

Once approved, I will implement Phase 1 and provide a summary before proceeding to Phase 2.