"""Professional in-memory PDF reports for NetLearn Analytics."""

from __future__ import annotations

from datetime import date
from html import escape
from io import BytesIO
from typing import Any

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#0B2A52")
BLUE = colors.HexColor("#087CF0")
LIGHT_BLUE = colors.HexColor("#EAF5FF")
PALE_BLUE = colors.HexColor("#F5F9FD")
MUTED = colors.HexColor("#536A88")
LINE = colors.HexColor("#D9E4EF")

KNOWN_SCALES = {
    "Internet facility in your locality": "Reported 1-5 rating; the publisher describes the direction as very bad to very good",
    "Your interaction in online mode": "Reported 1-5 rating; the publisher describes the direction as very bad to very good",
    "Clearing doubts with faculties in online mode": "Reported 1-5 rating; the publisher describes the direction as very bad to very good",
    "Performance in online": "Numeric online-performance response; values 2-10 are observed in the included dataset",
    "Your level of satisfaction in Online Education": "Ordered satisfaction rating",
}


def _plain(value: Any) -> str:
    """Return XML-safe, printable text without problematic Unicode dashes."""
    if value is None:
        return "Unavailable"
    return escape(str(value).replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-"))


def _number(value: Any, digits: int = 3) -> str:
    if value is None:
        return "Unavailable"
    number = float(value)
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def _p_value(value: Any) -> str:
    if value is None:
        return "Unavailable"
    return "less than 0.001" if float(value) < 0.001 else _number(value, 4)


def _processing_text(
    column: str,
    processing: dict[str, Any],
    *,
    include_known_scale: bool,
) -> str:
    transformation = processing.get("transformation")
    if not transformation:
        processing_text = "Numeric values used without transformation"
        known_scale = KNOWN_SCALES.get(column) if include_known_scale else None
        return f"{known_scale}. {processing_text}" if known_scale else processing_text
    mapping = transformation.get("mapping", {})
    mapping_text = ", ".join(f"{label}={value}" for label, value in mapping.items())
    return f"{transformation.get('description', 'Ordered rating encoding')}: {mapping_text}"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=4 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.5,
            textColor=colors.HexColor("#203B5E"),
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.5,
            textColor=NAVY,
            backColor=LIGHT_BLUE,
            borderColor=LINE,
            borderWidth=0.5,
            borderPadding=8,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.8,
            leading=11,
            textColor=colors.white,
        )
    )
    return styles


def _paragraph(value: Any, style) -> Paragraph:
    return Paragraph(_plain(value), style)


def _table(rows: list[list[Any]], widths: list[float], styles) -> Table:
    converted = []
    for row_index, row in enumerate(rows):
        row_style = styles["TableHeader"] if row_index == 0 else styles["BodySmall"]
        converted.append(
            [cell if isinstance(cell, Paragraph) else _paragraph(cell, row_style) for cell in row]
        )
    table = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_BLUE]),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _distribution_chart(items: list[dict[str, Any]], title: str) -> Drawing:
    """Build a dependency-free compact bar chart from aggregate frequencies."""
    original_count = len(items)
    if original_count > 12:
        indexes = [round(index * (original_count - 1) / 11) for index in range(12)]
        items = [items[index] for index in indexes]
        title = f"{title} (12 of {original_count} values shown)"
    width, height = 480, 155
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 13, title[:85], fontName="Helvetica-Bold", fontSize=9, fillColor=NAVY))
    if not items:
        drawing.add(
            String(
                0,
                height - 35,
                "No visualization data available",
                fontName="Helvetica",
                fontSize=8,
                fillColor=MUTED,
            )
        )
        return drawing
    chart_left, chart_bottom, chart_width, chart_height = 28, 27, 425, 95
    maximum = max(int(item.get("count", 0)) for item in items) or 1
    bar_slot = chart_width / len(items)
    bar_width = min(28, bar_slot * 0.62)
    drawing.add(Rect(chart_left, chart_bottom, chart_width, 0.6, fillColor=LINE, strokeColor=None))
    for index, item in enumerate(items):
        count = int(item.get("count", 0))
        bar_height = (count / maximum) * chart_height
        x = chart_left + index * bar_slot + (bar_slot - bar_width) / 2
        drawing.add(Rect(x, chart_bottom, bar_width, bar_height, fillColor=BLUE, strokeColor=None))
        drawing.add(
            String(
                x + bar_width / 2,
                chart_bottom - 11,
                str(item.get("value", ""))[:8],
                textAnchor="middle",
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=MUTED,
            )
        )
        drawing.add(
            String(
                x + bar_width / 2,
                chart_bottom + bar_height + 3,
                str(count),
                textAnchor="middle",
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=NAVY,
            )
        )
    return drawing


