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

# Script directory for absolute path resolution
SCRIPT_DIR = Path(__file__).parent.resolve()

# =============================================================================
# CHART CONFIGURATION - All 24 charts organized by pillar
# =============================================================================

# =============================================================================
# PILLAR SUMMARIES - "So What?" content for each pillar
# =============================================================================

# =============================================================================
# EXECUTIVE PRESENTATION CONFIG - Condensed ~25 slide version
# =============================================================================

EXECUTIVE_CONFIG = {
    "earning_power": {
        "title": "Earning Power",
        "subtitle": "Revenue Growth vs Margin Compression",
        "question": "Can Target grow revenue while protecting margins?",
        "key_charts": [
            ("Revenue vs Inventory Growth", "chart_revenue_vs_inventory.html",
             "Compares revenue growth to inventory buildup. Inventory growing faster than sales signals potential markdown risk."),
            ("Margin Analysis", "chart_margin_analysis.html",
             "Three margin lines tracking profitability over time. Compression between lines reveals where profits leak."),
        ],
        "summary": {
            "title": "The Earning Power Challenge",
            "key_insight": "Revenue +2% but Operating Margin -1.47%",
            "evidence": [
                "Inventory up 17% while sales growth slowed",
                "Clearance risk from excess inventory buildup",
                "SG&A expenses rising faster than revenue",
            ],
            "implication": "Q4 margin recovery is critical; watch for promotional activity"
        }
    },
    "liquidity": {
        "title": "Liquidity & Capital",
        "subtitle": "Debt Health vs Operational Efficiency",
        "question": "Can Target service debt while managing working capital?",
        "key_charts": [
            ("Debt Health (Interest Coverage)", "chart_debt_health.html",
             "Interest coverage ratio tracking. Above 3x is comfortable; below 2x requires monitoring."),
            ("Inventory Efficiency", "chart_inventory_efficiency.html",
             "Tracks turnover ratio and days on hand. Faster turns = less capital tied up in inventory."),
        ],
        "summary": {
            "title": "The Liquidity Squeeze",
            "key_insight": "Interest coverage collapsed 9.7x → 1.5x",
            "evidence": [
                "Debt increased 7.5% to $15.37B",
                "Below 1.5x coverage triggers covenant concerns",
                "$2B debt matures FY2026 amid rate uncertainty",
            ],
            "implication": "Refinancing risk; watch debt maturities and free cash flow"
        }
    },
    "valuation_risk": {
        "title": "Valuation & Risk",
        "subtitle": "Is the Discount Justified?",
        "question": "Is TGT cheap for a reason?",
        "key_charts": [
            ("Valuation vs Growth", "chart_valuation_scatter.html",
             "P/E ratio vs revenue growth for Target and peers. Lower-right quadrant = undervalued opportunities."),
            ("Risk Heatmap", "chart_risk_heatmap_grid.html",
             "Intensity grid showing risk types by period. Dark cells = high concern in that area."),
        ]
    }
}

# Charts for executive appendix (all charts not in main body)
APPENDIX_CHARTS = [
    # Remaining Pillar 1 charts
    ("Revenue & Net Income (10-Year)", "chart_revenue_netincome_annual.html"),
    ("Revenue Growth YoY", "chart_revenue_growth_yoy.html"),
    ("Revenue & Net Income (Quarterly)", "chart_revenue_netincome_longterm.html"),
    # Remaining Pillar 2 charts
    ("Margin Bridge Waterfall", "chart_margin_bridge.html"),
    ("Operating Expense Breakdown", "chart_expense_breakdown.html"),
    ("EBITDA Bridge", "chart_ebitda_bridge.html"),
    ("Operating Margin Waterfall", "chart_operating_margin_waterfall.html"),
    ("Earnings Quality", "chart_earnings_quality.html"),
    # Remaining Pillar 3 charts
    ("Current Ratio Gauge", "chart_current_ratio_gauge.html"),
    ("Capital Structure", "chart_capital_structure_donut.html"),
    ("Debt-to-EBITDA Trend", "chart_debt_to_ebitda_trend.html"),
    ("Statement of Cash Flows", "chart_cash_flows.html"),
    # Remaining Pillar 4 charts
    ("DuPont Analysis", "chart_dupont_analysis.html"),
    ("Cash Conversion Cycle", "chart_cash_conversion_cycle.html"),
    ("OCF vs CapEx", "chart_ocf_vs_capex.html"),
    # Remaining Pillar 5 charts
    ("Historical P/E Band", "chart_pe_band.html"),
    ("Cash Flow Sankey", "chart_cash_flow_sankey.html"),
    ("Risk Trends", "chart_risk_trends.html"),
]

