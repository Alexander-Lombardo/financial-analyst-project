"""
Create PowerPoint presentation from Target financial analysis

Organized into 5 Pillars of Financial Analysis:
1. Growth & Revenue - Is the business growing?
2. Profitability & Margins - How efficiently is the company generating profits?
3. Liquidity & Solvency - Can the company pay its bills today and debts in the future?
4. Operational Efficiency - How well is the company using its assets?
5. Valuation & Risk - Is the stock fairly priced, and what are the risks?
"""

import json
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from thesis_generator import ThesisGenerator


# =============================================================================
# CHART CONFIGURATION - All 24 charts organized by pillar
# =============================================================================

CHART_CONFIG = {
    # Pillar 1: Growth & Revenue (4 charts)
    "pillar_1": {
        "title": "Growth & Revenue",
        "question": "How is the business growing?",
        "charts": [
            {
                "title": "Revenue & Net Income (10-Year)",
                "file": "chart_revenue_netincome_annual.html",
                "description": "Shows Target's 10-year revenue and net income trajectory from annual 10-K filings. Look for consistent growth and whether profits keep pace with revenue."
            },
            {
                "title": "Revenue Growth YoY",
                "file": "chart_revenue_growth_yoy.html",
                "description": "Tracks year-over-year revenue growth rates by quarter. Reveals acceleration or deceleration in growth momentum."
            },
            {
                "title": "Revenue vs Inventory Growth",
                "file": "chart_revenue_vs_inventory.html",
                "description": "Compares revenue growth to inventory buildup. Inventory growing faster than sales signals potential markdown risk."
            },
            {
                "title": "Revenue & Net Income (Quarterly)",
                "file": "chart_revenue_netincome_longterm.html",
                "description": "Quarterly view with calculated Q4 data showing seasonal patterns. Q4 (holiday season) typically shows peak revenue."
            },
        ]
    },

    # Pillar 2: Profitability & Margins (6 charts)
    "pillar_2": {
        "title": "Profitability & Margins",
        "question": "How efficiently is the company generating profits?",
        "charts": [
            {
                "title": "Margin Analysis (Gross/Operating/Net)",
                "file": "chart_margin_analysis.html",
                "description": "Three margin lines tracking profitability over time. Compression between lines reveals where profits leak."
            },
            {
                "title": "Margin Bridge Waterfall",
                "file": "chart_margin_bridge.html",
                "description": "Waterfall showing margin evolution from FY2022 baseline. Green bars = improvement, red bars = deterioration."
            },
            {
                "title": "Operating Expense Breakdown",
                "file": "chart_expense_breakdown.html",
                "description": "100% stacked bars showing cost structure. Watch for SG&A creep eating into margins."
            },
            {
                "title": "EBITDA Bridge",
                "file": "chart_ebitda_bridge.html",
                "description": "Shows how revenue flows to EBITDA through operating expenses. The D&A add-back reveals capital intensity."
            },
            {
                "title": "Operating Margin Waterfall",
                "file": "chart_operating_margin_waterfall.html",
                "description": "Quarterly margin changes as waterfall. Identifies seasonal patterns and pressure points."
            },
            {
                "title": "Earnings Quality",
                "file": "chart_earnings_quality.html",
                "description": "Compares Net Income to Operating Cash Flow. High-quality earnings convert to cash consistently."
            },
        ]
    },

    # Pillar 3: Liquidity & Solvency (5 charts)
    "pillar_3": {
        "title": "Liquidity & Solvency",
        "question": "Can the company pay its bills today and debts in the future?",
        "charts": [
            {
                "title": "Current Ratio Gauge",
                "file": "chart_current_ratio_gauge.html",
                "description": "Measures short-term liquidity. Below 1.0 is warning (liabilities exceed assets); above 1.5 is healthy for retail."
            },
            {
                "title": "Capital Structure",
                "file": "chart_capital_structure_donut.html",
                "description": "Shows debt vs equity mix. Higher debt = higher risk but potentially higher returns on equity."
            },
            {
                "title": "Debt-to-EBITDA Trend",
                "file": "chart_debt_to_ebitda_trend.html",
                "description": "Key leverage metric showing how many years of earnings to repay debt. Below 3x is healthy; above 5x is risky."
            },
            {
                "title": "Debt Health (Interest Coverage)",
                "file": "chart_debt_health.html",
                "description": "Interest coverage ratio tracking. Above 3x is comfortable; below 2x requires monitoring."
            },
            {
                "title": "Statement of Cash Flows",
                "file": "chart_cash_flows.html",
                "description": "Three cash flow lines: Operating, Investing, Financing. Operating should be consistently positive."
            },
        ]
    },

    # Pillar 4: Operational Efficiency (4 charts)
    "pillar_4": {
        "title": "Operational Efficiency",
        "question": "How well is the company using its assets?",
        "charts": [
            {
                "title": "DuPont Analysis",
                "file": "chart_dupont_analysis.html",
                "description": "Decomposes ROE into Profit Margin x Asset Turnover x Financial Leverage. Shows what drives returns."
            },
            {
                "title": "Inventory Efficiency",
                "file": "chart_inventory_efficiency.html",
                "description": "Tracks turnover ratio and days on hand. Faster turns = less capital tied up in inventory."
            },
            {
                "title": "Cash Conversion Cycle",
                "file": "chart_cash_conversion_cycle.html",
                "description": "Days to convert inventory to cash vs retail peers. Lower is better; negative means suppliers finance operations."
            },
            {
                "title": "OCF vs CapEx",
                "file": "chart_ocf_vs_capex.html",
                "description": "Operating cash vs capital spending. The gap between them is Free Cash Flow available for shareholders."
            },
        ]
    },

    # Pillar 5: Valuation & Risk (5 charts)
    "pillar_5": {
        "title": "Valuation & Risk",
        "question": "Is the stock fairly priced, and what are the risks?",
        "charts": [
            {
                "title": "Valuation vs Growth",
                "file": "chart_valuation_scatter.html",
                "description": "P/E ratio vs revenue growth for Target and peers. Lower-right quadrant = undervalued opportunities."
            },
            {
                "title": "Historical P/E Band",
                "file": "chart_pe_band.html",
                "description": "Current price vs historical valuation range. Below 25th percentile = historically undervalued."
            },
            {
                "title": "Cash Flow Sankey",
                "file": "chart_cash_flow_sankey.html",
                "description": "Visualizes cash allocation: CapEx, dividends, buybacks, debt repayment. Shows management priorities."
            },
            {
                "title": "Risk Trends",
                "file": "chart_risk_trends.html",
                "description": "Stacked area of risk mentions (shrink, theft, markdown) over time. Rising trends signal increasing concerns."
            },
            {
                "title": "Risk Heatmap",
                "file": "chart_risk_heatmap_grid.html",
                "description": "Intensity grid showing risk types by period. Dark cells = high concern in that area."
            },
        ]
    },
}


