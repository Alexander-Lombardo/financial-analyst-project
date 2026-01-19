"""
Create PowerPoint presentation from Target financial analysis
"""

import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor


def create_target_presentation():
    """Create comprehensive PowerPoint presentation."""

    # Load analysis data
    with open('output/target_analysis.json', 'r') as f:
        data = json.load(f)

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    add_title_slide(prs)

    # Slide 2: Executive Summary
    add_executive_summary(prs, data)

    # Slide 3: Baseline (FY2024)
    add_baseline_slide(prs, data[0])

    # Slide 4: Q1 2025 Analysis
    add_quarter_slide(prs, data[1], data[0])

    # Slide 5: Q2 2025 Analysis
    add_quarter_slide(prs, data[2], data[0])

    # Slide 6: Q3 2025 Analysis - RED FLAGS
    add_q3_warning_slide(prs, data[3], data[0])

    # Slide 7: Debt & Leverage Analysis
    add_debt_analysis_slide(prs)

    # Slide 8: Key Risks & Recommendations
    add_recommendations_slide(prs, data)

    # Save presentation
    output_path = 'output/Target_Financial_Analysis.pptx'
    prs.save(output_path)
    print(f"✅ Presentation created: {output_path}")
    return output_path


def add_title_slide(prs):
    """Add title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    left = Inches(1)
    top = Inches(2.5)
    width = Inches(8)
    height = Inches(1)

    title_box = slide.shapes.add_textbox(left, top, width, height)
    tf = title_box.text_frame
    tf.text = "Target Corporation"

    p = tf.paragraphs[0]
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)  # Target red
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    subtitle_box = slide.shapes.add_textbox(left, Inches(3.5), width, Inches(0.5))
    tf = subtitle_box.text_frame
    tf.text = "Financial Analysis Report"
    p = tf.paragraphs[0]
    p.font.size = Pt(32)
    p.alignment = PP_ALIGN.CENTER

    # Period
    period_box = slide.shapes.add_textbox(left, Inches(4.2), width, Inches(0.4))
    tf = period_box.text_frame
    tf.text = "FY2024 - Q3 2025"
    p = tf.paragraphs[0]
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(128, 128, 128)
    p.alignment = PP_ALIGN.CENTER


def add_executive_summary(prs, data):
    """Add executive summary slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
    title = slide.shapes.title
    title.text = "Executive Summary"

    # Key findings box
    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(5.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    # Baseline metrics
    baseline = data[0]['vital_signs']
    q3 = data[3]['vital_signs']

    findings = [
        ("FY2024 Baseline Performance", [
            f"• Net Sales: ${baseline['net_sales_billion']:.2f}B",
            f"• Operating Margin: {baseline['operating_margin_percent']:.2f}%",
            f"• Gross Margin: {baseline['gross_margin_percent']:.2f}%",
        ]),
        ("Q3 2025 - Critical Weakness Detected", [
            f"• Operating Margin: {q3['operating_margin_percent']:.2f}% ({q3['vs_baseline']['operating_margin_change']:+.2f}% vs baseline) ⚠️",
            f"• Inventory: ${q3['inventory_billion']:.2f}B (+{((q3['inventory_billion']/baseline['inventory_billion']-1)*100):.1f}%) 🚨",
            f"• Debt increased 7.5% while operating income declined",
        ]),
        ("Key Risk Flags", [
            "• Interest coverage deteriorated from 9.7x to 1.5x",
            "• Shrink/theft mentioned in all quarters",
            "• Inventory buildup suggests potential clearance ahead",
        ]),
    ]

    for section_title, bullets in findings:
        p = tf.add_paragraph()
        p.text = section_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_after = Pt(6)

        for bullet in bullets:
            p = tf.add_paragraph()
            p.text = bullet
            p.level = 0
            p.font.size = Pt(14)
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(12)


def add_baseline_slide(prs, baseline_data):
    """Add baseline slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Baseline: FY2024 Annual Performance"

    vital = baseline_data['vital_signs']

    # Create table
    left = Inches(2)
    top = Inches(2)
    width = Inches(6)
    height = Inches(3)

    table = slide.shapes.add_table(6, 2, left, top, width, height).table

    # Header
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"

    # Data rows
    metrics = [
        ("Net Sales", f"${vital['net_sales_billion']:.2f}B"),
        ("Operating Income", f"${vital['operating_income_billion']:.2f}B"),
        ("Operating Margin", f"{vital['operating_margin_percent']:.2f}%"),
        ("Gross Margin", f"{vital['gross_margin_percent']:.2f}%"),
        ("Inventory", f"${vital['inventory_billion']:.2f}B"),
    ]

    for i, (metric, value) in enumerate(metrics, 1):
        table.cell(i, 0).text = metric
        table.cell(i, 1).text = value

    # Style table
    for row in table.rows:
        row.height = Inches(0.5)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(14)

    # Risk flags
    if baseline_data['risk_flags']:
        left = Inches(1)
        top = Inches(5.5)
        width = Inches(8)
        height = Inches(1.5)

        text_box = slide.shapes.add_textbox(left, top, width, height)
        tf = text_box.text_frame

        p = tf.add_paragraph()
        p.text = "Risk Flags:"
        p.font.size = Pt(14)
        p.font.bold = True

        for flag in baseline_data['risk_flags']:
            p = tf.add_paragraph()
            p.text = f"• {flag}"
            p.font.size = Pt(12)
            p.level = 0


def add_quarter_slide(prs, quarter_data, baseline_data):
    """Add quarterly analysis slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = f"{quarter_data['period']} Performance"

    vital = quarter_data['vital_signs']
    baseline_vital = baseline_data['vital_signs']

    # Left column: Metrics
    left = Inches(0.5)
    top = Inches(1.8)
    width = Inches(4.5)
    height = Inches(4)

    table = slide.shapes.add_table(6, 3, left, top, width, height).table

    # Headers
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = quarter_data['period']
    table.cell(0, 2).text = "vs Baseline"

    # Data
    metrics = [
        ("Net Sales", vital.get('net_sales_billion', 0), baseline_vital.get('net_sales_billion', 0), "B"),
        ("Operating Margin", vital.get('operating_margin_percent', 0), baseline_vital.get('operating_margin_percent', 0), "%"),
        ("Gross Margin", vital.get('gross_margin_percent', 0), baseline_vital.get('gross_margin_percent', 0), "%"),
        ("Operating Income", vital.get('operating_income_billion', 0), baseline_vital.get('operating_income_billion', 0), "B"),
        ("Inventory", vital.get('inventory_billion', 0), baseline_vital.get('inventory_billion', 0), "B"),
    ]

    for i, (metric, current, baseline, unit) in enumerate(metrics, 1):
        table.cell(i, 0).text = metric
        if unit == "B":
            table.cell(i, 1).text = f"${current:.2f}B"
            change = current - baseline
            table.cell(i, 2).text = f"{change:+.2f}B"
        else:
            table.cell(i, 1).text = f"{current:.2f}%"
            change = current - baseline
            table.cell(i, 2).text = f"{change:+.2f}%"

            # Color code changes
            cell = table.cell(i, 2)
            if change < -0.5:
                cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)
            elif change > 0.5:
                cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 128, 0)

    # Style table
    for row in table.rows:
        row.height = Inches(0.5)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(12)

    # Right column: Analysis
    left = Inches(5.5)
    top = Inches(1.8)
    width = Inches(4)
    height = Inches(4)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    p = tf.add_paragraph()
    p.text = "Key Observations:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.space_after = Pt(8)

    # Add trend analysis
    if 'vs_baseline' in vital and vital['vs_baseline']:
        vs = vital['vs_baseline']

        if 'operating_margin_trend' in vs:
            p = tf.add_paragraph()
            trend = vs['operating_margin_trend']
            emoji = "✅" if trend == "improving" else "⚠️"
            p.text = f"{emoji} Operating margin {trend}"
            p.font.size = Pt(12)
            p.level = 0

        if 'markdown_flag' in vs:
            p = tf.add_paragraph()
            p.text = f"🚨 {vs['markdown_flag']}"
            p.font.size = Pt(12)
            p.font.color.rgb = RGBColor(255, 0, 0)
            p.level = 0

    # Risk flags
    if quarter_data['risk_flags']:
        p = tf.add_paragraph()
        p.text = "\nRisk Flags:"
        p.font.size = Pt(12)
        p.font.bold = True

        for flag in quarter_data['risk_flags'][:3]:
            p = tf.add_paragraph()
            p.text = f"• {flag}"
            p.font.size = Pt(11)
            p.level = 1


