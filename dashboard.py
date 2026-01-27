#!/usr/bin/env python3
"""
Target Corporation Financial Analysis Dashboard

Interactive visualization of 24 key financial metrics across 6 pillars:
1. Revenue & Growth
2. Profitability & Margins
3. Liquidity & Solvency
4. Operational Efficiency
5. Cash Flow Dynamics
6. Valuation & Risk

Run: streamlit run dashboard.py
"""

import streamlit as st
from visualize_data import (
    load_timeseries_data,
    # Pillar 1: Revenue & Growth (4 charts)
    create_revenue_netincome_annual_chart,
    create_revenue_growth_yoy_chart,
    create_revenue_vs_inventory_chart,
    create_revenue_netincome_longterm_chart,
    # Pillar 2: Profitability & Margins (5 charts)
    create_margin_analysis_chart,
    create_margin_bridge_waterfall,
    create_expense_breakdown_chart,
    create_ebitda_bridge_waterfall,
    create_earnings_quality_chart,
    # Pillar 3: Liquidity & Solvency (4 charts)
    create_current_ratio_gauge,
    create_capital_structure_donut,
    create_debt_to_ebitda_trend,
    create_debt_health_chart,
    # Pillar 4: Operational Efficiency (4 charts)
    create_dupont_analysis_breakdown,
    create_cash_conversion_cycle_chart,
    create_inventory_efficiency_chart,
    create_operating_margin_waterfall,
    # Pillar 5: Cash Flow Dynamics (3 charts)
    create_ocf_vs_capex_chart,
    create_cash_flow_sankey,
    create_cash_flows_chart,
    # Pillar 6: Valuation & Risk (4 charts)
    create_valuation_vs_growth_scatter,
    create_pe_band_area_chart,
    create_risk_trends_chart,
    create_risk_heatmap_grid,
)

# =============================================================================
# CHART EXPLANATIONS
# =============================================================================
# Each chart gets a brief thesis explaining what it shows and key insights