def _page_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9.5 * mm, "NetLearn Analytics - Statistical Analysis Report")
    canvas.drawRightString(A4[0] - 18 * mm, 9.5 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_pdf_report(analysis: dict[str, Any], *, source_type: str) -> BytesIO:
    """Generate a validated-analysis report entirely in memory."""
    buffer = BytesIO()
    styles = _styles()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=19 * mm,
        title="NetLearn Analysis Report",
        author="NetLearn Analytics",
        pageCompression=0,
    )
    dataset = analysis["dataset"]
    selected = analysis["selected_variables"]
    x = selected["connectivity"]
    y = selected["learning_outcome"]
    x_stats = analysis["descriptive_statistics"]["connectivity"]
    y_stats = analysis["descriptive_statistics"]["learning_outcome"]
    correlation = analysis["correlation"]
    regression = analysis["regression"]
    hypothesis = analysis["hypothesis_test"]
    missing = analysis["missing_data"]
    is_default = source_type == "default"
    limitation_lines = [
        "The analysis is observational and statistical association does not establish causation.",
        "Survey responses may contain reporting or response bias.",
        "Reported internet facility quality is not equivalent to measured internet speed in Mbps.",
        "Linear regression is exploratory and assumes numerical rating levels can be treated as approximately equally spaced.",
    ]
    for warning in analysis.get("warnings", []):
        normalized = warning.casefold()
        if "establish causation" in normalized or "regression treats" in normalized:
            continue
        if warning not in limitation_lines:
            limitation_lines.append(warning)
    story: list[Any] = [
        Paragraph("NetLearn Analytics", styles["ReportTitle"]),
        Paragraph("Internet Speed and Online Learning Experience", styles["ReportSubtitle"]),
        Paragraph("<b>Statistical Analysis Report</b><br/>Generated " + _plain(date.today().strftime("%d %B %Y")), styles["ReportSubtitle"]),
        Paragraph("Research Objective", styles["SectionHeading"]),
        Paragraph(
            "To investigate statistical associations between reported internet connectivity conditions and online learning experiences or participation. The analysis describes association and does not establish causation.",
            styles["BodySmall"],
        ),
        Paragraph("Dataset Information", styles["SectionHeading"]),
        _table(
            [
                ["Field", "Value"],
                ["Dataset", dataset["source"]],
                ["Source type", "Verified included research dataset" if is_default else "User-provided CSV upload"],
                ["Verified source", "Mendeley Data DOI 10.17632/bzk9zbyvv7.1 (CC BY 4.0)" if is_default else "Upload provenance was not independently verified"],
                ["Total records", dataset["row_count"]],
                ["Total columns", dataset["column_count"]],
                ["Valid paired observations", analysis["sample_size"]],
                ["Excluded missing/invalid pairs", missing["excluded_from_paired_analysis"]],
                ["Exact duplicate rows", dataset["duplicate_row_count"]],
            ],
            [52 * mm, 118 * mm],
            styles,
        ),
        Paragraph("Selected Variables", styles["SectionHeading"]),
        _table(
            [
                ["Role", "Actual column", "Processing"],
                [
                    "Connectivity (X)",
                    x["column"],
                    _processing_text(
                        x["column"],
                        x["processing"],
                        include_known_scale=is_default,
                    ),
                ],
                [
                    "Learning outcome (Y)",
                    y["column"],
                    _processing_text(
                        y["column"],
                        y["processing"],
                        include_known_scale=is_default,
                    ),
                ],
            ],
            [34 * mm, 64 * mm, 72 * mm],
            styles,
        ),
        Paragraph("Descriptive Statistics", styles["SectionHeading"]),
        _table(
            [
                ["Variable", "Mean", "Median", "Sample SD (ddof=1)", "Valid n"],
                [x["column"], _number(x_stats["mean"]), _number(x_stats["median"]), _number(x_stats["sample_standard_deviation"]), x_stats["valid_observations"]],
                [y["column"], _number(y_stats["mean"]), _number(y_stats["median"]), _number(y_stats["sample_standard_deviation"]), y_stats["valid_observations"]],
            ],
            [70 * mm, 23 * mm, 23 * mm, 33 * mm, 21 * mm],
            styles,
        ),
        Paragraph("Correlation Analysis", styles["SectionHeading"]),
        _table(
            [
                ["Method", "Coefficient", "Direction", "p-value", "Valid pairs"],
                [correlation["method"], _number(correlation["coefficient"]), correlation["direction"], Paragraph(_p_value(correlation["p_value"]), styles["BodySmall"]), correlation["valid_pairs"]],
            ],
            [58 * mm, 26 * mm, 37 * mm, 23 * mm, 26 * mm],
            styles,
        ),
        Paragraph(_plain(correlation["interpretation"]), styles["Callout"]),
    ]

    story.append(Paragraph("Regression Analysis", styles["SectionHeading"]))
    if regression["status"] == "available":
        story.extend(
            [
                _table(
                    [
                        ["Equation", "Slope", "Intercept", "R-squared", "Valid pairs"],
                        [regression["equation"], _number(regression["slope"]), _number(regression["intercept"]), _number(regression["r_squared"]), regression["valid_pairs"]],
                    ],
                    [62 * mm, 25 * mm, 29 * mm, 28 * mm, 26 * mm],
                    styles,
                ),
                Paragraph(_plain(regression["interpretation"]), styles["Callout"]),
            ]
        )
    else:
        story.append(Paragraph("Regression was unavailable: " + _plain(regression.get("reason")), styles["Callout"]))

    story.extend(
        [
            Paragraph("Hypothesis Testing", styles["SectionHeading"]),
            _table(
                [
                    ["Item", "Result"],
                    ["Null hypothesis (H0)", hypothesis["null_hypothesis"]],
                    ["Alternative hypothesis (H1)", hypothesis["alternative_hypothesis"]],
                    ["Method", hypothesis["method"]],
                    ["Significance level", _number(hypothesis["alpha"], 3)],
                    ["Test statistic", _number(hypothesis["test_statistic"])],
                    ["p-value", Paragraph(_p_value(hypothesis["p_value"]), styles["BodySmall"])],
                    ["Decision", hypothesis["decision"]],
                ],
                [52 * mm, 118 * mm],
                styles,
            ),
            Paragraph(_plain(hypothesis["interpretation"]), styles["Callout"]),
            Paragraph("Key Findings", styles["SectionHeading"]),
            Paragraph(
                f"The selected sample produced a <b>{_plain(correlation['direction'])}</b> monotonic association between <b>{_plain(x['column'])}</b> and <b>{_plain(y['column'])}</b> (Spearman rho = {_number(correlation['coefficient'])}, p-value {_p_value(correlation['p_value'])}). {_plain(hypothesis['interpretation'])}",
                styles["BodySmall"],
            ),
            Paragraph("Limitations", styles["SectionHeading"]),
            Paragraph(
                "<br/>".join("- " + _plain(line) for line in limitation_lines),
                styles["BodySmall"],
            ),
            Paragraph("Visualization Summary", styles["SectionHeading"]),
            Paragraph("Frequency distributions for the two selected analytical variables. Counts are aggregate values; individual student records are not included.", styles["BodySmall"]),
            KeepTogether(
                [
                    _distribution_chart(analysis["visualization_data"]["distributions"]["connectivity"], x["column"]),
                    Spacer(1, 5 * mm),
                    _distribution_chart(analysis["visualization_data"]["distributions"]["learning_outcome"], y["column"]),
                ]
            ),
        ]
    )
    document.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    buffer.seek(0)
    return buffer