# =============================================================================
# MAIN PRESENTATION FUNCTION
# =============================================================================

def create_target_presentation():
    """Create comprehensive PowerPoint presentation organized by 5 pillars."""

    # Generate investment thesis
    print("   Generating investment thesis...")
    thesis_gen = ThesisGenerator()
    thesis_gen.export_thesis()

    # Load analysis data
    with open('output/target_analysis.json', 'r') as f:
        full_data = json.load(f)
        data = full_data['filings']

    # Load timeseries data
    with open('output/target_timeseries.json', 'r') as f:
        timeseries_data = json.load(f)

    # Load investment thesis
    with open('output/investment_thesis.json', 'r') as f:
        thesis = json.load(f)

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # === INTRODUCTION (3 slides) ===
    print("   Creating introduction slides...")
    add_title_slide(prs)
    add_executive_summary(prs, data)
    add_investment_thesis_slide(prs, thesis)

    # === PILLAR 1: Growth & Revenue (5 slides) ===
    print("   Creating Pillar 1: Growth & Revenue...")
    pillar = CHART_CONFIG["pillar_1"]
    add_pillar_section_slide(prs, 1, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"])

    # === PILLAR 2: Profitability & Margins (7 slides) ===
    print("   Creating Pillar 2: Profitability & Margins...")
    pillar = CHART_CONFIG["pillar_2"]
    add_pillar_section_slide(prs, 2, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"])

    # === PILLAR 3: Liquidity & Solvency (6 slides) ===
    print("   Creating Pillar 3: Liquidity & Solvency...")
    pillar = CHART_CONFIG["pillar_3"]
    add_pillar_section_slide(prs, 3, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"])

    # === PILLAR 4: Operational Efficiency (5 slides) ===
    print("   Creating Pillar 4: Operational Efficiency...")
    pillar = CHART_CONFIG["pillar_4"]
    add_pillar_section_slide(prs, 4, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"])

    # === PILLAR 5: Valuation & Risk (6 slides) ===
    print("   Creating Pillar 5: Valuation & Risk...")
    pillar = CHART_CONFIG["pillar_5"]
    add_pillar_section_slide(prs, 5, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"])

    # Save presentation
    output_path = 'output/Target_Financial_Analysis.pptx'
    prs.save(output_path)

    # Summary output
    total_charts = sum(len(p["charts"]) for p in CHART_CONFIG.values())
    total_slides = 3 + 5 + len(CHART_CONFIG)  # intro + section dividers + charts

    print(f"\n   Presentation created: {output_path}")
    print(f"   {3 + 5 * 2 + total_charts} slides total:")
    print("     - 3 introduction slides (Title, Executive Summary, Investment Thesis)")
    print("     - 5 pillar section dividers")
    print(f"     - {total_charts} chart slides across 5 pillars")
    print("     - Charts embedded as PNG images (run visualize_data.py first)")

    return output_path


# =============================================================================
# PILLAR SECTION SLIDE
# =============================================================================

def add_pillar_section_slide(prs, pillar_num, title, question):
    """Add a pillar section divider slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Colored banner at top
    banner = slide.shapes.add_shape(1, Inches(0), Inches(2.5), Inches(10), Inches(2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(204, 0, 0)  # Target red
    banner.line.color.rgb = RGBColor(204, 0, 0)

    # Pillar number
    num_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(9), Inches(0.6))
    num_frame = num_box.text_frame
    p = num_frame.paragraphs[0]
    p.text = f"PILLAR {pillar_num}"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Pillar title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.3), Inches(9), Inches(0.8))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Guiding question below banner
    q_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(9), Inches(0.5))
    q_frame = q_box.text_frame
    p = q_frame.paragraphs[0]
    p.text = f'"{question}"'
    p.font.size = Pt(24)
    p.font.italic = True
    p.font.color.rgb = RGBColor(100, 100, 100)
    p.alignment = PP_ALIGN.CENTER


# =============================================================================
# GENERIC CHART SLIDE
# =============================================================================

def add_chart_slide(prs, title, chart_file, description):
    """Add a chart slide with embedded PNG image.

    Embeds the static PNG version of the chart directly in the slide.
    Falls back to hyperlink if PNG not found.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title (top)
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.5))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)  # Target red

    # Check for PNG image
    image_file = chart_file.replace('.html', '.png')
    image_path = Path(f"output/{image_file}")

    if image_path.exists():
        # Embed chart image (center of slide)
        slide.shapes.add_picture(
            str(image_path),
            left=Inches(0.5),
            top=Inches(0.8),
            width=Inches(9),
            height=Inches(4.5)
        )

        # Description (bottom)
        desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(1.5))
        desc_frame = desc_box.text_frame
        desc_frame.word_wrap = True

        p = desc_frame.paragraphs[0]
        p.text = description
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(100, 100, 100)
    else:
        # Fallback: show description and hyperlink if image not found
        desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(1.5))
        desc_frame = desc_box.text_frame
        desc_frame.word_wrap = True

        p = desc_frame.paragraphs[0]
        p.text = description
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(60, 60, 60)
        p.space_after = Pt(12)

        # Hyperlink fallback
        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.0), Inches(9), Inches(1.0))
        link_frame = link_box.text_frame

        p = link_frame.paragraphs[0]
        p.text = "Click to view interactive chart:"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(8)

        p = link_frame.add_paragraph()
        chart_path = Path(f"output/{chart_file}").resolve()

        run = p.add_run()
        run.text = f"   {chart_file}"
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0, 0, 255)
        run.font.underline = True
        run.hyperlink.address = str(chart_path)

        # Placeholder indicator
        indicator_box = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(2))
        indicator_frame = indicator_box.text_frame

        p = indicator_frame.paragraphs[0]
        p.text = f"[Chart image not found: {image_file}]"
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.font.italic = True
        p.alignment = PP_ALIGN.CENTER