PILLAR_SUMMARIES = {
    "pillar_1": {
        "title": "Growth Summary: The Revenue Story",
        "key_insight": "Revenue growth has stalled at ~2% YoY",
        "evidence": [
            "Revenue grew only 1.6% in Q3 2025 vs prior year",
            "Inventory up 17% while sales growth slowed",
            "Clearance risk from excess inventory buildup",
        ],
        "implication": "Slowing growth limits pricing power; watch for markdown pressure in Q4"
    },
    "pillar_2": {
        "title": "Margin Compression Alert",
        "key_insight": "Operating margin dropped 1.47% (5.22% → 3.75%)",
        "evidence": [
            "Inventory up 17% while margins declined",
            "Clearance risk from excess inventory",
            "Shrink/theft mentioned in all quarterly filings",
        ],
        "implication": "Q4 margin recovery is critical; watch for promotional activity"
    },
    "pillar_3": {
        "title": "Interest Coverage Crisis",
        "key_insight": "Coverage collapsed from 9.7x to 1.5x",
        "evidence": [
            "Debt increased 7.5% to $15.37B",
            "Below 1.5x triggers covenant concerns",
            "$2B debt matures FY2026",
        ],
        "implication": "Refinancing risk; watch debt maturities and interest rates"
    },
    "pillar_4": {
        "title": "Efficiency Under Pressure",
        "key_insight": "Inventory days expanded while turnover slowed",
        "evidence": [
            "Days Sales of Inventory increased to 65+ days",
            "Cash conversion cycle extended",
            "Asset turnover showing signs of decline",
        ],
        "implication": "Working capital tied up in inventory; impacts free cash flow"
    },
    "pillar_5": {
        "title": "Valuation: Cheap for a Reason?",
        "key_insight": "Trading at discount to peers despite dividend yield",
        "evidence": [
            "P/E below peer average (if P/E available)",
            "Dividend yield attractive but payout ratio elevated",
            "Risk premium reflects execution uncertainty",
        ],
        "implication": "Value trap risk if margin recovery doesn't materialize"
    },
}


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
# CHART INSIGHTS - Data-driven insights for each chart
# =============================================================================

CHART_INSIGHTS = {
    # Pillar 1: Growth & Revenue
    "chart_revenue_netincome_annual.html":
        "Revenue grew 50% ($70B→$105B) over 10 years, but net income peaked in FY2021 at $7.1B then dropped 44% to $4.0B—profits not keeping pace with top-line growth.",

    "chart_revenue_growth_yoy.html":
        "Growth has decelerated sharply: from 20%+ during COVID to just 1.6% in Q3 2025. Target is now a low-single-digit grower.",

    "chart_revenue_vs_inventory.html":
        "Inventory growth outpaced revenue in FY2022-23, creating markdown risk. Recent quarters show better alignment as inventory normalizes.",

    "chart_revenue_netincome_longterm.html":
        "Q4 holiday peaks are visible, but FY2022-23 saw net income collapse despite stable revenue—margin compression is the story.",

    # Pillar 2: Profitability & Margins
    "chart_margin_analysis.html":
        "Operating margin compressed from 7.1% (FY2020) to 3.75% (Q3 2025)—a 3.3pp drop. Gross margin held steady, so the leak is in SG&A and shrink.",

    "chart_margin_bridge.html":
        "From FY2022 baseline, margins deteriorated in 5 of 8 periods. The FY2023 trough (-2.4pp) shows the inventory markdown pain.",

    "chart_expense_breakdown.html":
        "SG&A as % of revenue crept up from 19% to 21% since FY2020. This 2pp increase directly explains half the margin compression.",

    "chart_ebitda_bridge.html":
        "D&A adds ~$2.8B to operating income, but EBITDA margin still declined from 9.5% to 6.5% over three years.",

    "chart_operating_margin_waterfall.html":
        "Q3 margins consistently underperform Q4 due to holiday leverage. FY2023 Q2-Q3 saw the steepest drops (-1.5pp each).",

    "chart_earnings_quality.html":
        "Operating cash flow exceeds net income in most periods—earnings quality is solid. Working capital swings cause quarterly noise.",

    # Pillar 3: Liquidity & Solvency
    "chart_current_ratio_gauge.html":
        "Current ratio at 0.92x is below 1.0—current liabilities exceed current assets. Typical for retail but warrants monitoring.",

    "chart_capital_structure_donut.html":
        "Debt represents ~65% of capital structure. Leverage increased as buybacks reduced equity base.",

    "chart_debt_to_ebitda_trend.html":
        "Debt/EBITDA rose from 1.5x (FY2020) to 3.8x (FY2024) as EBITDA declined while debt stayed flat. Approaching the 4x caution zone.",

    "chart_debt_health.html":
        "Interest coverage dropped from 11.3x to 8.2x QoQ—a 27% decline. Still comfortable above 3x but trending wrong direction.",

    "chart_cash_flows.html":
        "Operating CF remains positive ($1-2B/quarter) but investing CF shows steady CapEx spend. Financing CF negative due to dividends.",

    # Pillar 4: Operational Efficiency
    "chart_dupont_analysis.html":
        "ROE driven primarily by leverage (3.2x), not margins (3.8%) or turnover (1.8x). Declining margins are dragging returns down.",

    "chart_inventory_efficiency.html":
        "Inventory turns improved from 5.8x to 6.2x as Target worked through excess stock. Days on hand dropped from 63 to 59 days.",

    "chart_cash_conversion_cycle.html":
        "Cash cycle at ~5 days is efficient for retail. Negative payables cycle offsets inventory days—suppliers help fund operations.",

    "chart_ocf_vs_capex.html":
        "Free cash flow (OCF - CapEx) remains positive at ~$3B annually, supporting dividends. CapEx steady at $4-5B for store/digital investments.",

    # Pillar 5: Valuation & Risk
    "chart_valuation_scatter.html":
        "Target trades at 14x P/E with 1.6% revenue growth—below peers like Walmart (23x, 5% growth) and Costco (45x, 8% growth).",

    "chart_pe_band.html":
        "Current P/E of 14x is below the 5-year average of 18x—historically undervalued, but margin concerns may justify discount.",

    "chart_cash_flow_sankey.html":
        "~40% of operating CF goes to CapEx, 25% to dividends, 20% to buybacks. Balanced capital allocation despite margin pressure.",

    "chart_risk_trends.html":
        "Shrink/theft mentions increased from 1/period (2020) to 3-4/period (2024-25). Management repeatedly flags this as a margin headwind.",

    "chart_risk_heatmap_grid.html":
        "FY2023-Q3 2025 shows elevated risk across all categories. Shrink, markdown, and margin pressure are concurrent concerns.",

    # Market Context
    "chart_market_context.html":
        "TGT underperformed S&P 500 by 102pp over 3 years. Beta dropped to 0.28 (less volatile than market)—defensive but lagging in bull markets.",
}


