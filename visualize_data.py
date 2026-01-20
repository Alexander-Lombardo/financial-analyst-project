"""
Plotly visualization examples for Target financial data.
Reads from output/target_timeseries.json
"""
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path


def load_timeseries_data(filepath: str = "output/target_timeseries.json"):
    """Load time-series JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_revenue_vs_inventory_chart(data):
    """Chart 1: Revenue vs Inventory Growth Over Time (Dual-Axis)"""
    periods = [p['period'] for p in data['periods']]
    revenue = data['metrics']['revenue']['net_sales_billion']
    inventory = data['metrics']['inventory']['inventory_billion']

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=periods, y=revenue, name="Net Sales",
                   line=dict(color='blue', width=3), mode='lines+markers'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=periods, y=inventory, name="Inventory",
                   line=dict(color='orange', width=3), mode='lines+markers'),
        secondary_y=False
    )

    fig.update_layout(
        title="Target: Revenue vs Inventory (FY2020-Q3 2025)",
        hovermode='x unified',
        height=500,
        xaxis_title="Period",
        yaxis_title="$ Billions"
    )

    fig.write_html("output/chart_revenue_vs_inventory.html")
    print("✅ Chart created: output/chart_revenue_vs_inventory.html")
    return fig


def create_operating_margin_waterfall(data):
    """Chart 2: Operating Margin Waterfall (Year-over-Year Changes)"""
    periods = [p['period'] for p in data['periods']]
    operating_margins = data['metrics']['margins']['operating_margin_percent']

    # Filter quarterly data
    quarterly_periods = []
    quarterly_margins = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q':
            quarterly_periods.append(period['period'])
            quarterly_margins.append(operating_margins[i])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=quarterly_periods, y=quarterly_margins,
                   mode='lines+markers', name='Operating Margin %',
                   line=dict(color='green', width=3), marker=dict(size=8))
    )

    # Add baseline reference line (FY2024)
    fig.add_hline(y=5.22, line_dash="dash", line_color="red",
                  annotation_text="FY2024 Baseline (5.22%)")

    fig.update_layout(
        title="Target: Operating Margin Trend (Quarterly)",
        xaxis_title="Quarter",
        yaxis_title="Operating Margin %",
        hovermode='x unified',
        height=500
    )

    fig.write_html("output/chart_operating_margin_waterfall.html")
    print("✅ Chart created: output/chart_operating_margin_waterfall.html")
    return fig


def create_inventory_efficiency_chart(data):
    """Chart 3: Inventory Turnover Ratio & Days Sales of Inventory"""
    periods = [p['period'] for p in data['periods']]
    turnover = data['metrics']['inventory']['inventory_turnover_ratio']
    dsi = data['metrics']['inventory']['days_sales_of_inventory']

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=periods, y=turnover, name="Inventory Turnover Ratio",
               marker_color='lightblue'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=periods, y=dsi, name="Days Sales of Inventory",
                   line=dict(color='red', width=2), mode='lines+markers'),
        secondary_y=True
    )

    fig.update_xaxes(title_text="Period")
    fig.update_yaxes(title_text="Turnover Ratio (x)", secondary_y=False)
    fig.update_yaxes(title_text="Days", secondary_y=True)

    fig.update_layout(
        title="Target: Inventory Efficiency Metrics",
        hovermode='x unified',
        height=500
    )

    fig.write_html("output/chart_inventory_efficiency.html")
    print("✅ Chart created: output/chart_inventory_efficiency.html")
    return fig


def create_debt_health_chart(data):
    """Chart 4: Interest Coverage Ratio & Total Debt"""
    periods = [p['period'] for p in data['periods']]
    coverage = data['metrics']['debt']['interest_coverage_ratio']
    total_debt = data['metrics']['debt']['total_debt_billion']

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=periods, y=coverage, name="Interest Coverage Ratio",
                   line=dict(color='green', width=3), mode='lines+markers'),
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(x=periods, y=total_debt, name="Total Debt",
               marker_color='lightcoral', opacity=0.6),
        secondary_y=True
    )

    # Add warning threshold line
    fig.add_hline(y=2.0, line_dash="dash", line_color="red",
                  annotation_text="Warning Threshold (2.0x)", secondary_y=False)

    fig.update_xaxes(title_text="Period")
    fig.update_yaxes(title_text="Coverage Ratio (x)", secondary_y=False)
    fig.update_yaxes(title_text="$ Billions", secondary_y=True)

    fig.update_layout(
        title="Target: Debt Health Monitoring",
        hovermode='x unified',
        height=500
    )

    fig.write_html("output/chart_debt_health.html")
    print("✅ Chart created: output/chart_debt_health.html")
    return fig


def create_cash_flows_chart(data):
    """Chart 5: Statement of Cash Flows (Operating, Investing, Financing)"""
    periods = [p['period'] for p in data['periods']]
    operating_cf = data['metrics']['cash_flows']['operating_cash_flow_billion']
    investing_cf = data['metrics']['cash_flows']['investing_cash_flow_billion']
    financing_cf = data['metrics']['cash_flows']['financing_cash_flow_billion']

    fig = go.Figure()

    # Operating Cash Flow (green solid)
    fig.add_trace(
        go.Scatter(x=periods, y=operating_cf, name="Operating Cash Flow",
                   line=dict(color='green', width=3), mode='lines+markers',
                   marker=dict(size=8))
    )

    # Investing Cash Flow (blue dashed)
    fig.add_trace(
        go.Scatter(x=periods, y=investing_cf, name="Investing Cash Flow",
                   line=dict(color='blue', width=3, dash='dash'),
                   mode='lines+markers', marker=dict(size=8))
    )

    # Financing Cash Flow (orange dotted)
    fig.add_trace(
        go.Scatter(x=periods, y=financing_cf, name="Financing Cash Flow",
                   line=dict(color='orange', width=3, dash='dot'),
                   mode='lines+markers', marker=dict(size=8))
    )

    # Zero line
    fig.add_hline(y=0, line_dash="solid", line_color="gray",
                  line_width=1, opacity=0.5)

    fig.update_layout(
        title="Target: Statement of Cash Flows (FY2020-Q3 2025)",
        xaxis_title="Period",
        yaxis_title="Cash Flow ($ Billions)",
        hovermode='x unified',
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1)
    )

    fig.write_html("output/chart_cash_flows.html")
    print("✅ Chart created: output/chart_cash_flows.html")
    return fig


def main():
    """Generate all Plotly visualizations."""
    print("📊 Generating Plotly visualizations from time-series data...")

    # Check if timeseries JSON exists
    timeseries_path = Path("output/target_timeseries.json")
    if not timeseries_path.exists():
        print("❌ Error: output/target_timeseries.json not found")
        print("   Please run financial_analyzer.py first to generate the data")
        return

    data = load_timeseries_data()
    print(f"   Loaded {data['metadata']['total_periods']} periods")

    # Create all 5 charts
    create_revenue_vs_inventory_chart(data)
    create_operating_margin_waterfall(data)
    create_inventory_efficiency_chart(data)
    create_debt_health_chart(data)
    create_cash_flows_chart(data)

    print("\n✅ All 5 visualizations created in output/ directory")
    print("   Open the .html files in your browser to view interactive charts:")
    print("     - chart_revenue_vs_inventory.html")
    print("     - chart_operating_margin_waterfall.html")
    print("     - chart_inventory_efficiency.html")
    print("     - chart_debt_health.html")
    print("     - chart_cash_flows.html")


if __name__ == "__main__":
    main()
