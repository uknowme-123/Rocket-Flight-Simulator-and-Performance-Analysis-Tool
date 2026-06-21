"""Streamlit dashboard for the rocket flight simulator."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mission import analyze_mission
from rocket import Rocket
from simulator import RocketSimulator
from visualization import generate_plots


st.set_page_config(page_title="Rocket Flight Simulator", page_icon="🚀", layout="wide")

st.title("Rocket Flight Simulator and Mission Analysis Tool")
st.caption("Aerospace-themed mission analysis dashboard for a vertical launch simulation.")

with st.sidebar:
    st.header("Rocket Inputs")
    dry_mass = st.number_input("Dry Mass (kg)", min_value=0.1, value=3.0, step=0.1)
    fuel_mass = st.number_input("Fuel Mass (kg)", min_value=0.0, value=2.0, step=0.1)
    thrust = st.number_input("Thrust (N)", min_value=0.0, value=300.0, step=5.0)
    burn_time = st.number_input("Burn Time (s)", min_value=0.1, value=8.0, step=0.1)
    drag_coefficient = st.number_input("Drag Coefficient", min_value=0.0, value=0.45, step=0.01)
    cross_sectional_area = st.number_input("Cross Sectional Area (m²)", min_value=0.001, value=0.02, step=0.001)

rocket = Rocket(dry_mass, fuel_mass, thrust, burn_time, drag_coefficient, cross_sectional_area)

if st.button("Run Simulation", type="primary"):
    simulator = RocketSimulator(rocket)
    result = simulator.run()
    telemetry = result.telemetry
    summary = analyze_mission(telemetry)
    plots = generate_plots(telemetry, str(ROOT_DIR / "screenshots"))

    latest = telemetry.iloc[-1]
    metric_columns = st.columns(3)
    metric_columns[0].metric("Current Altitude (m)", f"{latest['altitude_m']:.2f}")
    metric_columns[1].metric("Current Velocity (m/s)", f"{latest['velocity_mps']:.2f}")
    metric_columns[2].metric("Current Acceleration (m/s²)", f"{latest['acceleration_mps2']:.2f}")

    summary_columns = st.columns(3)
    summary_columns[0].metric("Maximum Altitude (m)", f"{summary['maximum_altitude_m']:.2f}")
    summary_columns[1].metric("Maximum Velocity (m/s)", f"{summary['maximum_velocity_mps']:.2f}")
    summary_columns[2].metric("Flight Duration (s)", f"{summary['flight_duration_s']:.2f}")

    st.subheader("Telemetry Data")
    st.dataframe(telemetry, use_container_width=True)

    st.subheader("Engineering Charts")
    st.image(plots["altitude_plot"], caption="Altitude vs Time", use_container_width=True)
    st.image(plots["velocity_plot"], caption="Velocity vs Time", use_container_width=True)
    st.image(plots["acceleration_plot"], caption="Acceleration vs Time", use_container_width=True)

else:
    st.info("Configure the rocket parameters in the sidebar and run the simulation.")
