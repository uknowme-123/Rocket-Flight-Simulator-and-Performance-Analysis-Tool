"""Streamlit Mission Control Center for the rocket flight simulator."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mission import analyze_mission, build_phase_timeline
from report_generator import generate_mission_report
from rocket import Rocket
from simulator import RocketSimulator
from visualization import generate_plots

from audio_system import (
    initialize_audio_state,
    render_alert,
    render_audio_controls,
    reset_audio_events,
    trigger_audio,
)
from ui_components import (
    CHART_SPECS,
    MISSION_CONTROL_CSS,
    MISSION_PRESETS,
    build_live_telemetry_chart,
    build_telemetry_chart,
    format_number,
    metric_card,
    phase_badge,
    subsystem_card,
)


REPORTS_DIR = ROOT_DIR / "reports"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
REPORT_PATH = REPORTS_DIR / "mission_report.pdf"

CONFIG_KEYS = (
    "dry_mass",
    "fuel_mass",
    "thrust",
    "burn_time",
    "drag_coefficient",
    "cross_sectional_area",
)


def initialize_session_state() -> None:
    """Initialize dashboard state for mission configuration and playback."""

    nominal_preset = "Nominal Sounding Flight"
    st.session_state.setdefault("selected_preset", nominal_preset)
    st.session_state.setdefault("mission_package", None)
    st.session_state.setdefault("telemetry_frame", 0)
    st.session_state.setdefault("countdown_seconds", 5)
    st.session_state.setdefault("mission_status", "STANDBY")
    st.session_state.setdefault("active_preset_name", nominal_preset)
    st.session_state.setdefault("live_stream_enabled", False)
    st.session_state.setdefault("stream_step", 4)
    st.session_state.setdefault("stream_interval_s", 0.18)
    initialize_audio_state()

    for key, value in MISSION_PRESETS[nominal_preset].items():
        st.session_state.setdefault(f"cfg_{key}", value)


def load_preset(preset_name: str) -> None:
    """Load a mission preset into Streamlit widget state."""

    for key, value in MISSION_PRESETS[preset_name].items():
        st.session_state[f"cfg_{key}"] = value
    st.session_state.active_preset_name = preset_name
    st.session_state.mission_status = "PRESET LOADED"


def collect_configuration() -> dict[str, float]:
    """Return the current sidebar rocket configuration."""

    return {key: float(st.session_state[f"cfg_{key}"]) for key in CONFIG_KEYS}


def run_mission(parameters: dict[str, float]) -> dict[str, Any]:
    """Run the simulator and build all dashboard mission products."""

    rocket = Rocket(
        dry_mass=parameters["dry_mass"],
        fuel_mass=parameters["fuel_mass"],
        thrust=parameters["thrust"],
        burn_time=parameters["burn_time"],
        drag_coefficient=parameters["drag_coefficient"],
        cross_sectional_area=parameters["cross_sectional_area"],
    )
    result = RocketSimulator(rocket).run()
    telemetry = result.telemetry
    summary = analyze_mission(telemetry)
    phase_timeline = build_phase_timeline(telemetry)
    plot_paths = generate_plots(telemetry, str(SCREENSHOTS_DIR))
    warnings = evaluate_mission_warnings(parameters, telemetry, summary)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generate_mission_report(
        output_path=str(REPORT_PATH),
        mission_summary=summary,
        rocket_spec=parameters,
        plot_paths=plot_paths,
        phase_timeline=phase_timeline,
    )

    return {
        "telemetry": telemetry,
        "summary": summary,
        "phase_timeline": phase_timeline,
        "plot_paths": plot_paths,
        "parameters": parameters,
        "report_path": REPORT_PATH,
        "warnings": warnings,
    }


def evaluate_mission_warnings(
    parameters: dict[str, float],
    telemetry: pd.DataFrame,
    summary: dict[str, Any],
) -> list[str]:
    """Return mission safety warnings for dashboard alerting."""

    warnings: list[str] = []
    if parameters["fuel_mass"] <= 0.0:
        warnings.append("Invalid mission parameter: propellant mass is zero.")
    if parameters["thrust"] <= 0.0:
        warnings.append("Invalid mission parameter: peak thrust is zero.")
    if telemetry.empty:
        warnings.append("Simulation instability: telemetry stream is empty.")
        return warnings
    if telemetry[["altitude_m", "velocity_mps", "acceleration_mps2"]].isna().any().any():
        warnings.append("Simulation instability: non-numeric telemetry detected.")
    if summary["maximum_acceleration_mps2"] > 80.0:
        warnings.append("Excessive acceleration exceeds 80 m/s^2 structural limit.")
    if abs(summary["landing_velocity_mps"]) > 20.0:
        warnings.append("Landing velocity exceeds the 20 m/s safe recovery limit.")
    return warnings


def current_sample(mission_package: dict[str, Any] | None) -> pd.Series | None:
    """Return the telemetry row selected by the playback frame."""

    if not mission_package:
        return None

    telemetry = mission_package["telemetry"]
    if telemetry.empty:
        return None

    frame = min(st.session_state.telemetry_frame, len(telemetry) - 1)
    return telemetry.iloc[frame]


def render_sidebar() -> tuple[dict[str, float], bool, bool]:
    """Render the mission configuration sidebar."""

    with st.sidebar:
        st.header("Mission Configuration")
        st.caption("Flight readiness inputs for the vertical launch vehicle.")

        preset_name = st.selectbox(
            "Mission Preset",
            options=list(MISSION_PRESETS.keys()),
            key="selected_preset",
        )

        preset_columns = st.columns(2)
        if preset_columns[0].button("Load Preset", use_container_width=True):
            load_preset(preset_name)
            st.rerun()
        if preset_columns[1].button("Reset Nominal", use_container_width=True):
            load_preset("Nominal Sounding Flight")
            st.rerun()

        st.divider()
        st.subheader("Vehicle Parameters")
        st.number_input("Dry Mass (kg)", min_value=0.1, step=0.1, key="cfg_dry_mass")
        st.number_input("Fuel Mass (kg)", min_value=0.0, step=0.1, key="cfg_fuel_mass")
        st.number_input("Peak Thrust (N)", min_value=0.0, step=5.0, key="cfg_thrust")
        st.number_input("Burn Time (s)", min_value=0.1, step=0.1, key="cfg_burn_time")
        st.number_input(
            "Drag Coefficient",
            min_value=0.0,
            step=0.01,
            key="cfg_drag_coefficient",
        )
        st.number_input(
            "Reference Area (m^2)",
            min_value=0.001,
            step=0.001,
            key="cfg_cross_sectional_area",
        )

        st.divider()
        st.subheader("Launch Sequencer")
        st.slider(
            "Terminal Count Duration (s)",
            min_value=3,
            max_value=10,
            key="countdown_seconds",
        )
        st.select_slider(
            "Telemetry Stream Rate",
            options=[1, 2, 4, 8, 12],
            key="stream_step",
            help="Frames advanced per screen refresh.",
        )
        render_audio_controls()
        launch_requested = st.button(
            "Initiate Countdown",
            type="primary",
            use_container_width=True,
        )
        quick_run_requested = st.button("Run Analysis Only", use_container_width=True)

    return collect_configuration(), launch_requested, quick_run_requested


def render_hero(mission_package: dict[str, Any] | None) -> None:
    """Render the Mission Control hero banner."""

    sample = current_sample(mission_package)
    phase = str(sample["flight_phase"]) if sample is not None else "PRE-LAUNCH"
    status = st.session_state.mission_status
    met = format_number(sample["time_s"], "s") if sample is not None else "0.00 s"
    apogee = "Awaiting simulation"
    if mission_package:
        apogee = format_number(mission_package["summary"]["maximum_altitude_m"], "m")

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-kicker">Launch Vehicle Mission Monitoring Dashboard</div>
            <div class="hero-title">Mission Control Center</div>
            <div class="hero-subtitle">
                Integrated flight dynamics, propulsion telemetry, atmospheric
                drag modeling, and mission performance analytics for a
                single-stage vertical launch profile.
            </div>
            <div class="status-strip">
                <div class="status-pill">
                    <div class="status-label">Mission Status</div>
                    <div class="status-value">{status}</div>
                </div>
                <div class="status-pill">
                    <div class="status-label">Flight Phase</div>
                    <div class="status-value">{phase}</div>
                </div>
                <div class="status-pill">
                    <div class="status-label">MET</div>
                    <div class="status-value">{met}</div>
                </div>
                <div class="status-pill">
                    <div class="status-label">Predicted Apogee</div>
                    <div class="status-value">{apogee}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def perform_countdown(seconds: int) -> None:
    """Render a terminal countdown before executing the mission simulation."""

    countdown_slot = st.empty()
    for remaining in range(seconds, -1, -1):
        callout = "Main engine start" if remaining == 0 else "Terminal count active"
        if remaining > 0:
            trigger_audio("countdown", unique_key=f"countdown_{remaining}", force=True)
        countdown_slot.markdown(
            f"""
            <div class="countdown-display">
                <div class="status-label">{callout}</div>
                <div class="countdown-number">T-{remaining}</div>
                <div class="hero-subtitle">Guidance, telemetry, and range systems nominal.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(1.0)
    countdown_slot.empty()