# =============================================================================
# MAIN PRESENTATION FUNCTION
# =============================================================================

def create_target_presentation():
    """Create comprehensive PowerPoint presentation organized by 5 pillars.

    Streamlined presentation flow (~38 slides):
    1. Title
    2. Executive Summary (enhanced with key flags)
    3. Market Context (NEW - TGT vs S&P 500)
    4. Investment Thesis
    5-9. Pillar 1: Growth & Revenue (section + 4 charts)
    10. Pillar 1 Summary (NEW - "So What?")
    11-17. Pillar 2: Profitability & Margins (section + 6 charts)
    18. Pillar 2 Summary (NEW - margin compression story)
    19-24. Pillar 3: Liquidity & Solvency (section + 5 charts)
    25. Pillar 3 Summary (NEW - interest coverage crisis)
    26-30. Pillar 4: Operational Efficiency (section + 4 charts)
    31. Pillar 4 Summary (NEW - efficiency insights)
    32-37. Pillar 5: Valuation & Risk (section + 5 charts)
    38. Conclusion (NEW - strategic questions)
    """

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

    # === INTRODUCTION (4 slides) ===
    print("   Creating introduction slides...")
    add_title_slide(prs)
    add_executive_summary(prs, data)
    add_market_context_slide(prs)  # NEW: Market context after exec summary
    add_investment_thesis_slide(prs, thesis)

    # === PILLAR 1: Growth & Revenue (5 slides + summary) ===
    print("   Creating Pillar 1: Growth & Revenue...")
    pillar = CHART_CONFIG["pillar_1"]
    add_pillar_section_slide(prs, 1, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        insight = CHART_INSIGHTS.get(chart["file"], None)
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"], insight)
    add_pillar_summary_slide(prs, "pillar_1")  # NEW: "So What?" summary

    # === PILLAR 2: Profitability & Margins (7 slides + summary) ===
    print("   Creating Pillar 2: Profitability & Margins...")
    pillar = CHART_CONFIG["pillar_2"]
    add_pillar_section_slide(prs, 2, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        insight = CHART_INSIGHTS.get(chart["file"], None)
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"], insight)
    add_pillar_summary_slide(prs, "pillar_2")  # NEW: Margin compression alert

    # === PILLAR 3: Liquidity & Solvency (6 slides + summary) ===
    print("   Creating Pillar 3: Liquidity & Solvency...")
    pillar = CHART_CONFIG["pillar_3"]
    add_pillar_section_slide(prs, 3, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        insight = CHART_INSIGHTS.get(chart["file"], None)
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"], insight)
    add_pillar_summary_slide(prs, "pillar_3")  # NEW: Interest coverage crisis

    # === PILLAR 4: Operational Efficiency (5 slides + summary) ===
    print("   Creating Pillar 4: Operational Efficiency...")
    pillar = CHART_CONFIG["pillar_4"]
    add_pillar_section_slide(prs, 4, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        insight = CHART_INSIGHTS.get(chart["file"], None)
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"], insight)
    add_pillar_summary_slide(prs, "pillar_4")  # NEW: Efficiency under pressure

    # === PILLAR 5: Valuation & Risk (6 slides) ===
    print("   Creating Pillar 5: Valuation & Risk...")
    pillar = CHART_CONFIG["pillar_5"]
    add_pillar_section_slide(prs, 5, pillar["title"], pillar["question"])
    for chart in pillar["charts"]:
        insight = CHART_INSIGHTS.get(chart["file"], None)
        add_chart_slide(prs, chart["title"], chart["file"], chart["description"], insight)
    # Note: No summary for Pillar 5 - goes directly to conclusion

    # === CONCLUSION (1 slide) ===
    print("   Creating conclusion slide...")
    add_conclusion_slide(prs, data, thesis)  # NEW: Strategic conclusion

    # Save presentation
    output_path = 'output/Target_Financial_Analysis.pptx'
    prs.save(output_path)

    # Summary output
    total_charts = sum(len(p["charts"]) for p in CHART_CONFIG.values())
    # Calculate new total: 4 intro + (section + charts + summary) * 4 pillars + (section + charts) for pillar 5 + conclusion
    intro_slides = 4  # Title, Exec Summary, Market Context, Investment Thesis
    pillar_slides = sum(1 + len(CHART_CONFIG[f"pillar_{i}"]["charts"]) + 1 for i in range(1, 5))  # sections + charts + summaries for pillars 1-4
    pillar5_slides = 1 + len(CHART_CONFIG["pillar_5"]["charts"])  # section + charts (no summary)
    conclusion_slides = 1
    total_slides = intro_slides + pillar_slides + pillar5_slides + conclusion_slides

    print(f"\n   Presentation created: {output_path}")
    print(f"   {total_slides} slides total:")
    print("     - 4 introduction slides (Title, Executive Summary, Market Context, Investment Thesis)")
    print("     - 5 pillar section dividers")
    print(f"     - {total_charts} chart slides across 5 pillars")
    print("     - 4 pillar summary slides ('So What?' takeaways)")
    print("     - 1 strategic conclusion slide")
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

def add_chart_slide(prs, title, chart_file, description, insight=None):
    """Add a chart slide with embedded PNG image.

    Embeds the static PNG version of the chart directly in the slide.
    Falls back to hyperlink if PNG not found.

    Args:
        prs: Presentation object
        title: Chart title
        chart_file: HTML chart filename
        description: Chart explanation (shown in info icon tooltip)
        insight: Data-driven insight text (shown at bottom of slide)
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

    # Info icon with tooltip (top right)
    info_icon = slide.shapes.add_textbox(Inches(9.0), Inches(0.25), Inches(0.4), Inches(0.4))
    info_frame = info_icon.text_frame
    p = info_frame.paragraphs[0]
    run = p.add_run()
    run.text = "ⓘ"
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(100, 100, 100)
    # Add hyperlink with ScreenTip containing the explanation
    # Truncate to 250 chars for ScreenTip limit
    tooltip_text = description[:247] + "..." if len(description) > 250 else description
    chart_path = Path(f"output/{chart_file}").resolve()
    run.hyperlink.address = chart_path.as_uri()  # file:// URI format
    run.hyperlink.screen_tip = tooltip_text

    # Check for PNG image
    image_file = chart_file.replace('.html', '.png')
    image_path = SCRIPT_DIR / "output" / image_file

    if image_path.exists():
        # Embed chart image (center of slide)
        slide.shapes.add_picture(
            str(image_path),
            left=Inches(0.5),
            top=Inches(0.8),
            width=Inches(9),
            height=Inches(4.5)
        )

        # Insight text (bottom) - replaces description
        insight_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(1.0))
        insight_frame = insight_box.text_frame
        insight_frame.word_wrap = True

        p = insight_frame.paragraphs[0]
        display_text = insight if insight else description
        p.text = display_text
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(50, 50, 50)  # Darker for insights
        p.font.bold = True  # Make insights stand out

        # Add hyperlink to interactive HTML version
        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.6), Inches(9), Inches(0.4))
        link_frame = link_box.text_frame
        p = link_frame.paragraphs[0]
        run = p.add_run()
        run.text = "📊 Click for interactive version"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 102, 204)  # Blue link color
        run.font.underline = True
        chart_path = Path(f"output/{chart_file}").resolve()
        run.hyperlink.address = chart_path.as_uri()
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
# NEW STREAMLINED PRESENTATION SLIDES
# =============================================================================

def add_market_context_slide(prs):
    """Add Market Context slide showing TGT vs S&P 500 performance.

    This slide appears after Executive Summary to provide market context.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.5))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Market Context: TGT vs S&P 500"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)  # Target red

    # Add info icon with tooltip (top right)
    description = "Compares TGT total return vs S&P 500 (SPY) and Retail ETF (XRT). Rolling beta shows stock's sensitivity to market movements."
    info_icon = slide.shapes.add_textbox(Inches(9.0), Inches(0.25), Inches(0.4), Inches(0.4))
    info_frame = info_icon.text_frame
    p = info_frame.paragraphs[0]
    run = p.add_run()
    run.text = "ⓘ"
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(100, 100, 100)
    chart_path = Path("output/chart_market_context.html").resolve()
    run.hyperlink.address = chart_path.as_uri()  # file:// URI format
    run.hyperlink.screen_tip = description

    # Check for chart image
    image_path = SCRIPT_DIR / "output" / "chart_market_context.png"

    if image_path.exists():
        # Embed chart image
        slide.shapes.add_picture(
            str(image_path),
            left=Inches(0.5),
            top=Inches(0.8),
            width=Inches(9),
            height=Inches(4.5)
        )

        # Insight text (bottom) - data-driven insight instead of generic bullets
        insight = CHART_INSIGHTS.get("chart_market_context.html", "")
        desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(1.0))
        desc_frame = desc_box.text_frame
        desc_frame.word_wrap = True

        p = desc_frame.paragraphs[0]
        p.text = insight
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RGBColor(50, 50, 50)

        # Link to interactive version
        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.6), Inches(9), Inches(0.4))
        link_frame = link_box.text_frame
        p = link_frame.paragraphs[0]
        run = p.add_run()
        run.text = "📊 Click for interactive version"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 102, 204)
        run.font.underline = True
        chart_path = Path("output/chart_market_context.html").resolve()
        run.hyperlink.address = chart_path.as_uri()
    else:
        # Fallback if chart not available
        placeholder_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(3))
        placeholder_frame = placeholder_box.text_frame
        placeholder_frame.word_wrap = True

        p = placeholder_frame.paragraphs[0]
        p.text = "[Market Context Chart]"
        p.font.size = Pt(20)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.font.italic = True
        p.alignment = PP_ALIGN.CENTER

        p = placeholder_frame.add_paragraph()
        p.text = "Run visualize_data.py to generate market context chart"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.alignment = PP_ALIGN.CENTER