def add_q3_warning_slide(prs, q3_data, baseline_data):
    """Special slide for Q3 with warnings."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Warning banner
    left = Inches(0)
    top = Inches(0.5)
    width = Inches(10)
    height = Inches(1)

    banner = slide.shapes.add_shape(1, left, top, width, height)  # Rectangle
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(255, 0, 0)
    banner.line.color.rgb = RGBColor(255, 0, 0)

    tf = banner.text_frame
    tf.text = "⚠️ Q3 2025: CRITICAL WEAKNESS DETECTED"
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Metrics comparison
    vital = q3_data['vital_signs']
    baseline_vital = baseline_data['vital_signs']

    left = Inches(1)
    top = Inches(2)
    width = Inches(8)
    height = Inches(4.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    issues = [
        f"Operating Margin: {vital['operating_margin_percent']:.2f}% ({vital['vs_baseline']['operating_margin_change']:+.2f}% vs baseline)",
        f"  → Declined 147 basis points - worst quarter of the year",
        "",
        f"Inventory: ${vital['inventory_billion']:.2f}B",
        f"  → Up {((vital['inventory_billion']/baseline_vital['inventory_billion']-1)*100):.1f}% from baseline",
        f"  → Excess inventory building = potential clearance sales ahead",
        "",
        f"Operating Income: ${vital['operating_income_billion']:.2f}B",
        f"  → Lowest quarterly operating income despite similar sales",
        "",
        "Combined Effect:",
        "  → Interest coverage dropped to 1.5x (from 9.7x at baseline)",
        "  → Approaching distressed territory (<1.5x is red flag)",
        "  → Rising debt + falling profitability = liquidity risk",
    ]

    for line in issues:
        p = tf.add_paragraph()
        p.text = line
        if line.startswith("  →"):
            p.font.size = Pt(13)
            p.level = 1
            p.font.color.rgb = RGBColor(128, 0, 0)
        elif ":" in line and not line.startswith(" "):
            p.font.size = Pt(16)
            p.font.bold = True
            p.space_after = Pt(4)
        else:
            p.font.size = Pt(14)

        if "worst" in line.lower() or "distressed" in line.lower() or "risk" in line.lower():
            p.font.color.rgb = RGBColor(255, 0, 0)


def add_debt_analysis_slide(prs):
    """Add debt analysis slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Debt & Leverage Analysis"

    # Debt metrics table
    left = Inches(0.5)
    top = Inches(1.8)
    width = Inches(9)
    height = Inches(2.5)

    table = slide.shapes.add_table(5, 5, left, top, width, height).table

    # Headers
    headers = ["Metric", "FY2024", "Q1 2025", "Q2 2025", "Q3 2025"]
    for i, header in enumerate(headers):
        table.cell(0, i).text = header

    # Data
    debt_data = [
        ["Total Debt", "$14.30B", "$14.33B", "$15.32B", "$15.37B"],
        ["Debt-to-Equity", "0.97x", "0.96x", "0.99x", "0.99x"],
        ["Interest Coverage", "9.7x", "2.6x", "2.2x", "1.5x"],
        ["Change from Baseline", "—", "+0.2%", "+7.1%", "+7.5%"],
    ]

    for i, row_data in enumerate(debt_data, 1):
        for j, value in enumerate(row_data):
            cell = table.cell(i, j)
            cell.text = value

            # Highlight deteriorating coverage
            if i == 2 and j > 1:  # Interest coverage row
                coverage = float(value.replace('x', ''))
                if coverage < 2.0:
                    cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)

    # Style table
    for row in table.rows:
        row.height = Inches(0.4)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(12)

    # Key findings
    left = Inches(0.5)
    top = Inches(4.5)
    width = Inches(9)
    height = Inches(2.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame

    p = tf.add_paragraph()
    p.text = "Critical Findings:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    findings = [
        "Debt increased 7.5% while operating income declined significantly",
        "Interest coverage compressed from 9.7x to 1.5x in one year (approaching distressed level)",
        "Debt likely used to fund inventory buildup and cover working capital shortfalls",
        "$2.00B debt matures in FY2026 - needs refinancing or paydown with limited cash flow",
    ]

    for finding in findings:
        p = tf.add_paragraph()
        p.text = f"• {finding}"
        p.font.size = Pt(13)
        p.level = 0