CHART_EXPLANATIONS = {
    # Pillar 1: Revenue & Growth
    "revenue_netincome_annual": """
**What it shows:** Target's 10-year revenue and net income trajectory from annual 10-K filings.

**Key insight:** Look for consistent growth and whether profits keep pace with revenue. Widening gap between lines suggests margin compression.
""",
    "revenue_growth_yoy": """
**What it shows:** Year-over-year revenue growth rates by quarter, revealing acceleration or deceleration in growth momentum.

**Key insight:** Consistent positive growth indicates healthy demand. Negative quarters may signal competitive pressure or macro headwinds.
""",
    "revenue_vs_inventory": """
**What it shows:** Compares revenue growth to inventory growth over time.

**Key insight:** Inventory growing faster than sales signals potential markdown risk and working capital strain. The lines should track closely.
""",
    "revenue_netincome_longterm": """
**What it shows:** Quarterly revenue and net income with calculated Q4 data, revealing seasonal patterns.

**Key insight:** Q4 (holiday season) typically shows peak revenue. Watch for profit volatility vs revenue stability.
""",

    # Pillar 2: Profitability & Margins
    "margin_analysis": """
**What it shows:** Three margin lines - Gross, Operating, and Net Profit margins over time.

**Key insight:** Compression between lines reveals where profits leak. Gross margin erosion = pricing/cost issues. Operating margin erosion = overhead creep.
""",
    "margin_bridge": """
**What it shows:** Waterfall visualization of margin evolution from FY2022 baseline to current quarter.

**Key insight:** Identifies inflection points and cumulative trend direction. Green bars = improvement, red bars = deterioration.
""",
    "expense_breakdown": """
**What it shows:** 100% stacked bars breaking down each revenue dollar into COGS, SG&A, Other expenses, and Operating Income.

**Key insight:** Watch for SG&A creep eating into margins. The green (Operating Income) slice should remain stable or grow.
""",
    "earnings_quality": """
**What it shows:** Compares Net Income to Operating Cash Flow with Cash Conversion Ratio.

**Key insight:** High-quality earnings convert to cash. Ratio consistently below 100% may indicate aggressive accounting or working capital issues.
""",
    "ebitda_bridge": """
**What it shows:** How revenue flows to EBITDA through operating expenses, with D&A add-back.

**Key insight:** The D&A add-back (green bar) reveals capital intensity. Larger D&A = more capital-intensive business requiring ongoing reinvestment.
""",

    # Pillar 3: Liquidity & Solvency
    "current_ratio": """
**What it shows:** Current assets divided by current liabilities - can the company pay bills due within 12 months?

**Key insight:** Below 1.0 means current liabilities exceed current assets (warning). Above 1.5 is healthy for retail. Target runs lean by design.
""",
    "capital_structure": """
**What it shows:** The debt vs equity mix in Target's capital structure.

**Key insight:** Higher debt = higher financial risk but potentially higher returns on equity. Watch for shifts toward more leverage over time.
""",
    "debt_to_ebitda": """
**What it shows:** Total debt divided by EBITDA - how many years of earnings to repay all debt?

**Key insight:** Below 3x is healthy, 3-5x is moderate, above 5x is risky. Trend direction matters as much as absolute level.
""",
    "debt_health": """
**What it shows:** Interest coverage ratio (Operating Income / Interest Expense) and total debt levels.

**Key insight:** Above 3x coverage is comfortable - the company can easily afford interest payments. Below 2x requires monitoring.
""",

    # Pillar 4: Operational Efficiency
    "dupont_analysis": """
**What it shows:** Decomposes Return on Equity into three multiplicative components: Profit Margin x Asset Turnover x Financial Leverage.

**Key insight:** Reveals what drives returns - is it margins, efficiency, or leverage? High ROE from leverage alone is riskier than from margins.
""",
    "cash_conversion_cycle": """
**What it shows:** Days to convert inventory investment back to cash, compared to retail peers.

**Key insight:** Lower is better. Negative CCC (like Amazon) means suppliers finance operations. Target's ~60 days is typical for retail.
""",
    "inventory_efficiency": """
**What it shows:** Inventory turnover ratio and days sales of inventory (DSI) over time.

**Key insight:** Faster turns = less capital tied up in inventory. Seasonal spikes in DSI before holidays are normal; persistent increases are concerning.
""",
    "operating_margin_waterfall": """
**What it shows:** Quarterly changes in operating margin as a waterfall, showing which quarters added or subtracted margin.

**Key insight:** Identifies seasonal patterns. Q1 often shows margin pressure post-holiday markdown season.
""",

    # Pillar 5: Cash Flow Dynamics
    "ocf_vs_capex": """
**What it shows:** Operating Cash Flow bars vs Capital Expenditure line, with Free Cash Flow as the gap between them.

**Key insight:** FCF = OCF - CapEx. Consistently positive FCF means the business generates cash after funding growth. Negative quarters need explanation.
""",
    "cash_flows": """
**What it shows:** The three cash flow statement lines: Operating, Investing, and Financing activities.

**Key insight:** Operating should be consistently positive. Investing is typically negative (spending on growth). Financing shows debt/equity activity.
""",
    "cash_flow_sankey": """
**What it shows:** Visual flow of where Operating Cash Flow gets allocated: CapEx, dividends, buybacks, debt repayment, or retained.

**Key insight:** Reveals management's capital allocation priorities. Heavy buybacks during high valuation periods may destroy value.
""",

    # Pillar 6: Valuation & Risk
    "valuation_scatter": """
**What it shows:** P/E ratio vs revenue growth for Target and retail peers, plotted by quarter.

**Key insight:** Lower-right quadrant = undervalued (low P/E, high growth). Upper-left = overvalued. Track Target's position drift over time.
""",
    "pe_band": """
**What it shows:** Current stock price overlaid on historical P/E valuation bands based on Target's own 5-year history.

**Key insight:** Shows if stock is cheap or expensive vs its own history. Below 25th percentile = historically undervalued opportunity.
""",
    "risk_trends": """
**What it shows:** Stacked area chart of risk mentions (shrink, theft, markdown, margin pressure) in SEC filings over time.

**Key insight:** Rising trends signal increasing management concern. Shrink has been a growing theme in recent filings.
""",
    "risk_heatmap": """
**What it shows:** Intensity grid showing which risk types are mentioned most frequently in each period.

**Key insight:** Dark cells = high concern. Identifies which risks are growing vs stable vs improving over time.
""",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def render_chart_with_explanation(title, explanation_key, fig, position="left"):
    """
    Render a chart with staggered explanatory text.

    Args:
        title: Chart title for the subheader
        explanation_key: Key to look up in CHART_EXPLANATIONS dict
        fig: Plotly figure to render
        position: "left" = explanation on left, "right" = explanation on right
    """
    st.subheader(title)

    explanation = CHART_EXPLANATIONS.get(explanation_key, "")

    if position == "left":
        col_text, col_chart = st.columns([1, 2])
    else:
        col_chart, col_text = st.columns([2, 1])

    with col_text:
        st.markdown(explanation)

    with col_chart:
        st.plotly_chart(fig, use_container_width=True)

    st.divider()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Target Financial Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🎯 Target Analysis")
st.sidebar.markdown("---")

pillar = st.sidebar.radio(
    "Select Pillar",
    [
        "1️⃣ Revenue & Growth",
        "2️⃣ Profitability & Margins",
        "3️⃣ Liquidity & Solvency",
        "4️⃣ Operational Efficiency",
        "5️⃣ Cash Flow Dynamics",
        "6️⃣ Valuation & Risk",
        "📊 All Charts"
    ]
)


# Load data once (cached for performance)
@st.cache_data
def load_data():
    """Load financial timeseries data with caching."""
    return load_timeseries_data()


data = load_data()

# Main content area
st.title("Target Corporation Financial Analysis")
st.markdown("*Interactive dashboard covering 6 pillars of financial analysis (24 charts)*")
st.markdown("---")


# =============================================================================
# PILLAR RENDER FUNCTIONS
# =============================================================================

def render_pillar_1():
    """Render Pillar 1: Revenue & Growth charts (4 charts) with staggered layout."""
    st.header("Pillar 1: Revenue & Growth")
    st.markdown("*Is the company growing its top line?*")
    st.markdown("")

    # Chart 1: Revenue & Net Income (10-Year) - explanation LEFT
    render_chart_with_explanation(
        "Revenue & Net Income (10-Year)",
        "revenue_netincome_annual",
        create_revenue_netincome_annual_chart(data),
        position="left"
    )

    # Chart 2: Revenue Growth YoY - explanation RIGHT
    render_chart_with_explanation(
        "Revenue Growth YoY",
        "revenue_growth_yoy",
        create_revenue_growth_yoy_chart(data),
        position="right"
    )

    # Chart 3: Revenue vs Inventory Growth - explanation LEFT
    render_chart_with_explanation(
        "Revenue vs Inventory Growth",
        "revenue_vs_inventory",
        create_revenue_vs_inventory_chart(data),
        position="left"
    )

    # Chart 4: Revenue & Net Income Long-Term - explanation RIGHT
    render_chart_with_explanation(
        "Revenue & Net Income Long-Term (Quarterly)",
        "revenue_netincome_longterm",
        create_revenue_netincome_longterm_chart(data),
        position="right"
    )


def render_pillar_2():
    """Render Pillar 2: Profitability & Margins charts (5 charts) with staggered layout."""
    st.header("Pillar 2: Profitability & Margins")
    st.markdown("*Is the company making money, and how efficiently?*")
    st.markdown("")

    # Chart 1: Margin Analysis - explanation LEFT
    render_chart_with_explanation(
        "Margin Analysis (Gross/Operating/Net)",
        "margin_analysis",
        create_margin_analysis_chart(data),
        position="left"
    )

    # Chart 2: Margin Bridge Waterfall - explanation RIGHT
    render_chart_with_explanation(
        "Margin Bridge Waterfall",
        "margin_bridge",
        create_margin_bridge_waterfall(data),
        position="right"
    )

    # Chart 3: Operating Expense Breakdown - explanation LEFT
    render_chart_with_explanation(
        "Operating Expense Breakdown",
        "expense_breakdown",
        create_expense_breakdown_chart(data),
        position="left"
    )

    # Chart 4: Earnings Quality - explanation RIGHT
    render_chart_with_explanation(
        "Earnings Quality",
        "earnings_quality",
        create_earnings_quality_chart(data),
        position="right"
    )

    # Chart 5: EBITDA Bridge - explanation LEFT
    render_chart_with_explanation(
        "EBITDA Bridge",
        "ebitda_bridge",
        create_ebitda_bridge_waterfall(data),
        position="left"
    )


def render_pillar_3():
    """Render Pillar 3: Liquidity & Solvency charts (4 charts) with staggered layout."""
    st.header("Pillar 3: Liquidity & Solvency")
    st.markdown("*Can the company pay its bills today and its debts in the future?*")
    st.markdown("")

    # Chart 1: Current Ratio Gauge - explanation LEFT
    render_chart_with_explanation(
        "Current Ratio",
        "current_ratio",
        create_current_ratio_gauge(data),
        position="left"
    )

    # Chart 2: Capital Structure Donut - explanation RIGHT
    render_chart_with_explanation(
        "Capital Structure",
        "capital_structure",
        create_capital_structure_donut(data),
        position="right"
    )

    # Chart 3: Debt-to-EBITDA Trend - explanation LEFT
    render_chart_with_explanation(
        "Debt-to-EBITDA Trend",
        "debt_to_ebitda",
        create_debt_to_ebitda_trend(data),
        position="left"
    )

    # Chart 4: Debt Health - explanation RIGHT
    render_chart_with_explanation(
        "Debt Health (Interest Coverage)",
        "debt_health",
        create_debt_health_chart(data),
        position="right"
    )


def render_pillar_4():
    """Render Pillar 4: Operational Efficiency charts (4 charts) with staggered layout."""
    st.header("Pillar 4: Operational Efficiency")
    st.markdown("*How well is management utilizing the company's assets?*")
    st.markdown("")

    # Chart 1: DuPont Analysis - explanation LEFT
    render_chart_with_explanation(
        "DuPont Analysis",
        "dupont_analysis",
        create_dupont_analysis_breakdown(data),
        position="left"
    )

    # Chart 2: Cash Conversion Cycle - explanation RIGHT
    render_chart_with_explanation(
        "Cash Conversion Cycle (vs Peers)",
        "cash_conversion_cycle",
        create_cash_conversion_cycle_chart(data),
        position="right"
    )

    # Chart 3: Inventory Efficiency - explanation LEFT
    render_chart_with_explanation(
        "Inventory Efficiency",
        "inventory_efficiency",
        create_inventory_efficiency_chart(data),
        position="left"
    )

    # Chart 4: Operating Margin Waterfall - explanation RIGHT
    render_chart_with_explanation(
        "Operating Margin Waterfall",
        "operating_margin_waterfall",
        create_operating_margin_waterfall(data),
        position="right"
    )


def render_pillar_5():
    """Render Pillar 5: Cash Flow Dynamics charts (3 charts) with staggered layout."""
    st.header("Pillar 5: Cash Flow Dynamics")
    st.markdown("*Where is cash coming from, and where is it going?*")
    st.markdown("")

    # Chart 1: OCF vs CapEx - explanation LEFT
    render_chart_with_explanation(
        "Operating CF vs CapEx",
        "ocf_vs_capex",
        create_ocf_vs_capex_chart(data),
        position="left"
    )

    # Chart 2: Statement of Cash Flows - explanation RIGHT
    render_chart_with_explanation(
        "Statement of Cash Flows",
        "cash_flows",
        create_cash_flows_chart(data),
        position="right"
    )

    # Chart 3: Cash Flow Sankey - explanation LEFT
    render_chart_with_explanation(
        "Cash Flow Allocation (Sankey)",
        "cash_flow_sankey",
        create_cash_flow_sankey(data),
        position="left"
    )


def render_pillar_6():
    """Render Pillar 6: Valuation & Risk charts (4 charts) with staggered layout."""
    st.header("Pillar 6: Valuation & Risk")
    st.markdown("*Is the stock fairly priced, and what are the risks?*")
    st.markdown("")

    # Chart 1: Valuation vs Growth Scatter - explanation LEFT
    render_chart_with_explanation(
        "Valuation vs Growth",
        "valuation_scatter",
        create_valuation_vs_growth_scatter(data),
        position="left"
    )

    # Chart 2: Historical P/E Band - explanation RIGHT
    render_chart_with_explanation(
        "Historical P/E Band",
        "pe_band",
        create_pe_band_area_chart(data),
        position="right"
    )

    # Chart 3: Risk Trends - explanation LEFT
    # Note: create_risk_trends_chart() reads from target_analysis.json directly
    render_chart_with_explanation(
        "Risk Trends",
        "risk_trends",
        create_risk_trends_chart(),
        position="left"
    )

    # Chart 4: Risk Heatmap - explanation RIGHT
    # Note: create_risk_heatmap_grid() reads from target_analysis.json directly
    render_chart_with_explanation(
        "Risk Heatmap",
        "risk_heatmap",
        create_risk_heatmap_grid(),
        position="right"
    )


# =============================================================================
# MAIN ROUTING LOGIC
# =============================================================================

if pillar == "1️⃣ Revenue & Growth":
    render_pillar_1()

elif pillar == "2️⃣ Profitability & Margins":
    render_pillar_2()

elif pillar == "3️⃣ Liquidity & Solvency":
    render_pillar_3()

elif pillar == "4️⃣ Operational Efficiency":
    render_pillar_4()

elif pillar == "5️⃣ Cash Flow Dynamics":
    render_pillar_5()

elif pillar == "6️⃣ Valuation & Risk":
    render_pillar_6()

else:  # All Charts
    st.header("📊 Complete Dashboard")
    st.markdown("*All 24 visualizations across 6 pillars of financial analysis*")

    # Use tabs for organized viewing
    tabs = st.tabs([
        "Revenue & Growth",
        "Profitability",
        "Liquidity",
        "Efficiency",
        "Cash Flow",
        "Valuation & Risk"
    ])

    with tabs[0]:
        render_pillar_1()

    with tabs[1]:
        render_pillar_2()

    with tabs[2]:
        render_pillar_3()

    with tabs[3]:
        render_pillar_4()

    with tabs[4]:
        render_pillar_5()

    with tabs[5]:
        render_pillar_6()

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.info("**Data Sources**\n- SEC EDGAR (10-K/10-Q)\n- Yahoo Finance")
st.sidebar.caption("Coverage: FY2015-FY2024 (24 charts)")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "[View Documentation](https://github.com/anthropics/claude-code) | "
    "[Report Issue](https://github.com/anthropics/claude-code/issues)"
)