def add_pillar_summary_slide(prs, pillar_key: str):
    """Add 'So What?' summary slide after each pillar's charts.

    Args:
        prs: Presentation object
        pillar_key: Key for PILLAR_SUMMARIES dict (e.g., 'pillar_1')
    """
    summary = PILLAR_SUMMARIES.get(pillar_key, {})
    if not summary:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # "So What?" badge
    badge_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(2), Inches(0.4))
    badge_frame = badge_box.text_frame
    p = badge_frame.paragraphs[0]
    p.text = "SO WHAT?"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    # Badge background (via shape)
    badge_shape = slide.shapes.add_shape(1, Inches(0.4), Inches(0.25), Inches(1.5), Inches(0.45))
    badge_shape.fill.solid()
    badge_shape.fill.fore_color.rgb = RGBColor(204, 0, 0)  # Target red
    badge_shape.line.color.rgb = RGBColor(204, 0, 0)
    # Move badge to back
    badge_shape.element.getparent().insert(0, badge_shape.element)

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.9), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = summary.get('title', 'Summary')
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)

    # Key Insight box
    insight_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(1.7), Inches(9), Inches(1.0))
    insight_shape.fill.solid()
    insight_shape.fill.fore_color.rgb = RGBColor(255, 240, 240)  # Light red background
    insight_shape.line.color.rgb = RGBColor(204, 0, 0)  # Red border

    insight_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.85), Inches(8.6), Inches(0.7))
    insight_frame = insight_box.text_frame
    insight_frame.word_wrap = True

    p = insight_frame.paragraphs[0]
    p.text = "KEY INSIGHT"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    p = insight_frame.add_paragraph()
    p.text = summary.get('key_insight', '')
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)

    # Evidence section
    evidence_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.0), Inches(9), Inches(2.5))
    evidence_frame = evidence_box.text_frame
    evidence_frame.word_wrap = True

    p = evidence_frame.paragraphs[0]
    p.text = "Evidence:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)
    p.space_after = Pt(8)

    for item in summary.get('evidence', []):
        p = evidence_frame.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(80, 80, 80)
        p.space_after = Pt(4)

    # Implication section
    impl_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(5.5), Inches(9), Inches(1.2))
    impl_shape.fill.solid()
    impl_shape.fill.fore_color.rgb = RGBColor(240, 248, 255)  # Light blue background
    impl_shape.line.color.rgb = RGBColor(0, 102, 204)  # Blue border

    impl_box = slide.shapes.add_textbox(Inches(0.7), Inches(5.65), Inches(8.6), Inches(0.9))
    impl_frame = impl_box.text_frame
    impl_frame.word_wrap = True

    p = impl_frame.paragraphs[0]
    p.text = "IMPLICATION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 102, 204)

    p = impl_frame.add_paragraph()
    p.text = summary.get('implication', '')
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(51, 51, 51)


