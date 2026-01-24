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


def create_earnings_quality_chart(data):
    """Chart 11: Earnings Quality (Net Income vs Operating Cash Flow)

    Compares net income to operating cash flow to assess earnings quality.
    Calculates Cash Conversion Ratio = (Operating CF / Net Income) × 100
    Ratio > 100% = Good (cash exceeds earnings)
    Ratio < 100% = Warning (earnings not backed by cash)
    """
    periods = [p['period'] for p in data['periods']]
    net_income = data['metrics']['cash_flows']['net_income_billion']
    operating_cf = data['metrics']['cash_flows']['operating_cash_flow_billion']

    # Step 1: Collect 10-Q quarterly data (starting from Q1 2022)
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q' and period['fiscal_year'] >= 2022:
            quarterly_data.append({
                'period': period['period'],
                'fiscal_year': period['fiscal_year'],
                'net_income': net_income[i],
                'operating_cf': operating_cf[i]
            })

    # Step 2: Calculate Q4 data from 10-K annual reports (FY2022 onwards)
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']
            annual_net_income = net_income[i]
            annual_operating_cf = operating_cf[i]

            # Find Q1, Q2, Q3 for this fiscal year
            q1_ni = q2_ni = q3_ni = None
            q1_cf = q2_cf = q3_cf = None

            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1_ni = q['net_income']
                        q1_cf = q['operating_cf']
                    elif 'Q2' in q['period']:
                        q2_ni = q['net_income']
                        q2_cf = q['operating_cf']
                    elif 'Q3' in q['period']:
                        q3_ni = q['net_income']
                        q3_cf = q['operating_cf']

            # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
            if q1_ni and q2_ni and q3_ni and q1_cf and q2_cf and q3_cf:
                q4_net_income = annual_net_income - (q1_ni + q2_ni + q3_ni)
                q4_operating_cf = annual_operating_cf - (q1_cf + q2_cf + q3_cf)

                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'net_income': q4_net_income,
                    'operating_cf': q4_operating_cf
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

    # Step 4: Calculate Cash Conversion Ratio
    for q in quarterly_data:
        if q['net_income'] and q['net_income'] != 0:
            q['cash_conversion_ratio'] = (q['operating_cf'] / q['net_income']) * 100
        else:
            q['cash_conversion_ratio'] = None

    # Step 5: Extract arrays
    quarterly_periods = [q['period'] for q in quarterly_data]
    quarterly_net_income = [q['net_income'] for q in quarterly_data]
    quarterly_operating_cf = [q['operating_cf'] for q in quarterly_data]
    quarterly_cash_conversion = [q['cash_conversion_ratio'] for q in quarterly_data]

    # Step 6: Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Net Income bars on primary axis
    fig.add_trace(
        go.Bar(
            x=quarterly_periods,
            y=quarterly_net_income,
            name="Net Income",
            marker_color='lightblue',
            opacity=0.7
        ),
        secondary_y=False
    )

    # Operating Cash Flow bars on primary axis
    fig.add_trace(
        go.Bar(
            x=quarterly_periods,
            y=quarterly_operating_cf,
            name="Operating Cash Flow",
            marker_color='lightgreen',
            opacity=0.7
        ),
        secondary_y=False
    )

    # Cash Conversion Ratio line on secondary axis
    # Color code markers: green if > 100%, red if < 100%
    colors = ['green' if r and r >= 100 else 'red' if r else 'gray'
              for r in quarterly_cash_conversion]

    fig.add_trace(
        go.Scatter(
            x=quarterly_periods,
            y=quarterly_cash_conversion,
            name="Cash Conversion Ratio %",
            line=dict(color='darkred', width=3),
            mode='lines+markers',
            marker=dict(size=10, color=colors,
                       line=dict(color='darkred', width=2))
        ),
        secondary_y=True
    )

    # Add 100% reference line on secondary axis
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        line_width=2,
        secondary_y=True,
        annotation_text="100% (Earnings = Cash)",
        annotation_position="right"
    )

    fig.update_xaxes(title_text="Quarter")
    fig.update_yaxes(
        title_text="Amount ($ Billions)",
        secondary_y=False,
        range=[0, 12]  # Fixed range: max Operating CF is 10.53B, provides 14% headroom
    )
    fig.update_yaxes(
        title_text="Cash Conversion Ratio %",
        secondary_y=True,
        range=[-150, 650]  # Accommodates negative Q4 values (-104%, -99%) and extreme positives (549%, 506%)
    )

    fig.update_layout(
        title="Target: Earnings Quality Analysis (Net Income vs Operating Cash Flow)<br>Q1 2022 - Q3 2025",
        hovermode='x unified',
        height=600,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.write_html("output/chart_earnings_quality.html")
    print("✅ Chart created: output/chart_earnings_quality.html")
    return fig


def create_revenue_netincome_longterm_chart(data):
    """Chart 12: Revenue & Net Income Long-Term Trajectory (5-10 Year Period)

    Line chart showing Revenue and Net Income over 5-10 years to show
    long-term trajectory and correlation between sales and profit.
    Includes calculated Q4 data from annual 10-K reports.
    """
    periods = [p['period'] for p in data['periods']]
    revenue = data['metrics']['revenue']['net_sales_billion']
    net_income = data['metrics']['cash_flows']['net_income_billion']

    # Step 1: Collect 10-Q quarterly data (all available years)
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q':
            quarterly_data.append({
                'period': period['period'],
                'fiscal_year': period['fiscal_year'],
                'revenue': revenue[i],
                'net_income': net_income[i]
            })

    # Step 2: Calculate Q4 data from 10-K annual reports
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K':
            fy = period['fiscal_year']
            annual_revenue = revenue[i]
            annual_net_income = net_income[i]

            # Find Q1, Q2, Q3 for this fiscal year
            q1_rev = q2_rev = q3_rev = None
            q1_ni = q2_ni = q3_ni = None

            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1_rev = q['revenue']
                        q1_ni = q['net_income']
                    elif 'Q2' in q['period']:
                        q2_rev = q['revenue']
                        q2_ni = q['net_income']
                    elif 'Q3' in q['period']:
                        q3_rev = q['revenue']
                        q3_ni = q['net_income']

            # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
            if q1_rev and q2_rev and q3_rev and q1_ni and q2_ni and q3_ni:
                q4_revenue = annual_revenue - (q1_rev + q2_rev + q3_rev)
                q4_net_income = annual_net_income - (q1_ni + q2_ni + q3_ni)

                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'revenue': q4_revenue,
                    'net_income': q4_net_income
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
    quarterly_revenue = [q['revenue'] for q in quarterly_data]
    quarterly_net_income = [q['net_income'] for q in quarterly_data]

    # Step 5: Create dual-axis line chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Revenue line on primary axis
    fig.add_trace(
        go.Scatter(
            x=quarterly_periods,
            y=quarterly_revenue,
            name="Revenue (Net Sales)",
            line=dict(color='blue', width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=False
    )

    # Net Income line on secondary axis
    fig.add_trace(
        go.Scatter(
            x=quarterly_periods,
            y=quarterly_net_income,
            name="Net Income",
            line=dict(color='green', width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True
    )

    fig.update_xaxes(title_text="Quarter")
    fig.update_yaxes(
        title_text="Revenue ($ Billions)",
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Net Income ($ Billions)",
        secondary_y=True
    )

    fig.update_layout(
        title="Target: Revenue & Net Income Long-Term Trajectory<br>Quarterly Data",
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.write_html("output/chart_revenue_netincome_longterm.html")
    print("✅ Chart created: output/chart_revenue_netincome_longterm.html")
    return fig


def create_revenue_netincome_annual_chart(data):
    """Chart 13: Revenue & Net Income Annual Trajectory (10-Year Period)

    Line chart showing Revenue and Net Income over a 10-year period using
    ONLY annual fiscal year data from 10-K reports.
    Shows long-term trajectory and correlation between sales and profit.

    This is separate from Chart 12 which uses quarterly data with calculated Q4.
    """
    periods = [p['period'] for p in data['periods']]
    revenue = data['metrics']['revenue']['net_sales_billion']
    net_income = data['metrics']['cash_flows']['net_income_billion']

    # Step 1: Filter ONLY annual 10-K data
    annual_periods = []
    annual_revenue = []
    annual_net_income = []

    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K':
            annual_periods.append(period['period'])
            annual_revenue.append(revenue[i])
            annual_net_income.append(net_income[i])

    # Step 2: Create dual-axis line chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Revenue line on primary axis
    fig.add_trace(
        go.Scatter(
            x=annual_periods,
            y=annual_revenue,
            name="Revenue (Net Sales)",
            line=dict(color='blue', width=4),
            mode='lines+markers',
            marker=dict(size=10)
        ),
        secondary_y=False
    )

    # Net Income line on secondary axis
    fig.add_trace(
        go.Scatter(
            x=annual_periods,
            y=annual_net_income,
            name="Net Income",
            line=dict(color='green', width=4),
            mode='lines+markers',
            marker=dict(size=10)
        ),
        secondary_y=True
    )

    # Update axes
    fig.update_xaxes(title_text="Fiscal Year")
    fig.update_yaxes(
        title_text="Revenue ($ Billions)",
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Net Income ($ Billions)",
        secondary_y=True
    )

    # Update layout
    fig.update_layout(
        title="Target: Revenue & Net Income Annual Trajectory<br>Fiscal Year Data (10-Year Period)",
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.write_html("output/chart_revenue_netincome_annual.html")
    print("✅ Chart created: output/chart_revenue_netincome_annual.html")
    return fig


def create_expense_breakdown_chart(data):
    """Chart 14: Operating Expense Breakdown (100% Stacked Bar)

    Shows what percentage of revenue goes to:
    - COGS (Cost of Goods Sold)
    - SG&A (Selling, General & Administrative)
    - Other Operating Expenses
    - Operating Income (profit)

    100% stacked format makes it easy to identify margin compression trends.
    """
    periods = data['periods']

    # Extract base metrics
    revenue = data['metrics']['revenue']['net_sales_billion']
    cogs = data['metrics']['operating_expenses']['cost_of_sales_billion']
    sga = data['metrics']['operating_expenses']['sga_expense_billion']
    other_exp = data['metrics']['operating_expenses']['other_operating_expenses_billion']

    # Step 1: Collect quarterly data from 10-Q filings (2022 onwards)
    quarterly_data = []
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-Q' and period['fiscal_year'] >= 2022:
            # Derive operating income to ensure stack = 100%
            if all([revenue[i], cogs[i], sga[i], other_exp[i]]):
                oi = revenue[i] - cogs[i] - sga[i] - other_exp[i]

                quarterly_data.append({
                    'period': period['period'],
                    'fiscal_year': period['fiscal_year'],
                    'revenue': revenue[i],
                    'cogs': cogs[i],
                    'sga': sga[i],
                    'other': other_exp[i],
                    'operating_income': oi
                })

    # Step 2: Calculate Q4 from annual 10-K reports
    # Q4 = Annual Total - (Q1 + Q2 + Q3)
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']
            annual_revenue = revenue[i]
            annual_cogs = cogs[i]
            annual_sga = sga[i]
            annual_other = other_exp[i]

            # Find Q1, Q2, Q3 for this fiscal year
            q1 = q2 = q3 = None
            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1 = q
                    elif 'Q2' in q['period']:
                        q2 = q
                    elif 'Q3' in q['period']:
                        q3 = q

            # Calculate Q4 = Annual - Q1 - Q2 - Q3
            if all([q1, q2, q3, annual_revenue, annual_cogs, annual_sga, annual_other]):
                q4_revenue = annual_revenue - (q1['revenue'] + q2['revenue'] + q3['revenue'])
                q4_cogs = annual_cogs - (q1['cogs'] + q2['cogs'] + q3['cogs'])
                q4_sga = annual_sga - (q1['sga'] + q2['sga'] + q3['sga'])
                q4_other = annual_other - (q1['other'] + q2['other'] + q3['other'])
                q4_oi = q4_revenue - q4_cogs - q4_sga - q4_other

                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'revenue': q4_revenue,
                    'cogs': q4_cogs,
                    'sga': q4_sga,
                    'other': q4_other,
                    'operating_income': q4_oi
                })

    # Step 3: Sort chronologically
    def sort_key(item):
        year = item['fiscal_year']
        period = item['period']
        quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
        for q_str, q_num in quarter_map.items():
            if q_str in period:
                return (year, q_num)
        return (year, 0)

    quarterly_data.sort(key=sort_key)

    # Step 4: Calculate percentages for 100% stacked bar
    quarterly_periods = []
    cogs_pct = []
    sga_pct = []
    other_pct = []
    oi_pct = []

    for q in quarterly_data:
        quarterly_periods.append(q['period'])

        # Calculate percentages (each component as % of revenue)
        if q['revenue'] and q['revenue'] > 0:
            cogs_pct.append(round((q['cogs'] / q['revenue']) * 100, 2))
            sga_pct.append(round((q['sga'] / q['revenue']) * 100, 2))
            other_pct.append(round((q['other'] / q['revenue']) * 100, 2))
            oi_pct.append(round((q['operating_income'] / q['revenue']) * 100, 2))
        else:
            cogs_pct.append(None)
            sga_pct.append(None)
            other_pct.append(None)
            oi_pct.append(None)

    # Step 5: Create stacked bar chart
    fig = go.Figure()

    # Stack order (bottom to top): Operating Income, Other, SG&A, COGS

    # Bottom: Operating Income (green - what's left as profit)
    fig.add_trace(go.Bar(
        x=quarterly_periods,
        y=oi_pct,
        name='Operating Income %',
        marker_color='#27AE60',  # Green
        hovertemplate='<b>Operating Income</b><br>%{y:.2f}% of Revenue<br><extra></extra>'
    ))

    # Second layer: Other Operating Expenses (orange)
    fig.add_trace(go.Bar(
        x=quarterly_periods,
        y=other_pct,
        name='Other Operating Expenses %',
        marker_color='#F39C12',  # Orange
        hovertemplate='<b>Other Expenses</b><br>%{y:.2f}% of Revenue<br><extra></extra>'
    ))

    # Third layer: SG&A (purple)
    fig.add_trace(go.Bar(
        x=quarterly_periods,
        y=sga_pct,
        name='SG&A Expenses %',
        marker_color='#9B59B6',  # Purple
        hovertemplate='<b>SG&A</b><br>%{y:.2f}% of Revenue<br><extra></extra>'
    ))

    # Top layer: COGS (red - largest expense)
    fig.add_trace(go.Bar(
        x=quarterly_periods,
        y=cogs_pct,
        name='Cost of Sales (COGS) %',
        marker_color='#E74C3C',  # Red
        hovertemplate='<b>COGS</b><br>%{y:.2f}% of Revenue<br><extra></extra>'
    ))

    # Step 6: Configure layout
    fig.update_layout(
        barmode='stack',  # 100% stacked bars
        title={
            'text': "Target: Operating Expense Breakdown (% of Revenue)<br><sub>Quarterly Breakdown: Q1 2022 - Q3 2025</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.96,  # Moved down from 0.98
            'yanchor': 'top'
        },
        xaxis_title="Quarter",
        yaxis_title="% of Net Sales",
        yaxis=dict(
            range=[-5, 105],  # Allow negative values for bad quarters
            ticksuffix='%',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black'
        ),
        hovermode='x unified',
        height=750,  # Increased from 700 for even more spacing
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.10,  # Decreased from 1.12 to move legend down
            xanchor="right",
            x=1,
            traceorder='reversed'  # Show stack order: COGS at top of legend
        ),
        bargap=0.15,  # Space between bars
        font=dict(size=12),
        margin=dict(t=140, b=80)  # Increased top margin, added bottom margin
    )

    # Add annotation explaining the chart
    fig.add_annotation(
        text="Each bar = 100% of Revenue. Wider Operating Income (green) = better margins.",
        xref="paper", yref="paper",
        x=0.5, y=-0.12,
        showarrow=False,
        font=dict(size=10, color='gray'),
        xanchor='center'
    )

    # Step 7: Export
    fig.write_html("output/chart_expense_breakdown.html")
    print("✅ Chart 14 created: output/chart_expense_breakdown.html")
    return fig


def create_ebitda_bridge_waterfall(data):
    """Chart 15: EBITDA Bridge Waterfall (Phase 7)

    Waterfall chart showing how revenue flows down to EBITDA by subtracting
    each major expense category: COGS, SG&A, Other Operating Expenses.
    Shows quarterly data (Q1 2022 - Q3 2025) including calculated Q4.
    """
    periods = data['periods']

    # Extract metrics
    revenue = data['metrics']['revenue']['net_sales_billion']
    cogs = data['metrics']['operating_expenses']['cost_of_sales_billion']
    sga = data['metrics']['operating_expenses']['sga_expense_billion']
    other_exp = data['metrics']['operating_expenses']['other_operating_expenses_billion']
    da = data['metrics']['operating_expenses']['depreciation_amortization_billion']
    ebitda = data['metrics']['operating_expenses']['ebitda_billion']

    # Step 1: Collect quarterly data from 10-Q filings (2022 onwards)
    quarterly_data = []
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-Q' and period['fiscal_year'] >= 2022:
            if all([revenue[i], cogs[i], sga[i], other_exp[i], da[i]]):
                quarterly_data.append({
                    'period': period['period'],
                    'fiscal_year': period['fiscal_year'],
                    'revenue': revenue[i],
                    'cogs': cogs[i],
                    'sga': sga[i],
                    'other': other_exp[i],
                    'da': da[i],
                    'ebitda': ebitda[i] if ebitda[i] else revenue[i] - cogs[i] - sga[i] - other_exp[i] + da[i]
                })

    # Step 2: Calculate Q4 from annual 10-K reports
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']

            # Find Q1, Q2, Q3 for this fiscal year
            q1 = q2 = q3 = None
            for q in quarterly_data:
                if q['fiscal_year'] == fy:
                    if 'Q1' in q['period']:
                        q1 = q
                    elif 'Q2' in q['period']:
                        q2 = q
                    elif 'Q3' in q['period']:
                        q3 = q

            # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
            if all([q1, q2, q3, revenue[i], cogs[i], sga[i], other_exp[i], da[i]]):
                q4_revenue = revenue[i] - (q1['revenue'] + q2['revenue'] + q3['revenue'])
                q4_cogs = cogs[i] - (q1['cogs'] + q2['cogs'] + q3['cogs'])
                q4_sga = sga[i] - (q1['sga'] + q2['sga'] + q3['sga'])
                q4_other = other_exp[i] - (q1['other'] + q2['other'] + q3['other'])
                q4_da = da[i] - (q1['da'] + q2['da'] + q3['da'])
                q4_ebitda = q4_revenue - q4_cogs - q4_sga - q4_other + q4_da

                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'revenue': q4_revenue,
                    'cogs': q4_cogs,
                    'sga': q4_sga,
                    'other': q4_other,
                    'da': q4_da,
                    'ebitda': q4_ebitda
                })

    # Step 3: Sort chronologically
    def sort_key(item):
        year = item['fiscal_year']
        period = item['period']
        quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
        for q_str, q_num in quarter_map.items():
            if q_str in period:
                return (year, q_num)
        return (year, 0)

    quarterly_data.sort(key=sort_key)

    # Step 4: Create interactive waterfall charts for all quarters with dropdown
    if not quarterly_data:
        print("⚠️  No quarterly data available for EBITDA bridge")
        return None

    x_labels = [
        'Revenue<br>(Starting Point)',
        'Less: COGS<br>(Cost of Sales)',
        'Less: SG&A<br>(Admin Expenses)',
        'Less: Other<br>(Operating Exp)',
        'Add Back: D&A<br>(Non-Cash)',
        'EBITDA<br>(Final Result)'
    ]

    measure_types = [
        'absolute',  # Revenue
        'relative',  # -COGS
        'relative',  # -SG&A
        'relative',  # -Other
        'relative',  # +D&A
        'total'      # EBITDA
    ]

    # Create a figure with traces for each quarter
    fig = go.Figure()

    # Add a waterfall trace for each quarter
    for idx, q in enumerate(quarterly_data):
        # Calculate values
        y_values = [
            q['revenue'],
            -q['cogs'],
            -q['sga'],
            -q['other'],
            q['da'],
            q['ebitda']
        ]

        # Calculate percentages of revenue
        cogs_pct = (q['cogs'] / q['revenue']) * 100
        sga_pct = (q['sga'] / q['revenue']) * 100
        other_pct = (q['other'] / q['revenue']) * 100
        da_pct = (q['da'] / q['revenue']) * 100
        ebitda_pct = (q['ebitda'] / q['revenue']) * 100

        # Create text labels with both dollar values and percentages
        text_labels = [
            f"${q['revenue']:.2f}B",
            f"-${q['cogs']:.2f}B ({cogs_pct:.1f}%)",
            f"-${q['sga']:.2f}B ({sga_pct:.1f}%)",
            f"-${q['other']:.2f}B ({other_pct:.1f}%)",
            f"+${q['da']:.2f}B ({da_pct:.1f}%)",
            f"${q['ebitda']:.2f}B ({ebitda_pct:.1f}%)"
        ]

        # Add waterfall trace
        fig.add_trace(go.Waterfall(
            name=q['period'],
            x=x_labels,
            y=y_values,
            measure=measure_types,
            text=text_labels,
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#27AE60"}},
            decreasing={"marker": {"color": "#E74C3C"}},
            totals={"marker": {"color": "#3498DB"}},
            visible=(idx == len(quarterly_data) - 1)  # Only show latest quarter initially
        ))

    # Create dropdown menu buttons (reverse order for most recent first)
    buttons = []
    for idx, q in enumerate(reversed(quarterly_data)):
        actual_idx = len(quarterly_data) - 1 - idx  # Map reversed index to actual data index
        visible_array = [False] * len(quarterly_data)
        visible_array[actual_idx] = True
        buttons.append({
            'label': q['period'],
            'method': 'update',
            'args': [
                {'visible': visible_array},
                {
                    'title': {
                        'text': f"Target: EBITDA Bridge Waterfall ({q['period']})<br><sub>Shows how Revenue flows to EBITDA: Start with Revenue, subtract Operating Expenses, add back D&A</sub>",
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.97,
                        'yanchor': 'top'
                    }
                }
            ]
        })

    fig.update_layout(
        title={
            'text': f"Target: EBITDA Bridge Waterfall ({quarterly_data[-1]['period']})<br><sub>Shows how Revenue flows to EBITDA: Start with Revenue, subtract Operating Expenses, add back D&A</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.97,
            'yanchor': 'top'
        },
        xaxis={
            'title': {
                'text': "Flow: Revenue → Operating Expenses → EBITDA",
                'font': {'size': 14, 'color': '#555'}
            },
            'tickfont': {'size': 12}
        },
        yaxis={
            'title': {
                'text': "$ Billions",
                'font': {'size': 14}
            },
            'tickprefix': '$',
            'ticksuffix': 'B',
            'gridcolor': '#E5E5E5'
        },
        height=700,
        hovermode='x unified',
        showlegend=False,
        plot_bgcolor='white',
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.17,
            'xanchor': 'left',
            'y': 1.12,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': '#BDBDBD',
            'borderwidth': 1
        }],
        annotations=[
            {
                'text': 'Select Quarter:',
                'x': 0.01,
                'xref': 'paper',
                'y': 1.12,
                'yref': 'paper',
                'align': 'left',
                'showarrow': False,
                'font': {'size': 12, 'color': '#333'}
            },
            {
                'text': 'RED bars = expenses reducing profit  |  GREEN bar = non-cash D&A added back  |  BLUE bars = totals',
                'x': 0.5,
                'xref': 'paper',
                'y': -0.15,
                'yref': 'paper',
                'xanchor': 'center',
                'showarrow': False,
                'font': {'size': 11, 'color': '#666'}
            }
        ],
        margin=dict(t=120, b=100, l=80, r=40)
    )

    fig.write_html("output/chart_ebitda_bridge.html")
    print("✅ Chart 15 created: output/chart_ebitda_bridge.html")
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

    # Create all 14 charts (7 from Phase 3 + 4 from Phase 4 + 2 new + 1 Phase 6)
    create_revenue_vs_inventory_chart(data)
    create_revenue_growth_yoy_chart(data)
    create_margin_analysis_chart(data)
    create_operating_margin_waterfall(data)
    create_inventory_efficiency_chart(data)
    create_debt_health_chart(data)
    create_cash_flows_chart(data)
    create_earnings_quality_chart(data)  # Phase 4
    create_revenue_netincome_longterm_chart(data)  # Chart 12
    create_revenue_netincome_annual_chart(data)  # Chart 13
    create_expense_breakdown_chart(data)  # Chart 14 (Phase 6)
    create_ebitda_bridge_waterfall(data)  # NEW - Chart 15 (Phase 7)
    create_margin_bridge_waterfall(data)
    create_risk_trends_chart()
    create_risk_heatmap_grid()

    print("\n✅ All 15 visualizations created in output/ directory")
    print("   Open the .html files in your browser to view interactive charts:")
    print("     - chart_revenue_vs_inventory.html")
    print("     - chart_revenue_growth_yoy.html")
    print("     - chart_margin_analysis.html")
    print("     - chart_operating_margin_waterfall.html")
    print("     - chart_inventory_efficiency.html")
    print("     - chart_debt_health.html")
    print("     - chart_cash_flows.html")
    print("     - chart_earnings_quality.html (Phase 4)")
    print("     - chart_revenue_netincome_longterm.html (Chart 12)")
    print("     - chart_revenue_netincome_annual.html (Chart 13)")
    print("     - chart_expense_breakdown.html (Chart 14 - Phase 6)")
    print("     - chart_ebitda_bridge.html (NEW - Chart 15 - Phase 7)")
    print("     - chart_margin_bridge.html (Phase 4)")
    print("     - chart_risk_trends.html (Phase 4)")
    print("     - chart_risk_heatmap_grid.html (Phase 4)")


if __name__ == "__main__":
    main()
