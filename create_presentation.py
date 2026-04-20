"""
Generate a PowerPoint presentation from analysis data.

Drives off a CompanyConfig so the same module produces decks for any company.
Colors, company name, and output filename come from the config; pillar summary
findings are computed from the timeseries data so they reflect actual numbers
rather than hand-written Target prose.

Organized into 5 Pillars:
1. Growth & Revenue
2. Profitability & Margins
3. Liquidity & Solvency
4. Operational Efficiency
5. Valuation & Risk
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from config_loader import CompanyConfig


# =============================================================================
# CHART CONFIGURATION - 24 charts organized by pillar
# =============================================================================

CHART_CONFIG = {
    "pillar_1": {
        "title": "Growth & Revenue",
        "question": "How is the business growing?",
        "charts": [
            {"title": "Revenue & Net Income (10-Year)", "file": "chart_revenue_netincome_annual.html",
             "description": "10-year revenue and net income trajectory from annual 10-K filings."},
            {"title": "Revenue Growth YoY", "file": "chart_revenue_growth_yoy.html",
             "description": "Year-over-year revenue growth by quarter. Reveals acceleration or deceleration."},
            {"title": "Revenue vs Inventory Growth", "file": "chart_revenue_vs_inventory.html",
             "description": "Inventory growing faster than sales signals potential markdown risk."},
            {"title": "Revenue & Net Income (Quarterly)", "file": "chart_revenue_netincome_longterm.html",
             "description": "Quarterly view with calculated Q4 data showing seasonal patterns."},
        ],
    },
    "pillar_2": {
        "title": "Profitability & Margins",
        "question": "How efficiently is the company generating profits?",
        "charts": [
            {"title": "Margin Analysis (Gross/Operating/Net)", "file": "chart_margin_analysis.html",
             "description": "Three margin lines tracking profitability over time."},
            {"title": "Margin Bridge Waterfall", "file": "chart_margin_bridge.html",
             "description": "Waterfall showing margin evolution quarter-over-quarter."},
            {"title": "Operating Expense Breakdown", "file": "chart_expense_breakdown.html",
             "description": "100% stacked bars of the cost structure."},
            {"title": "EBITDA Bridge", "file": "chart_ebitda_bridge.html",
             "description": "How revenue flows to EBITDA through operating expenses."},
            {"title": "Operating Margin Waterfall", "file": "chart_operating_margin_waterfall.html",
             "description": "Quarterly margin changes as waterfall."},
            {"title": "Earnings Quality", "file": "chart_earnings_quality.html",
             "description": "Net Income vs Operating Cash Flow — high-quality earnings convert to cash."},
        ],
    },
    "pillar_3": {
        "title": "Liquidity & Solvency",
        "question": "Can the company pay its bills today and debts in the future?",
        "charts": [
            {"title": "Current Ratio Gauge", "file": "chart_current_ratio_gauge.html",
             "description": "Short-term liquidity. Below 1.0 is warning; above 1.5 is healthy for retail."},
            {"title": "Capital Structure", "file": "chart_capital_structure_donut.html",
             "description": "Debt vs equity mix."},
            {"title": "Debt-to-EBITDA Trend", "file": "chart_debt_to_ebitda_trend.html",
             "description": "Leverage metric: years of EBITDA to repay debt. Below 3x is healthy."},
            {"title": "Debt Health (Interest Coverage)", "file": "chart_debt_health.html",
             "description": "Interest coverage ratio tracking."},
            {"title": "Statement of Cash Flows", "file": "chart_cash_flows.html",
             "description": "Operating, Investing, Financing cash flows."},
        ],
    },
    "pillar_4": {
        "title": "Operational Efficiency",
        "question": "How well is the company using its assets?",
        "charts": [
            {"title": "DuPont Analysis", "file": "chart_dupont_analysis.html",
             "description": "ROE decomposed into Margin × Asset Turnover × Leverage."},
            {"title": "Inventory Efficiency", "file": "chart_inventory_efficiency.html",
             "description": "Turnover ratio and days on hand."},
            {"title": "Cash Conversion Cycle", "file": "chart_cash_conversion_cycle.html",
             "description": "Days to convert inventory to cash vs peers."},
            {"title": "OCF vs CapEx", "file": "chart_ocf_vs_capex.html",
             "description": "Operating cash vs capital spending. Gap = Free Cash Flow."},
        ],
    },
    "pillar_5": {
        "title": "Valuation & Risk",
        "question": "Is the stock fairly priced, and what are the risks?",
        "charts": [
            {"title": "Valuation vs Growth", "file": "chart_valuation_scatter.html",
             "description": "P/E vs revenue growth vs peers."},
            {"title": "Historical P/E Band", "file": "chart_pe_band.html",
             "description": "Current price vs historical valuation range."},
            {"title": "Cash Flow Sankey", "file": "chart_cash_flow_sankey.html",
             "description": "Cash allocation: CapEx, dividends, buybacks, debt repayment."},
            {"title": "Risk Trends", "file": "chart_risk_trends.html",
             "description": "Risk mentions (shrink, theft, markdown) over time."},
            {"title": "Risk Heatmap", "file": "chart_risk_heatmap_grid.html",
             "description": "Risk type intensity by period."},
        ],
    },
}


# =============================================================================
# DATA-DRIVEN PILLAR SUMMARIES
# =============================================================================

def _first_last(series: List):
    """Return the first and last non-None values in a series, or (None, None)."""
    firsts = [v for v in series if v is not None]
    if not firsts:
        return None, None
    return firsts[0], firsts[-1]


def _min_max(series: List):
    values = [v for v in series if v is not None]
    if not values:
        return None, None
    return min(values), max(values)


def _latest(series: List):
    for v in reversed(series):
        if v is not None:
            return v
    return None


def build_pillar_summaries(timeseries: Dict, cfg: CompanyConfig) -> Dict:
    """
    Compute data-driven findings for each pillar's closing summary slide.
    Fall back to generic placeholder text if a metric is unavailable.
    """
    metrics = timeseries.get('metrics', {})
    name = cfg.short_name

    revenue = metrics.get('revenue', {}).get('net_sales_billion', [])
    rev_first, rev_last = _first_last(revenue)
    rev_growth = f"{((rev_last / rev_first) - 1) * 100:.1f}%" if rev_first and rev_last else "N/A"

    op_margin = metrics.get('margins', {}).get('operating_margin_percent', [])
    op_min, op_max = _min_max(op_margin)
    op_latest = _latest(op_margin)

    gross = metrics.get('margins', {}).get('gross_margin_percent', [])
    gross_latest = _latest(gross)

    roe = metrics.get('debt', {}).get('return_on_equity_percent', [])
    roe_latest = _latest(roe)

    dte = metrics.get('debt', {}).get('debt_to_ebitda_ratio', [])
    dte_latest = _latest(dte)

    ic = metrics.get('debt', {}).get('interest_coverage_ratio', [])
    ic_latest = _latest(ic)

    cr = metrics.get('liquidity', {}).get('current_ratio', [])
    cr_latest = _latest(cr)

    ocf = metrics.get('cash_flows', {}).get('operating_cash_flow_billion', [])
    ocf_latest = _latest(ocf)

    fcf = metrics.get('cash_flows', {}).get('free_cash_flow_billion', [])
    fcf_latest = _latest(fcf)

    inv_turn = metrics.get('inventory', {}).get('inventory_turnover_ratio', [])
    inv_latest = _latest(inv_turn)

    ccc = metrics.get('efficiency', {}).get('cash_conversion_cycle_days', [])
    ccc_latest = _latest(ccc)

    dupont_al = metrics.get('debt', {}).get('dupont_asset_turnover', [])
    dupont_lev = metrics.get('debt', {}).get('dupont_financial_leverage', [])
    dupont_al_latest = _latest(dupont_al)
    dupont_lev_latest = _latest(dupont_lev)

    def fmt(v, suffix="", precision=2):
        return f"{v:.{precision}f}{suffix}" if isinstance(v, (int, float)) else "n/a"

    return {
        "pillar_1": {
            "title": "Growth & Revenue Summary",
            "findings": [
                ("Revenue Trajectory",
                 f"{name} has grown from ${fmt(rev_first, 'B', 1)} to ${fmt(rev_last, 'B', 1)} "
                 f"({rev_growth}) over the covered period."),
                ("Latest Period",
                 f"Most recent quarter / year operating margin: {fmt(op_latest, '%')}. "
                 f"Gross margin: {fmt(gross_latest, '%')}."),
                ("Profitability Range",
                 f"Operating margin has ranged from {fmt(op_min, '%')} to {fmt(op_max, '%')} across the window."),
                ("Inventory Discipline",
                 f"Latest inventory turnover: {fmt(inv_latest, 'x')}. Faster turns ease working-capital needs."),
            ],
        },
        "pillar_2": {
            "title": "Profitability & Margins Summary",
            "findings": [
                ("Margin Recovery" if op_latest and op_max and op_latest >= op_max * 0.9
                 else "Margin Pressure",
                 f"Operating margin at {fmt(op_latest, '%')} vs peak {fmt(op_max, '%')} in the window."),
                ("Gross Margin",
                 f"Latest gross margin: {fmt(gross_latest, '%')}. "
                 f"A stable gross margin is the foundation for predictable earnings."),
                ("Earnings Quality",
                 f"Operating cash flow of ${fmt(ocf_latest, 'B', 1)} in the latest period; "
                 f"OCF tracking net income indicates high-quality earnings."),
                ("EBITDA & D&A",
                 "D&A add-back reveals capital intensity — high D&A signals heavy investment in PP&E."),
            ],
        },
        "pillar_3": {
            "title": "Liquidity & Solvency Summary",
            "findings": [
                ("Current Ratio",
                 f"{fmt(cr_latest, 'x')} — " +
                 ("healthy" if cr_latest and cr_latest >= 1.5 else
                  ("adequate" if cr_latest and cr_latest >= 1.0 else "below retail benchmark"))),
                ("Debt / EBITDA",
                 f"{fmt(dte_latest, 'x')} — " +
                 ("healthy (<3x)" if dte_latest and dte_latest < 3.0 else
                  ("moderate" if dte_latest and dte_latest < 5.0 else "elevated"))),
                ("Interest Coverage",
                 f"{fmt(ic_latest, 'x')} — " +
                 ("strong ability to service debt" if ic_latest and ic_latest >= 3.0 else "requires monitoring")),
                ("Cash Generation",
                 f"Operating cash flow ${fmt(ocf_latest, 'B', 1)} in the latest period provides flexibility."),
            ],
        },
        "pillar_4": {
            "title": "Operational Efficiency Summary",
            "findings": [
                ("DuPont Decomposition",
                 f"Asset turnover {fmt(dupont_al_latest, 'x')} × financial leverage {fmt(dupont_lev_latest, 'x')} "
                 f"drive ROE of {fmt(roe_latest, '%')}."),
                ("Inventory Turnover",
                 f"{fmt(inv_latest, 'x')} turns per year " +
                 (f"(~{365 / inv_latest:.0f} days on hand)" if inv_latest else "")),
                ("Cash Conversion Cycle",
                 f"{fmt(ccc_latest, ' days', 0)} — " +
                 ("efficient" if ccc_latest and ccc_latest < 60 else
                  ("moderate" if ccc_latest and ccc_latest < 90 else "room to improve"))),
                ("Free Cash Flow",
                 f"Latest FCF: ${fmt(fcf_latest, 'B', 1)}. OCF consistently exceeding CapEx funds shareholder returns."),
            ],
        },
        "pillar_5": {
            "title": "Valuation & Risk Summary",
            "findings": [
                ("Valuation",
                 "See P/E band and scatter — current vs historical range reveals whether the stock trades "
                 "at a premium or discount to its own history."),
                ("Risk Factors",
                 "Review the risk trends and heatmap charts for mention frequency of shrink, markdown, "
                 "and margin-pressure themes over time."),
                ("Capital Allocation",
                 "The cash-flow Sankey shows management priorities across CapEx, dividends, buybacks, "
                 "and debt repayment."),
                ("Competitive Position",
                 f"Peers compared: {', '.join(cfg.peers) if cfg.peers else 'none configured'}."),
            ],
        },
    }


# =============================================================================
# THESIS GENERATION
# =============================================================================

def generate_thesis(data: List[Dict], timeseries: Dict) -> Dict:
    """
    Derive a simple BUY / HOLD / SELL thesis from measurable signals:
      - ROE trend, operating margin latest, debt/EBITDA, interest coverage.
    """
    latest_filing = data[-1] if data else {}
    latest_vs = latest_filing.get('vital_signs', {})

    op_margin = latest_vs.get('operating_margin_percent', 0) or 0
    gross_margin = latest_vs.get('gross_margin_percent', 0) or 0

    debt = timeseries.get('metrics', {}).get('debt', {})
    dte = _latest(debt.get('debt_to_ebitda_ratio', []))
    ic = _latest(debt.get('interest_coverage_ratio', []))
    roe = _latest(debt.get('return_on_equity_percent', []))

    # Score signals
    positives = []
    negatives = []

    if op_margin >= 5.0:
        positives.append("operating margin >= 5%")
    elif op_margin < 3.0:
        negatives.append(f"operating margin only {op_margin:.2f}%")

    if dte is not None and dte < 3.0:
        positives.append(f"debt/EBITDA healthy at {dte:.2f}x")
    elif dte is not None and dte > 5.0:
        negatives.append(f"debt/EBITDA elevated at {dte:.2f}x")

    if ic is not None and ic >= 5.0:
        positives.append(f"interest coverage strong at {ic:.2f}x")
    elif ic is not None and ic < 2.0:
        negatives.append(f"interest coverage weak at {ic:.2f}x")

    if roe is not None and roe >= 15:
        positives.append(f"ROE of {roe:.1f}%")
    elif roe is not None and roe < 8:
        negatives.append(f"ROE depressed at {roe:.1f}%")

    if len(positives) >= 3 and not negatives:
        rating = "Buy"
        rationale = "Multiple positive signals: " + ", ".join(positives[:3]) + "."
    elif negatives and len(negatives) > len(positives):
        rating = "Sell"
        rationale = "Concerning signals: " + ", ".join(negatives[:3]) + "."
    else:
        rating = "Hold"
        rationale = ("Mixed signals. Positives: " + ", ".join(positives[:2]) +
                     ". Risks: " + ", ".join(negatives[:2]) if negatives else
                     "Stable but not clearly undervalued.")

    return {
        'recommendation': {'rating': rating, 'rationale': rationale},
        'signals': {'positives': positives, 'negatives': negatives},
    }


# =============================================================================
# MAIN PRESENTATION FUNCTION
# =============================================================================

def _rgb(cfg: CompanyConfig, which: str = 'primary') -> RGBColor:
    rgb = cfg.branding.primary_color_rgb if which == 'primary' else cfg.branding.accent_color_rgb
    return RGBColor(*rgb)


def create_presentation(config: CompanyConfig, analysis_path: str = None,
                        timeseries_path: str = None, output_path: str = None) -> str:
    """Create the PowerPoint deck from analysis outputs. Returns the saved path."""

    analysis_path = analysis_path or config.output_path("analysis.json")
    timeseries_path = timeseries_path or config.output_path("timeseries.json")
    output_path = output_path or config.output_path("Financial_Analysis.pptx")

    with open(analysis_path, 'r') as f:
        full_data = json.load(f)
        data = full_data['filings']

    with open(timeseries_path, 'r') as f:
        timeseries_data = json.load(f)

    print("   Generating data-driven investment thesis...")
    thesis = generate_thesis(data, timeseries_data)

    print("   Computing data-driven pillar summaries...")
    summaries = build_pillar_summaries(timeseries_data, config)

    # Coverage string from actual data
    periods = timeseries_data.get('periods', [])
    coverage = (f"{periods[0]['period']} - {periods[-1]['period']}"
                if periods else "—")

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    print("   Creating introduction slides...")
    _add_title_slide(prs, config, coverage)
    _add_executive_summary(prs, config, data, timeseries_data)
    _add_investment_thesis_slide(prs, config, thesis)

    for pillar_num in range(1, 6):
        key = f"pillar_{pillar_num}"
        pillar = CHART_CONFIG[key]
        print(f"   Creating Pillar {pillar_num}: {pillar['title']}...")
        _add_pillar_section_slide(prs, config, pillar_num, pillar["title"], pillar["question"])
        for chart in pillar["charts"]:
            _add_chart_slide(prs, config, chart["title"], chart["file"], chart["description"])
        _add_pillar_summary_slide(prs, config, pillar_num, summaries[key])

    prs.save(output_path)

    total_charts = sum(len(p["charts"]) for p in CHART_CONFIG.values())
    total_slides = 3 + 5 + total_charts + 5
    print(f"\n   Presentation created: {output_path}")
    print(f"   {total_slides} slides total.")

    return output_path


# =============================================================================
# SLIDE BUILDERS
# =============================================================================

def _add_pillar_summary_slide(prs, cfg, pillar_num, summary_config):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    p = title_box.text_frame.paragraphs[0]
    p.text = summary_config["title"]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = _rgb(cfg)

    findings_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(6))
    findings_box.text_frame.word_wrap = True

    for i, (finding_title, finding_detail) in enumerate(summary_config["findings"]):
        p = findings_box.text_frame.paragraphs[0] if i == 0 else findings_box.text_frame.add_paragraph()
        p.text = finding_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = _rgb(cfg, 'accent')
        p.space_before = Pt(12) if i > 0 else Pt(0)

        p = findings_box.text_frame.add_paragraph()
        p.text = finding_detail
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(80, 80, 80)
        p.space_after = Pt(6)

    indicator = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(9), Inches(0.3))
    p = indicator.text_frame.paragraphs[0]
    p.text = f"Pillar {pillar_num} | Key Takeaways"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(150, 150, 150)
    p.font.italic = True
    p.alignment = PP_ALIGN.RIGHT


def _add_pillar_section_slide(prs, cfg, pillar_num, title, question):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    banner = slide.shapes.add_shape(1, Inches(0), Inches(2.5), Inches(10), Inches(2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = _rgb(cfg)
    banner.line.color.rgb = _rgb(cfg)

    num_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(9), Inches(0.6))
    p = num_box.text_frame.paragraphs[0]
    p.text = f"PILLAR {pillar_num}"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.3), Inches(9), Inches(0.8))
    p = title_box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    q_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(9), Inches(0.5))
    p = q_box.text_frame.paragraphs[0]
    p.text = f'"{question}"'
    p.font.size = Pt(24)
    p.font.italic = True
    p.font.color.rgb = RGBColor(100, 100, 100)
    p.alignment = PP_ALIGN.CENTER


def _add_chart_slide(prs, cfg, title, chart_file, description):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.5))
    p = title_box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = _rgb(cfg)

    image_file = chart_file.replace('.html', '.png')
    image_path = Path(f"output/{image_file}")

    if image_path.exists():
        slide.shapes.add_picture(str(image_path),
                                 left=Inches(0.5), top=Inches(0.8),
                                 width=Inches(9), height=Inches(4.5))

        desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(1.0))
        desc_box.text_frame.word_wrap = True
        p = desc_box.text_frame.paragraphs[0]
        p.text = description
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(100, 100, 100)

        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.6), Inches(9), Inches(0.4))
        p = link_box.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = "Click for interactive version"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 102, 204)
        run.font.underline = True
        chart_path = Path(f"output/{chart_file}").resolve()
        run.hyperlink.address = str(chart_path)
    else:
        desc_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(1.5))
        desc_box.text_frame.word_wrap = True
        p = desc_box.text_frame.paragraphs[0]
        p.text = description
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(60, 60, 60)
        p.space_after = Pt(12)

        link_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.0), Inches(9), Inches(1.0))
        p = link_box.text_frame.paragraphs[0]
        p.text = "Click to view interactive chart:"
        p.font.size = Pt(14)
        p.font.bold = True
        p = link_box.text_frame.add_paragraph()
        chart_path = Path(f"output/{chart_file}").resolve()
        run = p.add_run()
        run.text = f"   {chart_file}"
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0, 0, 255)
        run.font.underline = True
        run.hyperlink.address = str(chart_path)


# =============================================================================
# INTRODUCTION SLIDES
# =============================================================================

def _add_title_slide(prs, cfg, coverage):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1))
    tf = title_box.text_frame
    tf.text = cfg.name
    p = tf.paragraphs[0]
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = _rgb(cfg)
    p.alignment = PP_ALIGN.CENTER

    subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(0.5))
    tf = subtitle_box.text_frame
    tf.text = "Financial Analysis Report"
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    period_box = slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(8), Inches(0.4))
    tf = period_box.text_frame
    tf.text = "5 Pillars of Financial Analysis | 24 Interactive Charts"
    tf.paragraphs[0].font.size = Pt(20)
    tf.paragraphs[0].font.color.rgb = RGBColor(128, 128, 128)
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    coverage_box = slide.shapes.add_textbox(Inches(1), Inches(4.8), Inches(8), Inches(0.4))
    tf = coverage_box.text_frame
    tf.text = f"Data: {coverage}"
    tf.paragraphs[0].font.size = Pt(16)
    tf.paragraphs[0].font.color.rgb = RGBColor(150, 150, 150)
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER


def _add_executive_summary(prs, cfg, data, timeseries):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    p = title_box.text_frame.paragraphs[0]
    p.text = "Executive Summary"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = _rgb(cfg)

    text_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(6))
    tf = text_box.text_frame
    tf.word_wrap = True

    # Baseline = last 10-K; Latest = last filing
    baseline = next((f for f in reversed(data) if f.get('filing_type') == '10-K'),
                    data[0] if data else {})
    baseline_vs = baseline.get('vital_signs', {})
    latest_vs = data[-1].get('vital_signs', {}) if data else {}

    findings = [
        (f"{baseline.get('period', 'Latest Annual')} Baseline", [
            f"Net Sales: ${baseline_vs.get('net_sales_billion', 0) or 0:.2f}B",
            f"Operating Margin: {baseline_vs.get('operating_margin_percent', 0) or 0:.2f}%",
            f"Gross Margin: {baseline_vs.get('gross_margin_percent', 0) or 0:.2f}%",
        ]),
        ("Latest Quarter Highlights", [
            f"Operating Margin: {latest_vs.get('operating_margin_percent', 0) or 0:.2f}%",
            f"Inventory: ${latest_vs.get('inventory_billion', 0) or 0:.2f}B",
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
        p.font.color.rgb = _rgb(cfg)
        p.space_after = Pt(6)

        for bullet in bullets:
            p = tf.add_paragraph()
            p.text = f"   {bullet}"
            p.level = 0
            p.font.size = Pt(14)
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(12)


def _add_investment_thesis_slide(prs, cfg, thesis):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.5))
    p = title_box.text_frame.paragraphs[0]
    p.text = "Investment Thesis"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = _rgb(cfg)

    rec_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(1.2))
    rec_frame = rec_box.text_frame
    rec = thesis['recommendation']

    p = rec_frame.paragraphs[0]
    p.text = f"Recommendation: {rec['rating']}"
    p.font.size = Pt(28)
    p.font.bold = True
    rating_color = (RGBColor(0, 128, 0) if rec['rating'] == 'Buy' else
                    RGBColor(255, 140, 0) if rec['rating'] == 'Hold' else
                    RGBColor(255, 0, 0))
    p.font.color.rgb = rating_color

    p = rec_frame.add_paragraph()
    p.text = rec['rationale']
    p.font.size = Pt(16)
    p.space_after = Pt(6)

    signals = thesis.get('signals', {})

    pos_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(4.25), Inches(4))
    p = pos_box.text_frame.paragraphs[0]
    p.text = "Positive Signals"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)
    for s in signals.get('positives', [])[:5]:
        p = pos_box.text_frame.add_paragraph()
        p.text = f"  • {s}"
        p.font.size = Pt(14)
        p.space_after = Pt(4)
    if not signals.get('positives'):
        p = pos_box.text_frame.add_paragraph()
        p.text = "  (none above threshold)"
        p.font.size = Pt(12)
        p.font.italic = True

    neg_box = slide.shapes.add_textbox(Inches(5.25), Inches(2.5), Inches(4.25), Inches(4))
    p = neg_box.text_frame.paragraphs[0]
    p.text = "Risks / Concerns"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)
    for s in signals.get('negatives', [])[:5]:
        p = neg_box.text_frame.add_paragraph()
        p.text = f"  • {s}"
        p.font.size = Pt(14)
        p.space_after = Pt(4)
    if not signals.get('negatives'):
        p = neg_box.text_frame.add_paragraph()
        p.text = "  (none above threshold)"
        p.font.size = Pt(12)
        p.font.italic = True


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build the financial-analysis deck.")
    parser.add_argument("--config", default="config/target.yaml",
                        help="Path to company YAML config.")
    args = parser.parse_args()
    cfg = CompanyConfig.from_yaml(args.config)
    create_presentation(cfg)


if __name__ == "__main__":
    main()