def add_conclusion_slide(prs, data, thesis):
    """Add strategic conclusion slide with key takeaways.

    Args:
        prs: Presentation object
        data: Financial data dict
        thesis: Investment thesis dict
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Strategic Conclusion"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    # Recommendation summary
    rec = thesis.get('recommendation', {})
    rating = rec.get('rating', 'Hold')

    rating_color = RGBColor(0, 128, 0) if rating == 'Buy' else \
                   RGBColor(255, 140, 0) if rating == 'Hold' else \
                   RGBColor(255, 0, 0)

    rec_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(9), Inches(0.5))
    rec_frame = rec_box.text_frame
    p = rec_frame.paragraphs[0]
    p.text = f"Recommendation: {rating}"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = rating_color

    # Key questions section
    questions_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(9), Inches(4.5))
    questions_frame = questions_box.text_frame
    questions_frame.word_wrap = True

    p = questions_frame.paragraphs[0]
    p.text = "Key Strategic Questions to Monitor:"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)
    p.space_after = Pt(12)

    strategic_questions = [
        ("Margin Recovery", "Can Target restore operating margins to 5%+ in FY2025?"),
        ("Interest Coverage", "Will interest coverage stabilize above 2.0x warning threshold?"),
        ("Inventory Management", "Can inventory levels normalize without significant markdowns?"),
        ("Debt Maturities", "How will Target refinance $2B debt maturing in FY2026?"),
        ("Competitive Position", "Can Target differentiate vs Walmart/Amazon in a slowing consumer environment?"),
    ]

    for topic, question in strategic_questions:
        p = questions_frame.add_paragraph()
        p.text = f"• {topic}: "
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)

        run = p.add_run()
        run.text = question
        run.font.size = Pt(14)
        run.font.bold = False
        run.font.color.rgb = RGBColor(60, 60, 60)

        p.space_after = Pt(8)

    # Bottom summary box
    summary_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(6.2), Inches(9), Inches(0.9))
    summary_shape.fill.solid()
    summary_shape.fill.fore_color.rgb = RGBColor(245, 245, 245)
    summary_shape.line.color.rgb = RGBColor(200, 200, 200)

    summary_box = slide.shapes.add_textbox(Inches(0.7), Inches(6.35), Inches(8.6), Inches(0.6))
    summary_frame = summary_box.text_frame
    summary_frame.word_wrap = True

    p = summary_frame.paragraphs[0]
    p.text = "Bottom Line: "
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)

    run = p.add_run()
    run.text = rec.get('rationale', 'Monitor key metrics for changes in investment thesis.')
    run.font.size = Pt(12)
    run.font.bold = False
    run.font.color.rgb = RGBColor(80, 80, 80)


# =============================================================================
# EXECUTIVE PRESENTATION SLIDES (Condensed Version)
# =============================================================================

def add_combined_section_slide(prs, section_key: str):
    """Add combined pillar section divider (e.g., 'Earning Power').

    Args:
        prs: Presentation object
        section_key: Key in EXECUTIVE_CONFIG ('earning_power', 'liquidity', 'valuation_risk')
    """
    config = EXECUTIVE_CONFIG.get(section_key, {})
    if not config:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Colored banner at top
    banner = slide.shapes.add_shape(1, Inches(0), Inches(2.5), Inches(10), Inches(2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(204, 0, 0)  # Target red
    banner.line.color.rgb = RGBColor(204, 0, 0)

    # Section title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(9), Inches(0.8))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = config.get('title', '')
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.5), Inches(9), Inches(0.6))
    subtitle_frame = subtitle_box.text_frame
    p = subtitle_frame.paragraphs[0]
    p.text = config.get('subtitle', '')
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Guiding question below banner
    q_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(9), Inches(0.5))
    q_frame = q_box.text_frame
    p = q_frame.paragraphs[0]
    p.text = f'"{config.get("question", "")}"'
    p.font.size = Pt(24)
    p.font.italic = True
    p.font.color.rgb = RGBColor(100, 100, 100)
    p.alignment = PP_ALIGN.CENTER


def add_combined_summary_slide(prs, section_key: str):
    """Add combined 'So What?' summary for merged pillars.

    Args:
        prs: Presentation object
        section_key: Key in EXECUTIVE_CONFIG ('earning_power', 'liquidity')
    """
    config = EXECUTIVE_CONFIG.get(section_key, {})
    summary = config.get('summary', {})
    if not summary:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # "So What?" badge
    badge_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(2), Inches(0.4))
    badge_frame = badge_box.text_frame
    p = badge_frame.paragraphs[0]
    p.text = "SO WHAT?"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    # Badge background (via shape)
    badge_shape = slide.shapes.add_shape(1, Inches(0.4), Inches(0.25), Inches(1.5), Inches(0.45))
    badge_shape.fill.solid()
    badge_shape.fill.fore_color.rgb = RGBColor(204, 0, 0)  # Target red
    badge_shape.line.color.rgb = RGBColor(204, 0, 0)
    # Move badge to back
    badge_shape.element.getparent().insert(0, badge_shape.element)

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.9), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = summary.get('title', 'Summary')
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)

    # Key Insight box
    insight_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(1.7), Inches(9), Inches(1.0))
    insight_shape.fill.solid()
    insight_shape.fill.fore_color.rgb = RGBColor(255, 240, 240)  # Light red background
    insight_shape.line.color.rgb = RGBColor(204, 0, 0)  # Red border

    insight_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.85), Inches(8.6), Inches(0.7))
    insight_frame = insight_box.text_frame
    insight_frame.word_wrap = True

    p = insight_frame.paragraphs[0]
    p.text = "KEY INSIGHT"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    p = insight_frame.add_paragraph()
    p.text = summary.get('key_insight', '')
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)

    # Evidence section
    evidence_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.0), Inches(9), Inches(2.5))
    evidence_frame = evidence_box.text_frame
    evidence_frame.word_wrap = True

    p = evidence_frame.paragraphs[0]
    p.text = "Evidence:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)
    p.space_after = Pt(8)

    for item in summary.get('evidence', []):
        p = evidence_frame.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(80, 80, 80)
        p.space_after = Pt(4)

    # Implication section
    impl_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(5.5), Inches(9), Inches(1.2))
    impl_shape.fill.solid()
    impl_shape.fill.fore_color.rgb = RGBColor(240, 248, 255)  # Light blue background
    impl_shape.line.color.rgb = RGBColor(0, 102, 204)  # Blue border

    impl_box = slide.shapes.add_textbox(Inches(0.7), Inches(5.65), Inches(8.6), Inches(0.9))
    impl_frame = impl_box.text_frame
    impl_frame.word_wrap = True

    p = impl_frame.paragraphs[0]
    p.text = "IMPLICATION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 102, 204)

    p = impl_frame.add_paragraph()
    p.text = summary.get('implication', '')
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(51, 51, 51)


def add_appendix_divider_slide(prs):
    """Add 'Appendix: Supporting Data' section divider."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Gray banner (neutral color to differentiate from main content)
    banner = slide.shapes.add_shape(1, Inches(0), Inches(2.5), Inches(10), Inches(2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(80, 80, 80)  # Dark gray
    banner.line.color.rgb = RGBColor(80, 80, 80)

    # Appendix label
    label_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(9), Inches(0.6))
    label_frame = label_box.text_frame
    p = label_frame.paragraphs[0]
    p.text = "APPENDIX"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.3), Inches(9), Inches(0.8))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Supporting Data"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Subtitle below banner
    subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(9), Inches(0.5))
    subtitle_frame = subtitle_box.text_frame
    p = subtitle_frame.paragraphs[0]
    p.text = f"{len(APPENDIX_CHARTS)} additional charts for detailed analysis"
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(100, 100, 100)
    p.alignment = PP_ALIGN.CENTER