def add_recommendations_slide(prs, data):
    """Add recommendations slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Key Risks & Monitoring Points"

    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(5.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    sections = [
        ("Immediate Risks (Q4 2025)", [
            "Q4 operating margin recovery critical to avoid further deterioration",
            "High inventory + weak margins → Expected Q4 clearance sales",
            "If interest coverage falls below 1.5x, triggers debt covenant concerns",
        ]),
        ("Watch Points for Next Quarter", [
            "Operating margin trend (needs to recover to 5%+ range)",
            "Inventory levels (should decline post-holiday)",
            "Comparable sales breakdown (store vs. digital performance)",
            "Cash flow from operations (ability to service $2B FY2026 debt maturity)",
        ]),
        ("Strategic Questions", [
            "Can Target reduce inventory without severe margin impact?",
            "Is the operating margin decline temporary or structural?",
            "Will shrink/theft issues persist into FY2026?",
            "Is current debt level sustainable with lower profitability?",
        ]),
    ]

    for section_title, bullets in sections:
        p = tf.add_paragraph()
        p.text = section_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_after = Pt(6)

        for bullet in bullets:
            p = tf.add_paragraph()
            p.text = f"• {bullet}"
            p.font.size = Pt(13)
            p.level = 0
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(10)


if __name__ == "__main__":
    create_target_presentation()
