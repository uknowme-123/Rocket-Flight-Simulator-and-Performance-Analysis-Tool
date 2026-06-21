# Rocket-Flight-Simulator-and-Performance-Analysis-Tool

A Python-based aerospace simulation tool for modelling rocket flight dynamics, trajectory analysis, altitude prediction, and mission performance evaluation.

## Project Overview

A physics-based Python project that simulates the vertical flight of a single-stage rocket, records telemetry, generates engineering plots, and produces a PDF mission report. It is designed as a portfolio-ready aerospace engineering project for first-year ECE students exploring launch vehicles, avionics, telemetry, and flight dynamics.

This simulator models the major phases of a rocket launch:

- Launch phase
- Powered flight
- Coasting phase
- Apogee
- Descent and landing

The engine calculates thrust, gravity, drag, velocity, altitude, acceleration, fuel consumption, apogee, and flight duration. The output is saved as telemetry data, visual plots, and a mission report.

## Features

- Physics-based vertical rocket simulation
- OOP rocket model with fuel tracking
- Telemetry logging to CSV
- Mission summary metrics
- Matplotlib engineering plots
- PDF report generation with ReportLab
- Streamlit dashboard for interactive analysis
- Unit tests for core physics and simulation logic

## Folder Structure

```text
rocket-flight-simulator/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py
│   ├── rocket.py
│   ├── physics.py
│   ├── simulator.py
│   ├── telemetry.py
│   ├── mission.py
│   ├── visualization.py
│   ├── report_generator.py
│   └── config.py
├── dashboard/
│   └── app.py
├── data/
│   ├── rocket_parameters.json
│   ├── sample_mission.json
│   └── simulation_output.csv
├── reports/
│   ├── mission_report.pdf
│   └── mission_summary.txt
├── screenshots/
│   ├── altitude_plot.png
│   ├── velocity_plot.png
│   └── acceleration_plot.png
├── docs/
├── tests/
└── assets/
```

## Physics Equations

The simulator uses the following equations:

### Gravity

$$F_g = m g$$

### Drag

$$F_d = \frac{1}{2} \rho C_d A V^2$$

### Newton's Second Law

$$F = ma$$

### Net Force

$$F_{net} = F_{thrust} - F_g - F_d$$

## Default Rocket Parameters

- Dry Mass: 3 kg
- Fuel Mass: 2 kg
- Total Mass: 5 kg
- Thrust: 300 N
- Burn Time: 8 s
- Drag Coefficient: 0.45
- Cross Section Area: 0.02 m²

## Installation Steps

1. Install Python 3.12 or newer.
2. Clone or open this repository in VS Code.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage Instructions

### Run the simulator

```bash
python src/main.py
```

This generates:

- `data/simulation_output.csv`
- `reports/mission_summary.txt`
- `reports/mission_report.pdf`
- `screenshots/altitude_plot.png`
- `screenshots/velocity_plot.png`
- `screenshots/acceleration_plot.png`

### Launch the dashboard

```bash
streamlit run dashboard/app.py
```

## Screenshots

The project generates engineering plots in the `screenshots/` folder. The dashboard can also be captured and saved as `screenshots/dashboard.png`.

## Testing

Run the unit tests with:

```bash
pytest
```

The tests cover:

- Gravity calculations
- Drag calculations
- Net force calculations
- Rocket mass updates
- Simulation execution

## Future Roadmap

- Version 2: Multi-stage rockets
- Version 3: Telemetry dashboard
- Version 4: ESP32 integration
- Version 5: PID guidance and control
- Version 6: Launch vehicle mission planner
- Version 7: Satellite launch simulation

## Repository Topics

- python
- aerospace
- rocket-simulation
- flight-dynamics
- ece
- space-tech
- avionics
- physics
- engineering
- trajectory-analysis

## Author Information

- Author: Add your name here
- Field: Aerospace engineering, ECE, avionics, and embedded systems

```text
Rocket-Flight-Simulator-and-Performance-Analysis-Tool/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
├── docs/
├── screenshots/
└── data/
```

## Next Steps

- Add simulator code under `src/`.
- Document algorithms, assumptions, and formulas in `docs/`.
- Store plots and UI captures in `screenshots/`.
- Keep sample inputs and outputs in `data/`.
- Add Python dependencies to `requirements.txt` when the code is ready.
