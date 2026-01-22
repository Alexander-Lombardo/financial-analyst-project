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


def load_detailed_analysis(filepath: str = "output/target_analysis.json"):
    """Load detailed analysis JSON for risk heatmap."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_revenue_vs_inventory_chart(data):
    """Chart 1: Revenue vs Inventory Growth Over Time (Dual-Axis) - Quarterly Only (Including Calculated Q4)"""
    periods = [p['period'] for p in data['periods']]
    revenue = data['metrics']['revenue']['net_sales_billion']
    inventory = data['metrics']['inventory']['inventory_billion']

    # Step 1: Collect 10-Q quarterly data
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q':
            quarterly_data.append({
                'period': period['period'],
                'fiscal_year': period['fiscal_year'],
                'revenue': revenue[i],
                'inventory': inventory[i]
            })

    # Step 2: Calculate Q4 data from 10-K annual reports
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K':
            fy = period['fiscal_year']
            annual_revenue = revenue[i]
            annual_inventory = inventory[i]  # Year-end inventory (point-in-time)

            # Find Q1, Q2, Q3 for this fiscal year
            q1_rev = q2_rev = q3_rev = None
            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1_rev = q['revenue']
                    elif 'Q2' in q['period']:
                        q2_rev = q['revenue']
                    elif 'Q3' in q['period']:
                        q3_rev = q['revenue']

            # Calculate Q4 revenue = Annual - (Q1 + Q2 + Q3)
            if q1_rev and q2_rev and q3_rev:
                q4_revenue = annual_revenue - (q1_rev + q2_rev + q3_rev)
                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'revenue': q4_revenue,
                    'inventory': annual_inventory  # Year-end inventory for Q4
                })

    # Step 3: Sort by fiscal year and quarter
    def sort_key(item):
        year = item['fiscal_year']
        period = item['period']
        if 'Q1' in period:
            quarter = 1
        elif 'Q2' in period:
            quarter = 2
        elif 'Q3' in period:
            quarter = 3
        elif 'Q4' in period:
            quarter = 4
        else:
            quarter = 0
        return (year, quarter)

    quarterly_data.sort(key=sort_key)

    # Step 4: Extract sorted arrays
    quarterly_periods = [q['period'] for q in quarterly_data]
    quarterly_revenue = [q['revenue'] for q in quarterly_data]
    quarterly_inventory = [q['inventory'] for q in quarterly_data]

    # Step 5: Create chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=quarterly_periods, y=quarterly_revenue, name="Net Sales",
                   line=dict(color='blue', width=3), mode='lines+markers'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=quarterly_periods, y=quarterly_inventory, name="Inventory",
                   line=dict(color='orange', width=3), mode='lines+markers'),
        secondary_y=False
    )

    fig.update_layout(
        title="Target: Revenue vs Inventory - Quarterly Trends (Q1 2022 - Q3 2025)",
        hovermode='x unified',
        height=500,
        xaxis_title="Quarter",
        yaxis_title="$ Billions"
    )

    fig.write_html("output/chart_revenue_vs_inventory.html")
    print("✅ Chart created: output/chart_revenue_vs_inventory.html")
    return fig


def create_revenue_growth_yoy_chart(data):
    """Chart 2: Revenue Growth Year-over-Year (Quarterly with Calculated Q4)"""
    periods = [p['period'] for p in data['periods']]
    revenue = data['metrics']['revenue']['net_sales_billion']

    # Step 1: Collect 10-Q quarterly data
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q':
            quarterly_data.append({
                'period': period['period'],
                'fiscal_year': period['fiscal_year'],
                'revenue': revenue[i]
            })

    # Step 2: Calculate Q4 data from 10-K annual reports
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K':
            fy = period['fiscal_year']
            annual_revenue = revenue[i]

            # Find Q1, Q2, Q3 for this fiscal year
            q1_rev = q2_rev = q3_rev = None
            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1_rev = q['revenue']
                    elif 'Q2' in q['period']:
                        q2_rev = q['revenue']
                    elif 'Q3' in q['period']:
                        q3_rev = q['revenue']

            # Calculate Q4 revenue = Annual - (Q1 + Q2 + Q3)
            if q1_rev and q2_rev and q3_rev:
                q4_revenue = annual_revenue - (q1_rev + q2_rev + q3_rev)
                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'revenue': q4_revenue
                })

    # Step 3: Sort by fiscal year and quarter
    def sort_key(item):
        year = item['fiscal_year']
        period = item['period']
        if 'Q1' in period:
            quarter = 1
        elif 'Q2' in period:
            quarter = 2
        elif 'Q3' in period:
            quarter = 3
        elif 'Q4' in period:
            quarter = 4
        else:
            quarter = 0
        return (year, quarter)

    quarterly_data.sort(key=sort_key)

    # Step 4: Calculate YoY growth percentages
    for i in range(len(quarterly_data)):
        current = quarterly_data[i]
        current_period = current['period']
        current_revenue = current['revenue']

        # Find same quarter last year (4 quarters back)
        if i >= 4:
            prior = quarterly_data[i - 4]
            prior_revenue = prior['revenue']

            if prior_revenue and prior_revenue > 0:
                yoy_growth = ((current_revenue - prior_revenue) / prior_revenue) * 100
                quarterly_data[i]['yoy_growth_percent'] = round(yoy_growth, 2)
            else:
                quarterly_data[i]['yoy_growth_percent'] = None
        else:
            quarterly_data[i]['yoy_growth_percent'] = None

    # Step 5: Extract sorted arrays
    quarterly_periods = [q['period'] for q in quarterly_data]
    quarterly_revenue = [q['revenue'] for q in quarterly_data]
    quarterly_yoy_growth = [q['yoy_growth_percent'] for q in quarterly_data]

    # Step 6: Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Revenue bars on primary axis
    fig.add_trace(
        go.Bar(x=quarterly_periods, y=quarterly_revenue, name="Net Sales",
               marker_color='lightblue', opacity=0.7),
        secondary_y=False
    )

    # YoY growth line on secondary axis
    # Color code: green for positive, red for negative
    colors = ['green' if g and g >= 0 else 'red' for g in quarterly_yoy_growth]

    fig.add_trace(
        go.Scatter(x=quarterly_periods, y=quarterly_yoy_growth, name="YoY Growth %",
                   line=dict(color='darkblue', width=3), mode='lines+markers',
                   marker=dict(size=10, color=colors, line=dict(color='darkblue', width=2))),
        secondary_y=True
    )

    # Add zero line for YoY growth reference
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1, secondary_y=True)

    fig.update_xaxes(title_text="Quarter")
    fig.update_yaxes(title_text="Revenue ($ Billions)", secondary_y=False)
    fig.update_yaxes(title_text="YoY Growth %", secondary_y=True)

    fig.update_layout(
        title="Target: Revenue Growth Year-over-Year (Q1 2022 - Q3 2025)",
        hovermode='x unified',
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.write_html("output/chart_revenue_growth_yoy.html")
    print("✅ Chart created: output/chart_revenue_growth_yoy.html")
    return fig


def create_margin_analysis_chart(data):
    """Chart 3: Margin Analysis (Gross, Operating, Net Profit)"""
    periods = [p['period'] for p in data['periods']]
    gross_margin = data['metrics']['margins']['gross_margin_percent']
    operating_margin = data['metrics']['margins']['operating_margin_percent']
    net_profit_margin = data['metrics']['margins']['net_profit_margin_percent']

    # Step 1: Collect 10-Q quarterly data (starting from Q1 2022)
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q' and period['fiscal_year'] >= 2022:
            quarterly_data.append({
                'period': period['period'],
                'fiscal_year': period['fiscal_year'],
                'gross_margin': gross_margin[i],
                'operating_margin': operating_margin[i],
                'net_profit_margin': net_profit_margin[i]
            })

    # Step 2: Add Q4 data from 10-K annual reports (FY2022 onwards)
    # For margins (percentages), use annual margin as Q4 proxy
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']
            # Use annual margins as Q4 proxy
            quarterly_data.append({
                'period': f'Q4 {fy}',
                'fiscal_year': fy,
                'gross_margin': gross_margin[i],
                'operating_margin': operating_margin[i],
                'net_profit_margin': net_profit_margin[i]
            })

    # Step 3: Sort chronologically
    def sort_key(item):
        year = item['fiscal_year']
        period = item['period']
        if 'Q1' in period:
            quarter = 1
        elif 'Q2' in period:
            quarter = 2
        elif 'Q3' in period:
            quarter = 3
        elif 'Q4' in period:
            quarter = 4
        else:
            quarter = 0
        return (year, quarter)

    quarterly_data.sort(key=sort_key)

    # Step 4: Extract arrays
    quarterly_periods = [q['period'] for q in quarterly_data]
    quarterly_gross = [q['gross_margin'] for q in quarterly_data]
    quarterly_operating = [q['operating_margin'] for q in quarterly_data]
    quarterly_net_profit = [q['net_profit_margin'] for q in quarterly_data]

    # Step 5: Create multi-line chart
    fig = go.Figure()

    # Gross margin line (top)
    fig.add_trace(go.Scatter(
        x=quarterly_periods, y=quarterly_gross,
        name='Gross Margin %',
        line=dict(color='blue', width=3),
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(173, 216, 230, 0.3)'  # Light blue
    ))

    # Operating margin line (middle)
    fig.add_trace(go.Scatter(
        x=quarterly_periods, y=quarterly_operating,
        name='Operating Margin %',
        line=dict(color='green', width=3),
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(144, 238, 144, 0.3)'  # Light green
    ))

    # Net profit margin line (bottom)
    fig.add_trace(go.Scatter(
        x=quarterly_periods, y=quarterly_net_profit,
        name='Net Profit Margin %',
        line=dict(color='red', width=3),
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(255, 182, 193, 0.3)'  # Light red
    ))

    fig.update_layout(
        title="Target: Margin Analysis (Gross, Operating, Net Profit) - Q1 2022 to Q3 2025",
        xaxis_title="Quarter",
        yaxis_title="Margin %",
        hovermode='x unified',
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.write_html("output/chart_margin_analysis.html")
    print("✅ Chart created: output/chart_margin_analysis.html")
    return fig


def create_operating_margin_waterfall(data):
    """Chart 3: Operating Margin Waterfall (Year-over-Year Changes)"""
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


def create_margin_bridge_waterfall(data):
    """Chart 6: Operating Margin Bridge (FY2022 → Q3 2025)

    Waterfall chart showing operating margin evolution from FY2022 baseline
    through Q3 2025, with quarterly changes.
    """
    periods = [p['period'] for p in data['periods']]
    margins = data['metrics']['margins']['operating_margin_percent']

    # Get FY2022 onwards (find the index)
    fy2022_idx = None
    for i, p in enumerate(data['periods']):
        if p['period'] == 'FY2022':
            fy2022_idx = i
            break

    if fy2022_idx is None:
        print("⚠️  Warning: FY2022 not found, using first period as baseline")
        fy2022_idx = 0

    # Extract periods and margins from FY2022 onwards
    relevant_periods = periods[fy2022_idx:]
    relevant_margins = margins[fy2022_idx:]

    # Build waterfall data
    measure_types = []
    x_labels = []
    y_values = []

    # Starting point
    measure_types.append('absolute')
    x_labels.append('FY2022 Baseline')
    y_values.append(relevant_margins[0] if relevant_margins[0] is not None else 0)

    # Quarterly deltas
    for i in range(1, len(relevant_margins)):
        if relevant_margins[i] is not None and relevant_margins[i-1] is not None:
            delta = relevant_margins[i] - relevant_margins[i-1]
            measure_types.append('relative')
            x_labels.append(relevant_periods[i])
            y_values.append(delta)

    # Ending point (total)
    measure_types.append('total')
    x_labels.append('Q3 2025 Current')
    latest_margin = [m for m in relevant_margins if m is not None][-1]
    y_values.append(latest_margin)

    fig = go.Figure(go.Waterfall(
        name="Operating Margin",
        orientation="v",
        measure=measure_types,
        x=x_labels,
        y=y_values,
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "red"}},
        increasing={"marker": {"color": "green"}},
        totals={"marker": {"color": "blue"}}
    ))

    fig.update_layout(
        title="Target: Operating Margin Bridge (FY2022-Q3 2025)",
        xaxis_title="Period",
        yaxis_title="Operating Margin %",
        showlegend=False,
        height=600
    )

    fig.write_html("output/chart_margin_bridge.html")
    print("✅ Chart created: output/chart_margin_bridge.html")
    return fig


def create_risk_trends_chart():
    """Chart 7: Risk Mention Trends Over Time

    Stacked area chart showing shrink and markdown mentions across periods.
    """
    data = load_detailed_analysis()
    risk_heatmap = data.get('risk_heatmap', {})

    # Extract shrink data
    shrink_details = risk_heatmap.get('shrink', {}).get('details', [])
    shrink_periods = [detail[0] for detail in shrink_details]
    shrink_counts = [detail[1] for detail in shrink_details]

    # Extract markdown data
    markdown_details = risk_heatmap.get('markdown', {}).get('details', [])
    markdown_periods = [detail[0] for detail in markdown_details]
    markdown_counts = [detail[1] for detail in markdown_details]

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=markdown_periods,
        y=markdown_counts,
        name='Markdown/Promotional',
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='orange', width=2),
        marker=dict(size=8)
    ))

    fig.add_trace(go.Scatter(
        x=shrink_periods,
        y=shrink_counts,
        name='Shrink/Theft',
        mode='lines+markers',
        fill='tonexty',
        line=dict(color='red', width=2),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title="Target: Risk Mention Trends (2022-2025)",
        xaxis_title="Period",
        yaxis_title="Mention Count",
        hovermode='x unified',
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1)
    )

    fig.write_html("output/chart_risk_trends.html")
    print("✅ Chart created: output/chart_risk_trends.html")
    return fig


def create_risk_heatmap_grid():
    """Chart 8: Risk Heatmap Grid (Risk Types × Quarters)

    Heatmap showing risk mention intensity across periods.
    """
    data = load_detailed_analysis()
    risk_heatmap = data.get('risk_heatmap', {})

    # Build matrix
    all_periods = set()
    risk_types = []

    for risk_type, risk_data in risk_heatmap.items():
        risk_types.append(risk_type.capitalize())
        for detail in risk_data.get('details', []):
            all_periods.add(detail[0])

    # Sort periods chronologically
    all_periods = sorted(list(all_periods))

    # Create matrix
    z_matrix = []
    for i, risk_type in enumerate(risk_heatmap.keys()):
        row = []
        risk_data = risk_heatmap[risk_type]
        period_dict = {detail[0]: detail[1] for detail in risk_data.get('details', [])}

        for period in all_periods:
            row.append(period_dict.get(period, 0))

        z_matrix.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=all_periods,
        y=[rt.capitalize() for rt in risk_heatmap.keys()],
        colorscale='Reds',
        hoverongaps=False,
        colorbar=dict(title="Mentions")
    ))

    fig.update_layout(
        title="Target: Risk Heatmap (Mention Intensity)",
        xaxis_title="Period",
        yaxis_title="Risk Type",
        height=400
    )

    fig.write_html("output/chart_risk_heatmap_grid.html")
    print("✅ Chart created: output/chart_risk_heatmap_grid.html")
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

    # Check if detailed analysis JSON exists (for Phase 4 charts)
    detailed_path = Path("output/target_analysis.json")
    if not detailed_path.exists():
        print("❌ Error: output/target_analysis.json not found")
        print("   Please run financial_analyzer.py first to generate the data")
        return

    data = load_timeseries_data()
    print(f"   Loaded {data['metadata']['total_periods']} periods")

    # Create all 10 charts (6 from Phase 3 + 3 from Phase 4 + 1 margin analysis)
    create_revenue_vs_inventory_chart(data)
    create_revenue_growth_yoy_chart(data)
    create_margin_analysis_chart(data)
    create_operating_margin_waterfall(data)
    create_inventory_efficiency_chart(data)
    create_debt_health_chart(data)
    create_cash_flows_chart(data)
    create_margin_bridge_waterfall(data)
    create_risk_trends_chart()
    create_risk_heatmap_grid()

    print("\n✅ All 10 visualizations created in output/ directory")
    print("   Open the .html files in your browser to view interactive charts:")
    print("     - chart_revenue_vs_inventory.html")
    print("     - chart_revenue_growth_yoy.html")
    print("     - chart_margin_analysis.html (NEW)")
    print("     - chart_operating_margin_waterfall.html")
    print("     - chart_inventory_efficiency.html")
    print("     - chart_debt_health.html")
    print("     - chart_cash_flows.html")
    print("     - chart_margin_bridge.html (Phase 4)")
    print("     - chart_risk_trends.html (Phase 4)")
    print("     - chart_risk_heatmap_grid.html (Phase 4)")


if __name__ == "__main__":
    main()