# =============================================================================
# INTRODUCTION SLIDES
# =============================================================================

def add_title_slide(prs):
    """Add title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1))
    tf = title_box.text_frame
    tf.text = "Target Corporation"
    p = tf.paragraphs[0]
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)  # Target red
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(0.5))
    tf = subtitle_box.text_frame
    tf.text = "Financial Analysis Report"
    p = tf.paragraphs[0]
    p.font.size = Pt(32)
    p.alignment = PP_ALIGN.CENTER

    # Period
    period_box = slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(8), Inches(0.4))
    tf = period_box.text_frame
    tf.text = "5 Pillars of Financial Analysis | 24 Interactive Charts"
    p = tf.paragraphs[0]
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(128, 128, 128)
    p.alignment = PP_ALIGN.CENTER

    # Data coverage
    coverage_box = slide.shapes.add_textbox(Inches(1), Inches(4.8), Inches(8), Inches(0.4))
    tf = coverage_box.text_frame
    tf.text = "Data: FY2015 - Q3 2025"
    p = tf.paragraphs[0]
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(150, 150, 150)
    p.alignment = PP_ALIGN.CENTER


def add_executive_summary(prs, data):
    """Add executive summary slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Executive Summary"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    # Key findings box
    text_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(6))
    tf = text_box.text_frame
    tf.word_wrap = True

    # Get baseline and latest data
    baseline = data[10]['vital_signs'] if len(data) > 10 else data[0]['vital_signs']
    latest = data[-1]['vital_signs'] if data else {}

    findings = [
        ("FY2024 Baseline Performance", [
            f"Net Sales: ${baseline.get('net_sales_billion', 0):.2f}B",
            f"Operating Margin: {baseline.get('operating_margin_percent', 0):.2f}%",
            f"Gross Margin: {baseline.get('gross_margin_percent', 0):.2f}%",
        ]),
        ("Latest Quarter Highlights", [
            f"Operating Margin: {latest.get('operating_margin_percent', 0):.2f}%",
            f"Inventory: ${latest.get('inventory_billion', 0):.2f}B",
            "See pillar charts for detailed trends",
        ]),
        ("5 Pillars Covered", [
            "1. Growth & Revenue - 4 charts",
            "2. Profitability & Margins - 6 charts",
            "3. Liquidity & Solvency - 5 charts",
            "4. Operational Efficiency - 4 charts",
            "5. Valuation & Risk - 5 charts",
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
            p.text = f"   {bullet}"
            p.level = 0
            p.font.size = Pt(14)
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(12)


def add_investment_thesis_slide(prs, thesis):
    """Add Investment Thesis slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.5))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Investment Thesis"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    # Recommendation box
    rec_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(1.2))
    rec_frame = rec_box.text_frame
    rec = thesis['recommendation']

    p = rec_frame.paragraphs[0]
    p.text = f"Recommendation: {rec['rating']}"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 128, 0) if rec['rating'] == 'Buy' else \
                       RGBColor(255, 140, 0) if rec['rating'] == 'Hold' else \
                       RGBColor(255, 0, 0)

    p = rec_frame.add_paragraph()
    p.text = rec['rationale']
    p.font.size = Pt(16)
    p.space_after = Pt(6)

    # Risk factors (left column)
    risk_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(4.25), Inches(4))
    risk_frame = risk_box.text_frame

    p = risk_frame.paragraphs[0]
    p.text = "Risk Factors"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)

    for risk in thesis['risk_factors'][:3]:
        p = risk_frame.add_paragraph()
        p.text = f"{risk['factor']} ({risk['severity']})"
        p.font.size = Pt(14)
        p.font.bold = True
        p.level = 0

        p = risk_frame.add_paragraph()
        p.text = risk['evidence']
        p.font.size = Pt(12)
        p.level = 1
        p.space_after = Pt(6)

    # Opportunities (right column)
    opp_box = slide.shapes.add_textbox(Inches(5.25), Inches(2.5), Inches(4.25), Inches(4))
    opp_frame = opp_box.text_frame

    p = opp_frame.paragraphs[0]
    p.text = "Opportunities"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)

    for opp in thesis['opportunities'][:3]:
        p = opp_frame.add_paragraph()
        p.text = f"{opp['factor']} ({opp['potential']} potential)"
        p.font.size = Pt(14)
        p.font.bold = True
        p.level = 0

        p = opp_frame.add_paragraph()
        p.text = opp['evidence']
        p.font.size = Pt(12)
        p.level = 1
        p.space_after = Pt(6)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    create_target_presentation()
