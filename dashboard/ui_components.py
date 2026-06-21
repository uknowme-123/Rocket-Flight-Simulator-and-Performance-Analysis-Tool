"""Reusable dashboard UI configuration and chart helpers."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd


MISSION_PRESETS: dict[str, dict[str, float]] = {
    "Nominal Sounding Flight": {
        "dry_mass": 3.0,
        "fuel_mass": 2.0,
        "thrust": 300.0,
        "burn_time": 8.0,
        "drag_coefficient": 0.45,
        "cross_sectional_area": 0.02,
    },
    "High-Thrust Qualification": {
        "dry_mass": 3.4,
        "fuel_mass": 2.4,
        "thrust": 420.0,
        "burn_time": 7.5,
        "drag_coefficient": 0.42,
        "cross_sectional_area": 0.022,
    },
    "Low-Drag Research Vehicle": {
        "dry_mass": 2.8,
        "fuel_mass": 1.8,
        "thrust": 310.0,
        "burn_time": 8.5,
        "drag_coefficient": 0.30,
        "cross_sectional_area": 0.016,
    },
    "Heavy Payload Demonstrator": {
        "dry_mass": 5.0,
        "fuel_mass": 2.8,
        "thrust": 450.0,
        "burn_time": 9.0,
        "drag_coefficient": 0.50,
        "cross_sectional_area": 0.028,
    },
}


CHART_SPECS: dict[str, tuple[str, str, str, str]] = {
    "Altitude": ("altitude_m", "Altitude", "m", "#4dd6ff"),
    "Velocity": ("velocity_mps", "Velocity", "m/s", "#f9c74f"),
    "Acceleration": ("acceleration_mps2", "Acceleration", "m/s^2", "#f94144"),
    "Thrust": ("thrust_n", "Thrust", "N", "#8cff98"),
    "Mass": ("mass_kg", "Vehicle Mass", "kg", "#c084fc"),
}


PHASE_COLORS: dict[str, str] = {
    "PRE-LAUNCH": "#94a3b8",
    "LIFTOFF": "#38bdf8",
    "POWERED_ASCENT": "#22c55e",
    "COASTING": "#f59e0b",
    "APOGEE": "#e879f9",
    "DESCENT": "#fb7185",
    "LANDING": "#a3e635",
}


MISSION_CONTROL_CSS = """
<style>
:root {
    --space-bg: #050816;
    --panel-bg: rgba(13, 22, 41, 0.92);
    --panel-border: rgba(125, 211, 252, 0.22);
    --text-primary: #e5f0ff;
    --text-muted: #95a3b8;
    --accent-cyan: #38bdf8;
    --accent-green: #22c55e;
    --accent-amber: #f59e0b;
    --accent-red: #fb7185;
}

.stApp {
    background:
        repeating-linear-gradient(90deg, rgba(125, 211, 252, 0.04) 0 1px, transparent 1px 72px),
        linear-gradient(135deg, #050816 0%, #08111f 48%, #020617 100%);
    color: var(--text-primary);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.1rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111f 0%, #020617 100%);
    border-right: 1px solid rgba(125, 211, 252, 0.18);
}

[data-testid="stSidebar"] * {
    color: #e5f0ff;
}

div[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(125, 211, 252, 0.18);
    border-radius: 8px;
    padding: 0.75rem 0.9rem;
}

.hero-banner {
    border: 1px solid rgba(125, 211, 252, 0.24);
    border-radius: 8px;
    padding: 1.25rem 1.35rem;
    background:
        linear-gradient(110deg, rgba(15, 23, 42, 0.96), rgba(8, 47, 73, 0.80)),
        repeating-linear-gradient(90deg, rgba(125, 211, 252, 0.07) 0 1px, transparent 1px 54px);
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
    margin-bottom: 1rem;
}

.hero-kicker {
    color: #7dd3fc;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.14rem;
    text-transform: uppercase;
}

.hero-title {
    color: #f8fbff;
    font-size: clamp(2rem, 4vw, 3.4rem);
    font-weight: 800;
    line-height: 1;
    margin: 0.35rem 0 0.45rem;
}

.hero-subtitle {
    color: #b6c7da;
    max-width: 850px;
    font-size: 1rem;
}

.status-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 0.65rem;
    margin-top: 1rem;
}