def render_metric_grid(sample: pd.Series | None) -> None:
    """Render real-time telemetry cards for the selected mission frame."""

    if sample is None:
        st.markdown(
            '<div class="section-panel">Mission telemetry is waiting for launch authorization.</div>',
            unsafe_allow_html=True,
        )
        return

    cards = [
        metric_card("Altitude", format_number(sample["altitude_m"], "m"), "#4dd6ff"),
        metric_card("Velocity", format_number(sample["velocity_mps"], "m/s"), "#f9c74f"),
        metric_card("Acceleration", format_number(sample["acceleration_mps2"], "m/s^2"), "#f94144"),
        metric_card("Vehicle Mass", format_number(sample["mass_kg"], "kg"), "#c084fc"),
        metric_card("Fuel Remaining", format_number(sample["fuel_remaining_kg"], "kg"), "#8cff98"),
        metric_card("Thrust", format_number(sample["thrust_n"], "N"), "#22c55e"),
        metric_card("Drag Force", format_number(sample["drag_force_n"], "N"), "#fb7185"),
        metric_card("Air Density", format_number(sample["air_density_kg_m3"], "kg/m^3", 4), "#38bdf8"),
    ]
    st.markdown(
        '<div class="mission-card-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def subsystem_states(sample: pd.Series | None) -> list[tuple[str, str, str]]:
    """Derive realistic subsystem states from the current telemetry sample."""

    if sample is None:
        return [
            ("Range Safety", "STANDBY", "#94a3b8"),
            ("Guidance", "AWAITING NAV", "#94a3b8"),
            ("Propulsion", "SAFE", "#94a3b8"),
            ("Telemetry Link", "IDLE", "#94a3b8"),
            ("Recovery", "STOWED", "#94a3b8"),
        ]

    phase = str(sample["flight_phase"])
    thrust = float(sample["thrust_n"])
    altitude = float(sample["altitude_m"])

    propulsion_state = "BURN ACTIVE" if thrust > 0.0 else "SHUTDOWN"
    guidance_state = "ASCENT TRACK" if sample["velocity_mps"] >= 0.0 else "DESCENT TRACK"
    recovery_state = "ARMED" if phase in {"DESCENT", "LANDING"} else "STOWED"
    range_state = "GREEN" if altitude >= 0.0 else "HOLD"

    return [
        ("Range Safety", range_state, "#22c55e"),
        ("Guidance", guidance_state, "#38bdf8"),
        ("Propulsion", propulsion_state, "#f59e0b" if thrust > 0.0 else "#94a3b8"),
        ("Telemetry Link", "LOCKED", "#22c55e"),
        ("Recovery", recovery_state, "#c084fc" if recovery_state == "ARMED" else "#94a3b8"),
    ]


def mission_events(telemetry: pd.DataFrame, frame: int) -> list[str]:
    """Build a mission event log up to the selected telemetry frame."""

    active = telemetry.iloc[: frame + 1]
    events = ["T-00.00 | Launch sequencer armed"]
    previous_phase = None

    for _, row in active.iterrows():
        phase = str(row["flight_phase"])
        if phase != previous_phase:
            events.append(f"T+{row['time_s']:05.2f} | Phase transition: {phase}")
            previous_phase = phase

    powered = active[active["thrust_n"] > 0.0]
    if not powered.empty:
        burnout_time = powered["time_s"].iloc[-1]
        if active["thrust_n"].iloc[-1] <= 0.0:
            events.append(f"T+{burnout_time:05.2f} | Motor burnout confirmed")

    if "APOGEE" in set(active["flight_phase"]):
        apogee_row = active.loc[active["altitude_m"].idxmax()]
        events.append(f"T+{apogee_row['time_s']:05.2f} | Apogee reached")

    if str(active["flight_phase"].iloc[-1]) == "LANDING":
        events.append(f"T+{active['time_s'].iloc[-1]:05.2f} | Touchdown detected")

    return events[-9:]


def render_subsystem_panel(sample: pd.Series | None) -> None:
    """Render subsystem health cards."""

    cards = [subsystem_card(label, state, color) for label, state, color in subsystem_states(sample)]
    st.markdown(
        '<div class="subsystem-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def render_playback_controls(mission_package: dict[str, Any]) -> None:
    """Render telemetry playback controls for live feed inspection."""

    telemetry = mission_package["telemetry"]
    max_frame = len(telemetry) - 1
    st.session_state.telemetry_frame = min(st.session_state.telemetry_frame, max_frame)
    selected_frame = st.slider(
        "Telemetry Playback Frame",
        min_value=0,
        max_value=max_frame,
        value=st.session_state.telemetry_frame,
    )
    st.session_state.telemetry_frame = selected_frame

    control_columns = st.columns(5)
    if control_columns[0].button("Go Live", use_container_width=True):
        st.session_state.live_stream_enabled = True
        st.rerun()
    if control_columns[1].button("Hold", use_container_width=True):
        st.session_state.live_stream_enabled = False
        st.rerun()
    if control_columns[2].button("Reset Feed", use_container_width=True):
        st.session_state.live_stream_enabled = False
        st.session_state.telemetry_frame = 0
        st.rerun()
    if control_columns[3].button("Step +1", use_container_width=True):
        st.session_state.live_stream_enabled = False
        st.session_state.telemetry_frame = min(max_frame, st.session_state.telemetry_frame + 1)
        st.rerun()
    if control_columns[4].button("Landing", use_container_width=True):
        st.session_state.live_stream_enabled = False
        st.session_state.telemetry_frame = max_frame
        st.rerun()


def render_live_feed(mission_package: dict[str, Any] | None) -> None:
    """Render a live-style mission event and telemetry feed."""

    if not mission_package:
        st.info("No mission run loaded. Configure the vehicle and initiate countdown.")
        return

    telemetry = mission_package["telemetry"]
    frame = min(st.session_state.telemetry_frame, len(telemetry) - 1)
    sample = telemetry.iloc[frame]
    feed_window = telemetry.iloc[max(0, frame - 9) : frame + 1]

    if st.session_state.live_stream_enabled:
        st.markdown(
            '<div class="live-indicator"><span class="live-dot"></span>Live telemetry acquisition</div>',
            unsafe_allow_html=True,
        )
    st.markdown(phase_badge(str(sample["flight_phase"])), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="telemetry-line">
            MET {sample['time_s']:.2f}s | ALT {sample['altitude_m']:.2f} m |
            VEL {sample['velocity_mps']:.2f} m/s | THR {sample['thrust_n']:.2f} N
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(feed_window, use_container_width=True, height=270)


def dispatch_sample_events(sample: pd.Series, mission_package: dict[str, Any]) -> None:
    """Trigger one-shot audio and alert banners for the current sample."""

    phase = str(sample["flight_phase"])
    phase_events = {
        "LIFTOFF": ("launch", "🚀 LIFTOFF CONFIRMED"),
        "POWERED_ASCENT": ("engine_burn", "Powered ascent engine burn active"),
        "APOGEE": ("apogee", "🎯 APOGEE REACHED"),
        "DESCENT": ("descent", "⬇ DESCENT PHASE INITIATED"),
        "LANDING": ("landing", "🛬 VEHICLE RECOVERED"),
    }

    if phase in phase_events:
        event_name, message = phase_events[phase]
        if trigger_audio(event_name):
            render_alert(event_name, message)

    if phase == "LANDING" and trigger_audio("mission_complete"):
        render_alert("mission_complete", "✅ MISSION SUCCESSFULLY COMPLETED")

    for index, warning in enumerate(mission_package.get("warnings", [])):
        if warning.startswith("Landing velocity") and phase != "LANDING":
            continue
        if warning.startswith("Excessive acceleration") and abs(sample["acceleration_mps2"]) <= 80.0:
            continue
        if trigger_audio("warning", unique_key=f"warning_{index}"):
            render_alert("warning", warning)


def render_event_log(mission_package: dict[str, Any] | None) -> None:
    """Render mission events up to the current telemetry frame."""

    if not mission_package:
        return

    telemetry = mission_package["telemetry"]
    frame = min(st.session_state.telemetry_frame, len(telemetry) - 1)
    rows = "".join(f'<div class="event-row">{event}</div>' for event in mission_events(telemetry, frame))
    st.markdown(f'<div class="event-log">{rows}</div>', unsafe_allow_html=True)


def render_live_profile(mission_package: dict[str, Any] | None) -> None:
    """Render live-revealed altitude and velocity traces."""

    if not mission_package:
        return

    telemetry = mission_package["telemetry"]
    frame = min(st.session_state.telemetry_frame, len(telemetry) - 1)
    left_column, right_column = st.columns(2)
    with left_column:
        st.altair_chart(
            build_live_telemetry_chart(telemetry, "altitude_m", "Altitude", "m", "#4dd6ff", frame),
            use_container_width=True,
        )
    with right_column:
        st.altair_chart(
            build_live_telemetry_chart(telemetry, "velocity_mps", "Velocity", "m/s", "#f9c74f", frame),
            use_container_width=True,
        )


def render_mission_control_tab(mission_package: dict[str, Any] | None) -> None:
    """Render the main mission-control tab."""

    sample = current_sample(mission_package)
    if sample is not None and mission_package:
        dispatch_sample_events(sample, mission_package)

    render_metric_grid(sample)
    st.subheader("Subsystem Health")
    render_subsystem_panel(sample)

    if mission_package:
        render_playback_controls(mission_package)

        telemetry = mission_package["telemetry"]
        progress = st.session_state.telemetry_frame / max(len(telemetry) - 1, 1)
        st.progress(progress, text=f"Mission Data Stream {progress * 100:.1f}%")
        render_live_profile(mission_package)

    st.subheader("Live Telemetry Feed")
    left_column, right_column = st.columns([1.25, 1.0])
    with left_column:
        render_live_feed(mission_package)
    with right_column:
        render_event_log(mission_package)


def render_telemetry_tab(mission_package: dict[str, Any] | None) -> None:
    """Render full telemetry tables and CSV export."""

    if not mission_package:
        st.info("Telemetry archive will populate after a mission simulation.")
        return

    telemetry = mission_package["telemetry"]
    csv_data = telemetry.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Mission Telemetry CSV",
        data=csv_data,
        file_name="mission_telemetry.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Flight Phase Timeline")
    st.dataframe(pd.DataFrame(mission_package["phase_timeline"]), use_container_width=True)

    st.subheader("Telemetry Archive")
    st.dataframe(telemetry, use_container_width=True, height=520)


def render_performance_tab(mission_package: dict[str, Any] | None) -> None:
    """Render interactive mission performance charts."""

    if not mission_package:
        st.info("Performance analytics are available after launch simulation.")
        return

    telemetry = mission_package["telemetry"]
    chart_names = list(CHART_SPECS.keys())
    for left_name, right_name in zip(chart_names[0::2], chart_names[1::2]):
        left_column, right_column = st.columns(2)
        with left_column:
            column, title, unit, color = CHART_SPECS[left_name]
            st.altair_chart(
                build_telemetry_chart(telemetry, column, title, unit, color),
                use_container_width=True,
            )
        with right_column:
            column, title, unit, color = CHART_SPECS[right_name]
            st.altair_chart(
                build_telemetry_chart(telemetry, column, title, unit, color),
                use_container_width=True,
            )

    remaining_chart = chart_names[-1]
    column, title, unit, color = CHART_SPECS[remaining_chart]
    st.altair_chart(
        build_telemetry_chart(telemetry, column, title, unit, color),
        use_container_width=True,
    )


def render_report_tab(mission_package: dict[str, Any] | None) -> None:
    """Render mission analytics and report download support."""

    if not mission_package:
        st.info("Mission report package will be generated after simulation.")
        return

    summary = mission_package["summary"]
    parameters = mission_package["parameters"]

    summary_columns = st.columns(4)
    summary_columns[0].metric("Maximum Altitude", format_number(summary["maximum_altitude_m"], "m"))
    summary_columns[1].metric("Maximum Velocity", format_number(summary["maximum_velocity_mps"], "m/s"))
    summary_columns[2].metric("Apogee Time", format_number(summary["apogee_time_s"], "s"))
    summary_columns[3].metric("Landing Velocity", format_number(summary["landing_velocity_mps"], "m/s"))

    st.subheader("Mission Summary")
    st.dataframe(pd.DataFrame([summary]), use_container_width=True)

    st.subheader("Launch Vehicle Parameters")
    st.dataframe(pd.DataFrame([parameters]), use_container_width=True)

    report_path = mission_package["report_path"]
    if report_path.exists():
        st.download_button(
            "Download Mission Report PDF",
            data=report_path.read_bytes(),
            file_name="mission_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.warning("PDF report was not found on disk.")


def main() -> None:
    """Run the Streamlit Mission Control Center."""

    st.set_page_config(
        page_title="Mission Control Center",
        page_icon=":rocket:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_session_state()
    st.markdown(MISSION_CONTROL_CSS, unsafe_allow_html=True)

    configuration, launch_requested, quick_run_requested = render_sidebar()
    render_hero(st.session_state.mission_package)

    if launch_requested:
        reset_audio_events()
        st.session_state.mission_status = "TERMINAL COUNT"
        perform_countdown(int(st.session_state.countdown_seconds))
        st.session_state.mission_package = run_mission(configuration)
        st.session_state.telemetry_frame = 0
        st.session_state.live_stream_enabled = True
        st.session_state.mission_status = "LIVE TELEMETRY"
        st.rerun()

    if quick_run_requested:
        reset_audio_events()
        st.session_state.mission_package = run_mission(configuration)
        st.session_state.telemetry_frame = len(st.session_state.mission_package["telemetry"]) - 1
        st.session_state.live_stream_enabled = False
        st.session_state.mission_status = "ANALYSIS COMPLETE"
        st.rerun()

    mission_tab, telemetry_tab, analytics_tab, report_tab = st.tabs(
        ["Mission Control", "Telemetry", "Performance Analytics", "Mission Report"]
    )

    with mission_tab:
        render_mission_control_tab(st.session_state.mission_package)

    with telemetry_tab:
        render_telemetry_tab(st.session_state.mission_package)

    with analytics_tab:
        render_performance_tab(st.session_state.mission_package)

    with report_tab:
        render_report_tab(st.session_state.mission_package)

    if st.session_state.live_stream_enabled and st.session_state.mission_package:
        telemetry = st.session_state.mission_package["telemetry"]
        max_frame = len(telemetry) - 1
        if st.session_state.telemetry_frame >= max_frame:
            st.session_state.live_stream_enabled = False
            st.session_state.mission_status = "MISSION COMPLETE"
        else:
            st.session_state.telemetry_frame = min(
                max_frame,
                st.session_state.telemetry_frame + int(st.session_state.stream_step),
            )
            time.sleep(float(st.session_state.stream_interval_s))
            st.rerun()


if __name__ == "__main__":
    main()
