"""PDF mission report generation using ReportLab."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_mission_report(
    output_path: str,
    mission_summary: dict[str, Any],
    rocket_spec: dict[str, Any],
    plot_paths: dict[str, str],
) -> None:
    document = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Rocket Flight Simulator and Mission Analysis Tool", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Mission Report", styles["Heading2"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Rocket Specifications", styles["Heading2"]))
    spec_table = Table([[key.replace("_", " ").title(), str(value)] for key, value in rocket_spec.items()], hAlign="LEFT")
    spec_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
    story.append(spec_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Mission Summary", styles["Heading2"]))
    summary_table = Table([[key.replace("_", " ").title(), f"{value:.3f}" if isinstance(value, float) else str(value)] for key, value in mission_summary.items()], hAlign="LEFT")
    summary_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke)]))
    story.append(summary_table)
    story.append(PageBreak())

    for title, plot_path in plot_paths.items():
        image_file = Path(plot_path)
        if image_file.exists():
            story.append(Paragraph(title.replace("_", " ").title(), styles["Heading2"]))
            story.append(Image(str(image_file), width=500, height=275))
            story.append(Spacer(1, 12))

    document.build(story)