.status-pill,
.phase-pill,
.telemetry-line {
    border: 1px solid rgba(125, 211, 252, 0.18);
    border-radius: 8px;
    background: rgba(2, 6, 23, 0.44);
    padding: 0.65rem 0.75rem;
}

.status-label,
.card-label {
    color: #95a3b8;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.status-value,
.card-value {
    color: #f8fbff;
    font-size: 1.05rem;
    font-weight: 800;
}

.mission-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.75rem;
    margin: 0.5rem 0 1rem;
}

.mission-card {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 0.9rem;
}

.card-value {
    font-size: 1.45rem;
    margin-top: 0.25rem;
}

.phase-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    font-weight: 800;
    text-transform: uppercase;
}

.phase-dot {
    width: 0.7rem;
    height: 0.7rem;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 16px currentColor;
}

.section-panel {
    background: rgba(15, 23, 42, 0.70);
    border: 1px solid rgba(125, 211, 252, 0.16);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.countdown-display {
    text-align: center;
    border: 1px solid rgba(251, 191, 36, 0.35);
    border-radius: 8px;
    background: rgba(120, 53, 15, 0.28);
    padding: 1rem;
    margin-bottom: 1rem;
}

.countdown-number {
    color: #fbbf24;
    font-size: clamp(2.5rem, 7vw, 5rem);
    font-weight: 900;
    line-height: 1;
}

.telemetry-line {
    font-family: Consolas, monospace;
    color: #cdeafe;
    margin-bottom: 0.45rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(125, 211, 252, 0.14);
    border-radius: 8px;
    padding: 0.45rem 0.8rem;
}

@media (max-width: 760px) {
    .hero-banner {
        padding: 1rem;
    }

    .hero-title {
        font-size: 2rem;
    }
}
</style>
"""


def format_number(value: Any, unit: str = "", digits: int = 2) -> str:
    """Return a compact engineering value with optional units."""

    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        formatted = f"{value:,.{digits}f}"
        return f"{formatted} {unit}".strip()
    return str(value)


def phase_badge(phase: str) -> str:
    """Return HTML for the current flight phase indicator."""

    color = PHASE_COLORS.get(phase, "#94a3b8")
    return (
        f'<div class="phase-pill" style="color:{color};">'
        f'<span class="phase-dot" style="background:{color};"></span>'
        f"{phase}</div>"
    )


def metric_card(label: str, value: str, accent: str = "#38bdf8") -> str:
    """Return HTML for one mission-control metric card."""

    return (
        f'<div class="mission-card" style="border-color:{accent}44;">'
        f'<div class="card-label">{label}</div>'
        f'<div class="card-value" style="color:{accent};">{value}</div>'
        "</div>"
    )


def build_telemetry_chart(
    telemetry: pd.DataFrame,
    column: str,
    title: str,
    unit: str,
    color: str,
) -> alt.Chart:
    """Build an interactive Altair telemetry chart."""

    chart_data = telemetry[["time_s", column, "flight_phase"]].rename(
        columns={"time_s": "met_s", column: "value"}
    )

    return (
        alt.Chart(chart_data)
        .mark_line(color=color, strokeWidth=2.5)
        .encode(
            x=alt.X("met_s:Q", title="Mission Elapsed Time (s)"),
            y=alt.Y("value:Q", title=f"{title} ({unit})"),
            tooltip=[
                alt.Tooltip("met_s:Q", title="Mission Elapsed Time (s)", format=".2f"),
                alt.Tooltip("value:Q", title=f"{title} ({unit})", format=".3f"),
                alt.Tooltip("flight_phase:N", title="Flight Phase"),
            ],
        )
        .properties(height=280)
        .interactive()
    )
