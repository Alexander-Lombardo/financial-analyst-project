#!/usr/bin/env python3
"""
Company Financial Analysis Dashboard
=====================================
Interactive visualization of 24 key financial metrics across 6 pillars.
Supports any company with SEC filings - just enter the ticker symbol.

Pillars:
1. Revenue & Growth
2. Profitability & Margins
3. Liquidity & Solvency
4. Operational Efficiency
5. Cash Flow Dynamics
6. Valuation & Risk

Run: streamlit run dashboard.py
"""

import streamlit as st
from pathlib import Path
from visualize_data import (
    load_timeseries_data,
    get_company_name,
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
from company_analyzer import get_company_info, has_cached_data, analyze_company, list_available_companies

# =============================================================================
# CHART EXPLANATIONS (Generic - not company-specific)
# =============================================================================

CHART_EXPLANATIONS = {
    # Pillar 1: Revenue & Growth
    "revenue_netincome_annual": """
**What it shows:** 10-year revenue and net income trajectory from annual 10-K filings.

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

**Key insight:** Q4 (holiday season) typically shows peak revenue for retailers. Watch for profit volatility vs revenue stability.
""",

    # Pillar 2: Profitability & Margins
    "margin_analysis": """
**What it shows:** Three margin lines - Gross, Operating, and Net Profit margins over time.

**Key insight:** Compression between lines reveals where profits leak. Gross margin erosion = pricing/cost issues. Operating margin erosion = overhead creep.
""",
    "margin_bridge": """
**What it shows:** Waterfall visualization of margin evolution from baseline to current quarter.

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

**Key insight:** Below 1.0 means current liabilities exceed current assets (warning). Above 1.5 is healthy for retail.
""",
    "capital_structure": """
**What it shows:** The debt vs equity mix in the company's capital structure.

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

**Key insight:** Lower is better. Negative CCC (like Amazon) means suppliers finance operations. ~60 days is typical for retail.
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
**What it shows:** P/E ratio vs revenue growth for the company and retail peers, plotted by quarter.

**Key insight:** Lower-right quadrant = undervalued (low P/E, high growth). Upper-left = overvalued. Track position drift over time.
""",
    "pe_band": """
**What it shows:** Current stock price overlaid on historical P/E valuation bands based on the company's own 5-year history.

**Key insight:** Shows if stock is cheap or expensive vs its own history. Below 25th percentile = historically undervalued opportunity.
""",
    "risk_trends": """
**What it shows:** Stacked area chart of risk mentions (shrink, theft, markdown, margin pressure) in SEC filings over time.

**Key insight:** Rising trends signal increasing management concern. Shrink has been a growing theme in recent retail filings.
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
    """Render a chart with staggered explanatory text."""
    if fig is None:
        st.warning(f"Chart '{title}' could not be rendered - missing data.")
        return

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
    page_title="Financial Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# SIDEBAR - Company Selection
# =============================================================================

st.sidebar.title("📊 Financial Analysis")
st.sidebar.markdown("---")

# Company Selection Section
st.sidebar.subheader("Company Selection")

# Ticker input
ticker_input = st.sidebar.text_input(
    "Enter Ticker Symbol",
    value="TGT",
    max_chars=10,
    help="Enter any stock ticker (e.g., TGT, WMT, AAPL)"
).upper().strip()

# Get company info (now uses SEC API for ANY ticker)
has_data = has_cached_data(ticker_input)

# Initialize company_info in session state to track lookup status
if 'company_info' not in st.session_state:
    st.session_state.company_info = None
if 'last_ticker' not in st.session_state:
    st.session_state.last_ticker = None

# Only lookup if ticker changed
if st.session_state.last_ticker != ticker_input:
    st.session_state.last_ticker = ticker_input
    st.session_state.company_info = None  # Reset for new ticker

# Show company info - lookup on demand
company_info = st.session_state.company_info

if company_info is None and ticker_input:
    # Try to get company info (uses cached SEC data if available)
    with st.sidebar.container():
        company_info = get_company_info(ticker_input)
        st.session_state.company_info = company_info

if company_info:
    st.sidebar.success(f"**{company_info['name']}**")
    st.sidebar.caption(f"CIK: {company_info['cik']}")
    if has_data:
        st.sidebar.caption("✅ Data available")
    else:
        st.sidebar.caption("⚠️ Data needs to be analyzed")
elif ticker_input:
    st.sidebar.warning(f"Ticker '{ticker_input}' not found in SEC database")
    st.sidebar.caption("Check spelling or try a different ticker")

# Analyze button - enabled for any valid ticker
button_disabled = not company_info or not ticker_input
if st.sidebar.button("🔄 Analyze Company", disabled=button_disabled, type="primary"):
    if company_info:
        with st.spinner(f"Analyzing {company_info['name']}... This may take 2-5 minutes."):
            result = analyze_company(ticker_input, force_refresh=True)

        if result['success']:
            st.sidebar.success(f"✅ Analysis complete! {result['num_filings']} filings processed.")
            st.rerun()  # Reload with new data
        else:
            st.sidebar.error(f"❌ Analysis failed: {result['error']}")

# Show available companies
with st.sidebar.expander("📋 Companies with Data"):
    st.caption("*Enter ANY ticker above - these are just cached/configured:*")
    companies = list_available_companies()
    if companies:
        for ticker, info in sorted(companies.items()):
            cached = "✓" if info['has_cached_data'] else " "
            st.caption(f"[{cached}] **{ticker}**: {info['name']}")
    else:
        st.caption("No companies analyzed yet. Enter a ticker and click Analyze.")

st.sidebar.markdown("---")

# Pillar Selection
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


# =============================================================================
# LOAD DATA
# =============================================================================

@st.cache_data
def load_data_for_ticker(ticker: str):
    """Load financial timeseries data for a specific ticker."""
    try:
        return load_timeseries_data(ticker=ticker)
    except FileNotFoundError:
        return None


# Load data for selected ticker
data = load_data_for_ticker(ticker_input)

# Get company name for title
if data:
    company_name = get_company_name(data)
else:
    company_name = company_info['name'] if company_info else ticker_input


# =============================================================================
# MAIN CONTENT AREA
# =============================================================================

st.title(f"{company_name} Financial Analysis")
st.markdown(f"*Interactive dashboard covering 6 pillars of financial analysis (24 charts)*")
st.markdown("---")

# Check if data is available
if data is None:
    st.warning(f"No analyzed data found for {ticker_input}.")
    st.info("Click 'Analyze Company' in the sidebar to download and analyze SEC filings.")

    # Show instructions
    st.markdown("""
    ### Getting Started

    1. **Enter ANY ticker symbol** in the sidebar (e.g., TGT, F, NFLX, AAPL)
    2. The system will look up the company in the SEC EDGAR database
    3. Click "Analyze Company" to download SEC filings
    4. Wait 2-5 minutes for analysis to complete
    5. Explore the 24 interactive charts across 6 pillars

    **Supported:** All ~10,000 publicly traded US companies with SEC filings.

    **Note:** You need SEC credentials configured in `.env` file:
    ```
    SEC_USER_NAME="Your Name"
    SEC_USER_EMAIL="your@email.com"
    ```
    """)
    st.stop()


# =============================================================================
# PILLAR RENDER FUNCTIONS
# =============================================================================

def render_pillar_1():
    """Render Pillar 1: Revenue & Growth charts."""
    st.header("Pillar 1: Revenue & Growth")
    st.markdown("*Is the company growing its top line?*")

    render_chart_with_explanation(
        "Revenue & Net Income (10-Year)",
        "revenue_netincome_annual",
        create_revenue_netincome_annual_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Revenue Growth YoY",
        "revenue_growth_yoy",
        create_revenue_growth_yoy_chart(data),
        position="right"
    )

    render_chart_with_explanation(
        "Revenue vs Inventory Growth",
        "revenue_vs_inventory",
        create_revenue_vs_inventory_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Revenue & Net Income Long-Term (Quarterly)",
        "revenue_netincome_longterm",
        create_revenue_netincome_longterm_chart(data),
        position="right"
    )


def render_pillar_2():
    """Render Pillar 2: Profitability & Margins charts."""
    st.header("Pillar 2: Profitability & Margins")
    st.markdown("*Is the company making money, and how efficiently?*")

    render_chart_with_explanation(
        "Margin Analysis (Gross/Operating/Net)",
        "margin_analysis",
        create_margin_analysis_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Margin Bridge Waterfall",
        "margin_bridge",
        create_margin_bridge_waterfall(data),
        position="right"
    )

    render_chart_with_explanation(
        "Operating Expense Breakdown",
        "expense_breakdown",
        create_expense_breakdown_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Earnings Quality",
        "earnings_quality",
        create_earnings_quality_chart(data),
        position="right"
    )

    render_chart_with_explanation(
        "EBITDA Bridge",
        "ebitda_bridge",
        create_ebitda_bridge_waterfall(data),
        position="left"
    )


def render_pillar_3():
    """Render Pillar 3: Liquidity & Solvency charts."""
    st.header("Pillar 3: Liquidity & Solvency")
    st.markdown("*Can the company pay its bills today and its debts in the future?*")

    render_chart_with_explanation(
        "Current Ratio",
        "current_ratio",
        create_current_ratio_gauge(data),
        position="left"
    )

    render_chart_with_explanation(
        "Capital Structure",
        "capital_structure",
        create_capital_structure_donut(data),
        position="right"
    )

    render_chart_with_explanation(
        "Debt-to-EBITDA Trend",
        "debt_to_ebitda",
        create_debt_to_ebitda_trend(data),
        position="left"
    )

    render_chart_with_explanation(
        "Debt Health (Interest Coverage)",
        "debt_health",
        create_debt_health_chart(data),
        position="right"
    )


def render_pillar_4():
    """Render Pillar 4: Operational Efficiency charts."""
    st.header("Pillar 4: Operational Efficiency")
    st.markdown("*How well is management utilizing the company's assets?*")

    render_chart_with_explanation(
        "DuPont Analysis",
        "dupont_analysis",
        create_dupont_analysis_breakdown(data),
        position="left"
    )

    render_chart_with_explanation(
        "Cash Conversion Cycle (vs Peers)",
        "cash_conversion_cycle",
        create_cash_conversion_cycle_chart(data),
        position="right"
    )

    render_chart_with_explanation(
        "Inventory Efficiency",
        "inventory_efficiency",
        create_inventory_efficiency_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Operating Margin Waterfall",
        "operating_margin_waterfall",
        create_operating_margin_waterfall(data),
        position="right"
    )


def render_pillar_5():
    """Render Pillar 5: Cash Flow Dynamics charts."""
    st.header("Pillar 5: Cash Flow Dynamics")
    st.markdown("*Where is cash coming from, and where is it going?*")

    render_chart_with_explanation(
        "Operating CF vs CapEx",
        "ocf_vs_capex",
        create_ocf_vs_capex_chart(data),
        position="left"
    )

    render_chart_with_explanation(
        "Statement of Cash Flows",
        "cash_flows",
        create_cash_flows_chart(data),
        position="right"
    )

    render_chart_with_explanation(
        "Cash Flow Allocation (Sankey)",
        "cash_flow_sankey",
        create_cash_flow_sankey(data),
        position="left"
    )


def render_pillar_6():
    """Render Pillar 6: Valuation & Risk charts."""
    st.header("Pillar 6: Valuation & Risk")
    st.markdown("*Is the stock fairly priced, and what are the risks?*")

    render_chart_with_explanation(
        "Valuation vs Growth",
        "valuation_scatter",
        create_valuation_vs_growth_scatter(data),
        position="left"
    )

    render_chart_with_explanation(
        "Historical P/E Band",
        "pe_band",
        create_pe_band_area_chart(data),
        position="right"
    )

    # Risk charts need ticker parameter
    render_chart_with_explanation(
        "Risk Trends",
        "risk_trends",
        create_risk_trends_chart(ticker=ticker_input),
        position="left"
    )

    render_chart_with_explanation(
        "Risk Heatmap",
        "risk_heatmap",
        create_risk_heatmap_grid(ticker=ticker_input),
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

# =============================================================================
# SIDEBAR FOOTER
# =============================================================================

st.sidebar.markdown("---")
st.sidebar.info("**Data Sources**\n- SEC EDGAR (10-K/10-Q)\n- Yahoo Finance")
st.sidebar.caption(f"Ticker: {ticker_input} | 24 charts")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "[View Documentation](https://github.com/anthropics/claude-code) | "
    "[Report Issue](https://github.com/anthropics/claude-code/issues)"
)