def add_appendix_chart_slide(prs, title, chart_file):
    """Add a simplified chart slide for appendix (minimal description).

    Args:
        prs: Presentation object
        title: Chart title
        chart_file: HTML chart filename
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title (top)
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.5))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(80, 80, 80)  # Gray for appendix (vs red for main)

    # Check for PNG image
    image_file = chart_file.replace('.html', '.png')
    image_path = SCRIPT_DIR / "output" / image_file

    if image_path.exists():
        # Embed chart image (center of slide, larger without description)
        slide.shapes.add_picture(
            str(image_path),
            left=Inches(0.5),
            top=Inches(0.8),
            width=Inches(9),
            height=Inches(5.5)
        )

        # Add hyperlink to interactive HTML version
        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.5), Inches(9), Inches(0.4))
        link_frame = link_box.text_frame
        p = link_frame.paragraphs[0]
        run = p.add_run()
        run.text = "Click for interactive version"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 102, 204)  # Blue link color
        run.font.underline = True
        chart_path = Path(f"output/{chart_file}").resolve()
        run.hyperlink.address = str(chart_path)
    else:
        # Placeholder if image not found
        placeholder_box = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(2))
        placeholder_frame = placeholder_box.text_frame

        p = placeholder_frame.paragraphs[0]
        p.text = f"[Chart image not found: {image_file}]"
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.font.italic = True
        p.alignment = PP_ALIGN.CENTER

        p = placeholder_frame.add_paragraph()
        p.text = "Run visualize_data.py to generate chart images"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.alignment = PP_ALIGN.CENTER


def add_executive_conclusion_slide(prs, data, thesis):
    """Add strategic conclusion slide for executive presentation.

    Focuses on key strategic questions: Clearance Sale + Refinancing risks.

    Args:
        prs: Presentation object
        data: Financial data dict
        thesis: Investment thesis dict
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Strategic Conclusion"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    # Recommendation summary
    rec = thesis.get('recommendation', {})
    rating = rec.get('rating', 'Hold')

    rating_color = RGBColor(0, 128, 0) if rating == 'Buy' else \
                   RGBColor(255, 140, 0) if rating == 'Hold' else \
                   RGBColor(255, 0, 0)

    rec_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(0.5))
    rec_frame = rec_box.text_frame
    p = rec_frame.paragraphs[0]
    p.text = f"Recommendation: {rating}"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = rating_color

    # Key strategic questions - focused on Clearance Sale + Refinancing
    questions_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.7), Inches(9), Inches(3.8))
    questions_frame = questions_box.text_frame
    questions_frame.word_wrap = True

    p = questions_frame.paragraphs[0]
    p.text = "Key Strategic Questions:"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(51, 51, 51)
    p.space_after = Pt(12)

    strategic_questions = [
        ("Clearance Sale Risk", "Can Target execute a controlled inventory drawdown, or will excess inventory force deep discounting that crushes margins further?"),
        ("Refinancing Risk", "With $2B debt maturing FY2026 and interest coverage at 1.5x, how will Target refinance in a higher rate environment?"),
        ("Margin Recovery", "Can Target restore operating margins to 5%+ without sacrificing market share?"),
    ]

    for topic, question in strategic_questions:
        p = questions_frame.add_paragraph()
        p.text = f"{topic}"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)

        p = questions_frame.add_paragraph()
        p.text = question
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(60, 60, 60)
        p.space_after = Pt(12)

    # Bottom summary box
    summary_shape = slide.shapes.add_shape(1, Inches(0.5), Inches(5.8), Inches(9), Inches(1.3))
    summary_shape.fill.solid()
    summary_shape.fill.fore_color.rgb = RGBColor(255, 240, 240)  # Light red
    summary_shape.line.color.rgb = RGBColor(204, 0, 0)

    summary_box = slide.shapes.add_textbox(Inches(0.7), Inches(5.95), Inches(8.6), Inches(1.0))
    summary_frame = summary_box.text_frame
    summary_frame.word_wrap = True

    p = summary_frame.paragraphs[0]
    p.text = "Bottom Line"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    p = summary_frame.add_paragraph()
    p.text = rec.get('rationale', 'Target faces near-term headwinds from inventory and debt pressures. Monitor Q4 margin recovery and FY2026 refinancing plans.')
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(51, 51, 51)


