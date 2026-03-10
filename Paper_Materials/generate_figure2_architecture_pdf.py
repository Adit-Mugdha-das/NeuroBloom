from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
OUTPUT_PATH = r"d:\NeuroBloom\Paper_Materials\figure2_system_architecture.pdf"

TITLE_COLOR = colors.HexColor("#1E293B")
TEXT_COLOR = colors.HexColor("#243447")
MUTED_COLOR = colors.HexColor("#5F6B7A")
LINE_COLOR = colors.HexColor("#7C8A99")
INTERFACE_FILL = colors.HexColor("#E9EEF3")
SERVICE_FILL = colors.HexColor("#DDF3F0")
ANALYTICS_FILL = colors.HexColor("#F7ECD2")
DATA_FILL = colors.HexColor("#EEF2F7")
HEADER_FILL = colors.HexColor("#F8FAFC")


def rounded_box(pdf, x, y, width, height, fill, stroke=LINE_COLOR, radius=14):
    pdf.setStrokeColor(stroke)
    pdf.setFillColor(fill)
    pdf.roundRect(x, y, width, height, radius, stroke=1, fill=1)


def draw_centered_lines(pdf, x, y_top, width, title, lines, title_size=11, body_size=8.2, line_gap=11):
    pdf.setFillColor(TITLE_COLOR)
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawCentredString(x + width / 2, y_top, title)

    current_y = y_top - 16
    pdf.setStrokeColor(MUTED_COLOR)
    pdf.setLineWidth(0.8)
    divider_width = min(52, width * 0.35)
    pdf.line(x + (width - divider_width) / 2, current_y + 4, x + (width + divider_width) / 2, current_y + 4)

    pdf.setFont("Helvetica", body_size)
    pdf.setFillColor(TEXT_COLOR)
    for line in lines:
        pdf.drawCentredString(x + width / 2, current_y - 10, line)
        current_y -= line_gap


def draw_layer_header(pdf, x, y, width, title):
    rounded_box(pdf, x, y, width, 34, HEADER_FILL, stroke=colors.HexColor("#CBD5E1"), radius=10)
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.setFillColor(TITLE_COLOR)
    pdf.drawCentredString(x + width / 2, y + 12, title)


def draw_database_box(pdf, x, y, width, height, title, lines):
    rounded_box(pdf, x, y, width, height, DATA_FILL, radius=18)
    pdf.setFillColor(TITLE_COLOR)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(x + width / 2, y + height - 24, title)

    pdf.setStrokeColor(MUTED_COLOR)
    pdf.setLineWidth(0.9)
    pdf.line(x + 24, y + height - 34, x + width - 24, y + height - 34)

    pdf.setFillColor(TEXT_COLOR)
    pdf.setFont("Helvetica", 8.3)
    current_y = y + height - 52
    for line in lines:
        pdf.drawCentredString(x + width / 2, current_y, line)
        current_y -= 13


def arrow(pdf, x1, y1, x2, y2, head_len=7, head_half=4):
    pdf.setStrokeColor(MUTED_COLOR)
    pdf.setFillColor(MUTED_COLOR)
    pdf.setLineWidth(1.15)
    pdf.line(x1, y1, x2, y2)

    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux

    tip_x = x2
    tip_y = y2
    base_x = tip_x - ux * head_len
    base_y = tip_y - uy * head_len
    left_x = base_x + px * head_half
    left_y = base_y + py * head_half
    right_x = base_x - px * head_half
    right_y = base_y - py * head_half
    pdf.wedge if False else None
    pdf.line(tip_x, tip_y, left_x, left_y)
    pdf.line(tip_x, tip_y, right_x, right_y)


