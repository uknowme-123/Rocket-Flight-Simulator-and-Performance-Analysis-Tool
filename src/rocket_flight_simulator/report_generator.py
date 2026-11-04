"""PDF mission report generation using ReportLab."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _format_value(value: Any) -> str:
    """Format report table values for engineering readability."""

    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _styled_table(rows: list[list[str]], background: colors.Color) -> Table:
    """Build a compact table with a consistent report style."""

    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), background),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def generate_mission_report(
    output_path: str,
    mission_summary: dict[str, Any],
    rocket_spec: dict[str, Any],
    plot_paths: dict[str, str],
    phase_timeline: list[dict[str, Any]] | None = None,
    vehicle_name: str = "Custom Rocket",
    vehicle_info: dict[str, Any] | None = None,
) -> None:
    """Generate a professional PDF mission report."""

    document = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Rocket Flight Simulator and Mission Analysis Tool", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Mission Report", styles["Heading2"]))
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "Vehicle specifications are simplified and adapted for educational "
            "simulation. The simulator does not reproduce real-world launch performance.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Mission Summary", styles["Heading2"]))
    story.append(
        Paragraph(
            "This report summarizes a one-dimensional vertical launch using "
            "variable thrust, propellant mass depletion, altitude-dependent "
            "atmospheric density, and velocity-opposed aerodynamic drag.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))

    summary_context = [["Attribute", "Value"], ["Selected Launch Vehicle", vehicle_name]]
    if vehicle_info:
        summary_context.extend(
            [
                ["Country", _format_value(vehicle_info.get("country", ""))],
                ["Organization", _format_value(vehicle_info.get("organization", ""))],
            ]
        )
    story.append(_styled_table(summary_context, colors.whitesmoke))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Vehicle Specifications", styles["Heading2"]))
    if vehicle_info:
        vehicle_rows = [["Parameter", "Value"]]
        vehicle_rows.extend(
            [
                ["Rocket Name", vehicle_name],
                ["Country", _format_value(vehicle_info.get("country", ""))],
                ["Organization", _format_value(vehicle_info.get("organization", ""))],
                ["Height (m)", _format_value(vehicle_info.get("height_m", ""))],
                ["Diameter (m)", _format_value(vehicle_info.get("diameter_m", ""))],
                ["Stages", _format_value(vehicle_info.get("stages", ""))],
                ["Liftoff Mass (kg)", _format_value(vehicle_info.get("liftoff_mass_kg", ""))],
                ["Payload LEO (kg)", _format_value(vehicle_info.get("payload_leo_kg", ""))],
                ["Thrust (kN)", _format_value(vehicle_info.get("thrust_kn", ""))],
                ["Burn Time (s)", _format_value(vehicle_info.get("burn_time_s", ""))],
            ]
        )
        story.append(_styled_table(vehicle_rows, colors.lightgrey))
    else:
        story.append(
            Paragraph(
                "Custom Rocket mode is active. Vehicle-level catalog data was not selected.",
                styles["BodyText"],
            )
        )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Vehicle Description", styles["Heading2"]))
    if vehicle_info:
        story.append(
            Paragraph(
                _format_value(vehicle_info.get("description", "No description available.")),
                styles["BodyText"],
            )
        )
    else:
        story.append(Paragraph("User-defined custom vehicle configuration.", styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Rocket Parameters", styles["Heading2"]))
    spec_rows = [["Parameter", "Value"]]
    spec_rows.extend(
        [key.replace("_", " ").title(), _format_value(value)]
        for key, value in rocket_spec.items()
    )
    story.append(_styled_table(spec_rows, colors.lightgrey))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Atmospheric Model", styles["Heading2"]))
    story.append(
        Paragraph(
            "Density follows a simplified International Standard Atmosphere: "
            "1.225 kg/m^3 at sea level, cooling through the troposphere, then "
            "an isothermal lower-stratosphere approximation above 11 km.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))

    if phase_timeline:
        story.append(Paragraph("Flight Phase Timeline", styles["Heading2"]))
        phase_rows = [["Phase", "Start (s)", "End (s)", "Duration (s)"]]
        phase_rows.extend(
            [
                str(item["flight_phase"]),
                _format_value(item["start_time_s"]),
                _format_value(item["end_time_s"]),
                _format_value(item["duration_s"]),
            ]
            for item in phase_timeline
        )
        story.append(_styled_table(phase_rows, colors.whitesmoke))
        story.append(Spacer(1, 12))

    story.append(Paragraph("Performance Metrics", styles["Heading2"]))
    summary_rows = [["Metric", "Value"]]
    summary_rows.extend(
        [key.replace("_", " ").title(), _format_value(value)]
        for key, value in mission_summary.items()
    )
    story.append(_styled_table(summary_rows, colors.whitesmoke))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Engineering Conclusions", styles["Heading2"]))
    story.append(
        Paragraph(
            "The upgraded simulation captures the dominant first-order effects "
            "for vertical flight analysis: decreasing density reduces drag at "
            "altitude, thrust tail-off shapes burnout acceleration, and mass "
            "depletion improves the predicted acceleration history.",
            styles["BodyText"],
        )
    )
    story.append(PageBreak())

    for title, plot_path in plot_paths.items():
        image_file = Path(plot_path)
        if image_file.exists():
            story.append(Paragraph(title.replace("_", " ").title(), styles["Heading2"]))
            story.append(Image(str(image_file), width=500, height=275))
            story.append(Spacer(1, 12))

    document.build(story)