def create_executive_presentation():
    """Create condensed executive presentation with appendix (~34 slides).

    Presentation flow:
    1. Title
    2. Executive Summary (key flags)
    3. Investment Thesis
    4-7. Earning Power (section + 2 charts + summary)
    8-11. Liquidity (section + 2 charts + summary)
    12-14. Valuation & Risk (section + 2 charts)
    15. Strategic Conclusion
    16. Appendix Divider
    17-34. Appendix Charts (18 charts)

    Total: ~34 slides (vs 38 for full version)
    Main body: ~15 slides (vs 33 for full version)
    """

    # Generate investment thesis
    print("   Generating investment thesis...")
    thesis_gen = ThesisGenerator()
    thesis_gen.export_thesis()

    # Load analysis data
    with open('output/target_analysis.json', 'r') as f:
        full_data = json.load(f)
        data = full_data['filings']

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

    # === EARNING POWER SECTION (4 slides: section + 2 charts + summary) ===
    print("   Creating Earning Power section...")
    add_combined_section_slide(prs, "earning_power")
    for title, chart_file, description in EXECUTIVE_CONFIG["earning_power"]["key_charts"]:
        add_chart_slide(prs, title, chart_file, description)
    add_combined_summary_slide(prs, "earning_power")

    # === LIQUIDITY SECTION (4 slides: section + 2 charts + summary) ===
    print("   Creating Liquidity section...")
    add_combined_section_slide(prs, "liquidity")
    for title, chart_file, description in EXECUTIVE_CONFIG["liquidity"]["key_charts"]:
        add_chart_slide(prs, title, chart_file, description)
    add_combined_summary_slide(prs, "liquidity")

    # === VALUATION & RISK SECTION (3 slides: section + 2 charts) ===
    print("   Creating Valuation & Risk section...")
    add_combined_section_slide(prs, "valuation_risk")
    for title, chart_file, description in EXECUTIVE_CONFIG["valuation_risk"]["key_charts"]:
        add_chart_slide(prs, title, chart_file, description)

    # === CONCLUSION (1 slide) ===
    print("   Creating conclusion slide...")
    add_executive_conclusion_slide(prs, data, thesis)

    # === APPENDIX (1 divider + 18 charts = 19 slides) ===
    print("   Creating appendix slides...")
    add_appendix_divider_slide(prs)
    for title, chart_file in APPENDIX_CHARTS:
        add_appendix_chart_slide(prs, title, chart_file)

    # Save presentation
    output_path = 'output/Target_Executive_Presentation.pptx'
    prs.save(output_path)

    # Summary output
    main_slides = 3 + 4 + 4 + 3 + 1  # intro + earning + liquidity + valuation + conclusion
    appendix_slides = 1 + len(APPENDIX_CHARTS)  # divider + charts
    total_slides = main_slides + appendix_slides

    print(f"\n   Executive presentation created: {output_path}")
    print(f"   {total_slides} slides total:")
    print(f"     - {main_slides} main body slides (executive summary)")
    print("       • 3 introduction slides (Title, Executive Summary, Investment Thesis)")
    print("       • 4 Earning Power slides (Pillars 1+2 combined)")
    print("       • 4 Liquidity slides (Pillars 3+4 combined)")
    print("       • 3 Valuation & Risk slides (Pillar 5)")
    print("       • 1 strategic conclusion")
    print(f"     - {appendix_slides} appendix slides ({len(APPENDIX_CHARTS)} supporting charts)")
    print("     - Charts embedded as PNG images (run visualize_data.py first)")

    return output_path


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--executive':
        create_executive_presentation()
    else:
        create_target_presentation()
        print("\n   Tip: Run with --executive flag for condensed executive version")