def label_fit_lines(text, font_name, font_size, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw():
    pdf = canvas.Canvas(OUTPUT_PATH, pagesize=landscape(A4))
    pdf.setTitle("NeuroBloom system architecture")

    margin_x = 34
    top_y = PAGE_HEIGHT - 26
    content_top = PAGE_HEIGHT - 72
    footer_y = 18
    gap = 16
    col_widths = [166, 208, 184, 170]
    x_positions = [margin_x]
    for width in col_widths[:-1]:
        x_positions.append(x_positions[-1] + width + gap)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(TITLE_COLOR)
    pdf.drawCentredString(PAGE_WIDTH / 2, top_y, "NeuroBloom System Architecture")

    layer_titles = [
        "Layer 1  |  Role-based Interfaces",
        "Layer 2  |  Core Application Services",
        "Layer 3  |  Analytics & Monitoring",
        "Layer 4  |  Persistent Data Layer",
    ]
    for x, width, title in zip(x_positions, col_widths, layer_titles):
        draw_layer_header(pdf, x, content_top, width, title)

    col1_x = x_positions[0]
    col2_x = x_positions[1]
    col3_x = x_positions[2]
    col4_x = x_positions[3]

    box_w1 = col_widths[0]
    box_h1 = 96
    box_gap1 = 18
    start_y1 = content_top - 54 - box_h1
    interface_boxes = [
        (
            "Patient Interface",
            ["baseline & training tasks", "progress/history", "prescriptions/messages"],
        ),
        (
            "Doctor Portal",
            ["patient review", "dashboard & prescriptions", "training plans/reports"],
        ),
        (
            "Admin Portal",
            ["doctor verification", "governance & notifications", "audit/export"],
        ),
    ]
    interface_centers = []
    y = start_y1
    for title, lines in interface_boxes:
        rounded_box(pdf, col1_x, y, box_w1, box_h1, INTERFACE_FILL, radius=18)
        draw_centered_lines(pdf, col1_x, y + box_h1 - 24, box_w1, title, lines)
        interface_centers.append((col1_x + box_w1, y + box_h1 / 2))
        y -= box_h1 + box_gap1

    auth_y = content_top - 54 - 78
    auth_h = 78
    service_gap = 14
    service_h = 86
    rounded_box(pdf, col2_x, auth_y, col_widths[1], auth_h, SERVICE_FILL, radius=18)
    draw_centered_lines(
        pdf,
        col2_x,
        auth_y + auth_h - 22,
        col_widths[1],
        "Authentication & Role Access",
        ["login", "authorization", "role control"],
    )

    service_titles = [
        (
            "Task, Baseline & Training Services",
            ["task execution", "baseline assessment", "training session management"],
        ),
        (
            "Clinician Workflow Services",
            ["patient assignment", "prescriptions", "intervention planning", "messaging/reports"],
        ),
        (
            "Administrative Governance Services",
            ["user management", "department/oversight", "notifications", "audit support"],
        ),
    ]
    service_positions = []
    current_y = auth_y - service_gap - service_h
    custom_heights = [92, 100, 100]
    for (title, lines), height in zip(service_titles, custom_heights):
        rounded_box(pdf, col2_x, current_y, col_widths[1], height, SERVICE_FILL, radius=18)
        draw_centered_lines(pdf, col2_x, current_y + height - 22, col_widths[1], title, lines)
        service_positions.append((col2_x, current_y, col_widths[1], height))
        current_y -= height + service_gap

    analytic_boxes = [
        (
            "Session Context & Digital Biomarkers",
            ["fatigue / sleep / stress context", "response speed & accuracy", "variability indicators"],
            110,
        ),
        (
            "Longitudinal Analytics & Reporting",
            ["trend analysis", "progress summaries", "risk alerts / reports"],
            96,
        ),
    ]
    analytics_positions = []
    analytics_y = content_top - 54 - 98
    for title, lines, height in analytic_boxes:
        rounded_box(pdf, col3_x, analytics_y, col_widths[2], height, ANALYTICS_FILL, radius=18)
        draw_centered_lines(pdf, col3_x, analytics_y + height - 22, col_widths[2], title, lines)
        analytics_positions.append((col3_x, analytics_y, col_widths[2], height))
        analytics_y -= height + 26

    db_y = content_top - 54 - 198
    draw_database_box(
        pdf,
        col4_x,
        db_y,
        col_widths[3],
        190,
        "PostgreSQL / SQLModel Data Store",
        [
            "users & roles",
            "baseline records",
            "training sessions",
            "session context",
            "plans / reports / alerts",
        ],
    )

    auth_center_y = auth_y + auth_h / 2
    for start_x, start_y in interface_centers:
        arrow(pdf, start_x + 4, start_y, col2_x - 10, auth_center_y)

    service_centers = [
        (col2_x + col_widths[1], service_positions[0][1] + service_positions[0][3] / 2),
        (col2_x + col_widths[1], service_positions[1][1] + service_positions[1][3] / 2),
        (col2_x + col_widths[1], service_positions[2][1] + service_positions[2][3] / 2),
    ]
    auth_right_x = col2_x + col_widths[1]
    auth_targets = [
        service_positions[0][1] + service_positions[0][3] / 2,
        service_positions[1][1] + service_positions[1][3] / 2,
        service_positions[2][1] + service_positions[2][3] / 2,
    ]
    for target_y in auth_targets:
        arrow(pdf, auth_right_x - 6, auth_center_y, auth_right_x - 6, target_y)

    biomarker_center_y = analytics_positions[0][1] + analytics_positions[0][3] / 2
    reporting_center_y = analytics_positions[1][1] + analytics_positions[1][3] / 2
    arrow(pdf, service_centers[0][0] + 4, service_centers[0][1], col3_x - 10, biomarker_center_y)
    arrow(pdf, service_centers[1][0] + 4, service_centers[1][1], col3_x - 10, reporting_center_y)
    arrow(pdf, service_centers[2][0] + 4, service_centers[2][1], col3_x - 10, reporting_center_y)
    arrow(
        pdf,
        col3_x + col_widths[2],
        biomarker_center_y,
        col3_x + col_widths[2],
        reporting_center_y + 28,
    )

    db_left_x = col4_x - 10
    db_mid_y = db_y + 95
    arrow(pdf, col2_x + col_widths[1] + 4, auth_center_y - 8, db_left_x, db_mid_y + 44)
    arrow(pdf, col3_x + col_widths[2] + 4, reporting_center_y, db_left_x, db_mid_y - 10)

    footer_text = "Svelte frontend • FastAPI backend • SQLModel ORM • PostgreSQL"
    pdf.setFont("Helvetica", 9.5)
    pdf.setFillColor(MUTED_COLOR)
    pdf.drawCentredString(PAGE_WIDTH / 2, footer_y, footer_text)

    pdf.save()


if __name__ == "__main__":
    draw()