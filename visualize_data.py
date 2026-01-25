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


def create_current_ratio_gauge(data):
    """
    Chart 16: Current Ratio Gauge - Pillar 2 Liquidity Analysis.

    Shows Current Ratio as gauge with health zones and dropdown to switch between quarters:
    - Red (<1.0): Cannot cover current liabilities
    - Yellow (1.0-1.5): Adequate liquidity
    - Green (>1.5): Healthy liquidity (retail benchmark)
    """
    # Extract balance sheet data for Q4 calculation
    liquidity_metrics = data['metrics'].get('liquidity', {})
    current_ratios = liquidity_metrics.get('current_ratio', [])
    current_assets = liquidity_metrics.get('current_assets_billion', [])
    current_liabilities = liquidity_metrics.get('current_liabilities_billion', [])
    periods = data['periods']

    if not current_ratios or all(cr is None for cr in current_ratios):
        print("⚠️  Skipping Current Ratio Gauge: No liquidity data available")
        return None

    # Step 1: Collect quarterly data from 10-Q filings (2022 onwards)
    quarterly_data = []
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-Q' and period['fiscal_year'] >= 2022:
            if current_assets[i] and current_liabilities[i]:
                quarterly_data.append({
                    'period': period['period'],
                    'fiscal_year': period['fiscal_year'],
                    'current_assets': current_assets[i],
                    'current_liabilities': current_liabilities[i],
                    'current_ratio': current_ratios[i]
                })

    # Step 2: Add Q4 from annual 10-K reports
    # NOTE: Current Assets and Current Liabilities are point-in-time balance sheet items,
    # NOT cumulative like income statement items. The annual 10-K value IS the Q4 end value.
    for i, period in enumerate(periods):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']
            annual_ca = current_assets[i]
            annual_cl = current_liabilities[i]
            annual_ratio = current_ratios[i]

            # For balance sheet items, the FY (year-end) value equals Q4 end value
            if annual_ca and annual_cl and annual_ratio:
                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'current_assets': annual_ca,
                    'current_liabilities': annual_cl,
                    'current_ratio': annual_ratio
                })

    if not quarterly_data:
        print("⚠️  Skipping Current Ratio Gauge: No valid quarterly data")
        return None

    # Sort chronologically (Q1 2022, Q2 2022, ..., Q4 2024, Q1 2025, ...)
    quarterly_data.sort(key=lambda x: (x['fiscal_year'], 1 if 'Q1' in x['period'] else 2 if 'Q2' in x['period'] else 3 if 'Q3' in x['period'] else 4))

    # Step 3: Create figure with multiple indicator traces (one per period)
    fig = go.Figure()

    for idx, period_data in enumerate(quarterly_data):
        period = period_data['period']
        ratio = period_data['current_ratio']

        # Create gauge indicator for this period
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=ratio,
            delta={
                'reference': 1.5,
                'increasing': {'color': 'green'},
                'decreasing': {'color': 'red'},
                'font': {'size': 24}  # Smaller delta font
            },
            title={'text': f"Current Ratio ({period})", 'font': {'size': 18}},
            number={'font': {'size': 48}},
            gauge={
                'axis': {'range': [None, 3.0], 'tickwidth': 1, 'tickfont': {'size': 14}},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 1.0], 'color': '#ffcccc'},    # Red - Warning
                    {'range': [1.0, 1.5], 'color': '#ffffcc'},  # Yellow - Adequate
                    {'range': [1.5, 3.0], 'color': '#ccffcc'}   # Green - Healthy
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 1.5
                }
            },
            domain={'x': [0, 1], 'y': [0, 1]},
            visible=(idx == len(quarterly_data) - 1)  # Show most recent by default
        ))

    # Create dropdown menu buttons (reverse order for most recent first)
    buttons = []
    for idx, period_data in enumerate(reversed(quarterly_data)):
        actual_idx = len(quarterly_data) - 1 - idx
        visible_array = [False] * len(quarterly_data)
        visible_array[actual_idx] = True

        buttons.append({
            'label': period_data['period'],
            'method': 'update',
            'args': [
                {'visible': visible_array},
                {
                    'title': {
                        'text': f"Target: Current Ratio Gauge (Liquidity Health)<br><sub style='font-size:11px'>Formula: Current Assets ÷ Current Liabilities | Benchmark: >1.5 for retail | Red (<1.0) Yellow (1.0-1.5) Green (>1.5)</sub>",
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.95,
                        'yanchor': 'top',
                        'font': {'size': 20}
                    }
                }
            ]
        })

    # Initial layout
    fig.update_layout(
        title={
            'text': f"Target: Current Ratio Gauge (Liquidity Health)<br><sub style='font-size:11px'>Formula: Current Assets ÷ Current Liabilities | Benchmark: >1.5 for retail | Red (<1.0) Yellow (1.0-1.5) Green (>1.5)</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top',
            'font': {'size': 20}
        },
        height=550,
        margin=dict(t=140, b=80, l=60, r=60),
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.17,
            'xanchor': 'left',
            'y': 1.15,
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
                'y': 1.15,
                'yref': 'paper',
                'align': 'left',
                'showarrow': False,
                'font': {'size': 12, 'color': '#333'}
            }
        ]
    )

    fig.write_html("output/chart_current_ratio_gauge.html")
    print("✅ Chart 16 created: output/chart_current_ratio_gauge.html")
    return fig


def create_capital_structure_donut(data):
    """
    Chart 17: Capital Structure Donut - Pillar 2 Solvency Analysis.

    Shows most recent split between Total Debt and Stockholders' Equity.
    Center displays Debt-to-Equity ratio.
    """
    debt_metrics = data['metrics'].get('debt', {})
    total_debts = debt_metrics.get('total_debt_billion', [])
    periods = [p['period'] for p in data['periods']]

    # Need to extract stockholders equity from detailed analysis JSON
    detailed_path = Path("output/target_analysis.json")
    if not detailed_path.exists():
        print("⚠️  Skipping Capital Structure Donut: target_analysis.json not found")
        return None

    with open(detailed_path, 'r') as f:
        detailed_data = json.load(f)

    # Collect ALL 10-K filings with complete balance sheet data
    fiscal_year_data = []

    for filing in detailed_data['filings']:
        if filing['filing_type'] == '10-K':
            vital = filing.get('vital_signs', {})
            debt_m = filing.get('debt_metrics', {})

            total_debt = debt_m.get('total_debt_billion')
            stockholders_equity = vital.get('stockholders_equity_billion')
            de_ratio = debt_m.get('debt_to_equity_ratio')

            if total_debt and stockholders_equity and de_ratio:
                fiscal_year_data.append({
                    'period': filing['period'],
                    'fiscal_year': filing.get('fiscal_year', 0),
                    'total_debt': total_debt,
                    'stockholders_equity': stockholders_equity,
                    'de_ratio': de_ratio
                })

    if not fiscal_year_data:
        print("⚠️  Skipping Capital Structure Donut: No balance sheet data available")
        return None

    # Sort chronologically
    fiscal_year_data.sort(key=lambda x: x['fiscal_year'])

    # Create figure with multiple Pie traces (one per fiscal year)
    fig = go.Figure()

    for idx, fy_data in enumerate(fiscal_year_data):
        fig.add_trace(go.Pie(
            labels=['Total Debt', 'Stockholders\' Equity'],
            values=[fy_data['total_debt'], fy_data['stockholders_equity']],
            hole=0.5,
            domain={'x': [0.05, 0.75], 'y': [0.1, 0.9]},  # Fixed position - centered, leaving right side for dropdown
            marker=dict(colors=['#ff6666', '#66cc66']),
            textinfo='label+percent',
            textposition='outside',
            automargin=False,  # Prevent automatic margin adjustments
            pull=[0, 0],  # No slice separation
            hovertemplate='<b>%{label}</b><br>$%{value:.2f}B<br>%{percent}<extra></extra>',
            visible=(idx == len(fiscal_year_data) - 1),  # Show most recent by default
            name=fy_data['period']
        ))

    # Create dropdown menu buttons (newest first)
    buttons = []
    for i in range(len(fiscal_year_data) - 1, -1, -1):
        fy_data = fiscal_year_data[i]
        visible_array = [False] * len(fiscal_year_data)
        visible_array[i] = True

        buttons.append({
            'label': fy_data['period'],
            'method': 'update',
            'args': [
                {
                    'visible': visible_array,
                    'textinfo': ['label+percent'],
                    'textposition': ['outside']
                },
                {
                    'title': {
                        'text': f"Target: Capital Structure ({fy_data['period']})<br><sub>Total Debt vs Stockholders' Equity</sub>",
                        'x': 0.5,
                        'xanchor': 'center'
                    },
                    'annotations': [
                        {
                            'text': 'Select Fiscal Year:',
                            'x': 1.02,
                            'xref': 'paper',
                            'y': 0.95,
                            'yref': 'paper',
                            'xanchor': 'left',
                            'showarrow': False,
                            'font': {'size': 12, 'color': '#333'}
                        },
                        {
                            'text': f"D/E Ratio<br><b>{fy_data['de_ratio']:.2f}</b>",
                            'x': 0.4,
                            'y': 0.5,
                            'font_size': 16,
                            'showarrow': False
                        }
                    ]
                }
            ]
        })

    # Initial layout (most recent period)
    most_recent = fiscal_year_data[-1]

    fig.update_layout(
        title={
            'text': f"Target: Capital Structure ({most_recent['period']})<br><sub>Total Debt vs Stockholders' Equity</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        autosize=False,  # Disable automatic resizing
        width=800,  # Fixed width
        height=600,  # Increased from 550 to accommodate dropdown
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, b=100, l=60, r=200),  # Reduced top margin, increased right margin for dropdown
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 1.02,
            'xanchor': 'left',
            'y': 0.9,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': '#BDBDBD',
            'borderwidth': 1
        }],
        annotations=[
            {
                'text': 'Select Fiscal Year:',
                'x': 1.02,
                'xref': 'paper',
                'y': 0.95,
                'yref': 'paper',
                'xanchor': 'left',
                'showarrow': False,
                'font': {'size': 12, 'color': '#333'}
            },
            {
                'text': f"D/E Ratio<br><b>{most_recent['de_ratio']:.2f}</b>",
                'x': 0.4,
                'y': 0.5,
                'font_size': 16,
                'showarrow': False
            }
        ]
    )

    fig.write_html("output/chart_capital_structure_donut.html")
    print("✅ Chart 17 created: output/chart_capital_structure_donut.html")
    return fig


def create_debt_to_ebitda_trend(data):
    """
    Chart 18: Debt-to-EBITDA Trend - Pillar 2 Solvency Analysis.

    Shows quarterly Debt-to-EBITDA ratio trend with color-coded health zones:
    - Green (<3.0x): Healthy leverage
    - Yellow (3.0-5.0x): Moderate leverage
    - Red (>5.0x): Risky leverage
    """
    debt_metrics = data['metrics'].get('debt', {})
    debt_to_ebitda = debt_metrics.get('debt_to_ebitda_ratio', [])
    periods = [p['period'] for p in data['periods']]

    if not debt_to_ebitda or all(d is None for d in debt_to_ebitda):
        print("⚠️  Skipping Debt-to-EBITDA Trend: No data available")
        return None

    # Create period labels and filter out None values
    valid_data = [(p, d) for p, d in zip(periods, debt_to_ebitda) if d is not None]
    if not valid_data:
        print("⚠️  Skipping Debt-to-EBITDA Trend: No valid data points")
        return None

    period_labels, ratios = zip(*valid_data)

    # Color-code markers based on health thresholds
    marker_colors = []
    for ratio in ratios:
        if ratio < 3.0:
            marker_colors.append('#66cc66')  # Green - Healthy
        elif ratio <= 5.0:
            marker_colors.append('#ffcc66')  # Yellow - Moderate
        else:
            marker_colors.append('#ff6666')  # Red - Risky

    # Create line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(period_labels),
        y=list(ratios),
        mode='lines+markers+text',
        name='Debt-to-EBITDA',
        text=[f"{r:.2f}x" for r in ratios],
        textposition="top center",
        textfont=dict(size=10),
        line=dict(color='#4472C4', width=3),
        marker=dict(
            size=10,
            color=marker_colors,
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{x}</b><br>Debt-to-EBITDA: %{y:.2f}x<extra></extra>'
    ))

    # Add legend entries for color-coded health zones
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=10, color='#66cc66', line=dict(color='white', width=2)),
        name='Healthy (<3.0x)',
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=10, color='#ffcc66', line=dict(color='white', width=2)),
        name='Moderate (3.0-5.0x)',
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=10, color='#ff6666', line=dict(color='white', width=2)),
        name='Risky (>5.0x)',
        showlegend=True
    ))

    # Add reference lines (without annotations - we'll add them separately)
    fig.add_hline(y=3.0, line_dash="dash", line_color="green", line_width=1)
    fig.add_hline(y=5.0, line_dash="dash", line_color="red", line_width=1)

    fig.update_layout(
        title={
            'text': "Target: Debt-to-EBITDA Trend<br><sub>Lower is better - Shows how many years of EBITDA needed to repay debt (Healthy: <3.0x)</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title="Fiscal Year",
        yaxis_title="Debt-to-EBITDA Ratio (x)",
        height=550,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, b=120, l=80, r=40),
        annotations=[
            dict(
                text="Healthy Threshold (3.0x)",
                x=0.02,
                y=3.0,
                xref="paper",
                yref="y",
                xanchor="left",
                yanchor="middle",
                showarrow=False,
                bgcolor="white",
                bordercolor="green",
                borderwidth=1,
                borderpad=4,
                font=dict(size=10)
            ),
            dict(
                text="Risky Threshold (5.0x)",
                x=0.02,
                y=5.0,
                xref="paper",
                yref="y",
                xanchor="left",
                yanchor="middle",
                showarrow=False,
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                borderpad=4,
                font=dict(size=10)
            )
        ]
    )

    fig.write_html("output/chart_debt_to_ebitda_trend.html")
    print("✅ Chart 18 created: output/chart_debt_to_ebitda_trend.html")
    return fig


def create_dupont_analysis_breakdown(data):
    """
    Chart 19: DuPont Analysis Breakdown (Pillar 3)

    Shows how ROE breaks down into three multiplicative components:
    - Profit Margin (Net Income / Revenue)
    - Asset Turnover (Revenue / Total Assets)
    - Financial Leverage (Total Assets / Stockholders Equity)

    Formula: ROE = Profit Margin × Asset Turnover × Financial Leverage

    Uses dropdown menu to switch between fiscal quarters (Q1-Q4).
    Q4 values are calculated from annual 10-K data minus Q1-Q3.
    """
    import plotly.graph_objects as go

    # Step 1: Collect Q1-Q3 quarterly data from 10-Q filings
    periods_data = []

    for i, period in enumerate(data['periods']):
        # Only include 10-Q quarterly filings (exclude annual 10-K)
        if period['filing_type'] != '10-Q':
            continue

        period_label = period.get('period')  # e.g., "Q3 2025"
        fiscal_year = period.get('fiscal_year')
        fiscal_quarter = period.get('fiscal_quarter')

        # Get DuPont components
        roe = data['metrics']['debt'].get('return_on_equity_percent', [None])[i]
        profit_margin = data['metrics']['margins'].get('net_profit_margin_percent', [None])[i]
        asset_turnover = data['metrics']['debt'].get('dupont_asset_turnover', [None])[i]
        financial_leverage = data['metrics']['debt'].get('dupont_financial_leverage', [None])[i]

        # Get revenue and net income for Q4 calculation
        revenue = data['metrics']['revenue'].get('net_sales_billion', [None])[i]
        net_income = data['metrics']['cash_flows'].get('net_income_billion', [None])[i]

        # Only include periods with complete data
        if all(v is not None for v in [roe, profit_margin, asset_turnover, financial_leverage, revenue, net_income]):
            periods_data.append({
                'period': period_label,
                'fiscal_year': fiscal_year,
                'fiscal_quarter': fiscal_quarter,
                'roe': roe,
                'profit_margin': profit_margin,
                'asset_turnover': asset_turnover,
                'financial_leverage': financial_leverage,
                'revenue': revenue,
                'net_income': net_income
            })

    # Step 2: Calculate Q4 from annual 10-K reports
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K' and period['fiscal_year'] >= 2022:
            fy = period['fiscal_year']

            # Get annual values
            annual_revenue = data['metrics']['revenue'].get('net_sales_billion', [None])[i]
            annual_net_income = data['metrics']['cash_flows'].get('net_income_billion', [None])[i]
            annual_asset_turnover = data['metrics']['debt'].get('dupont_asset_turnover', [None])[i]
            annual_financial_leverage = data['metrics']['debt'].get('dupont_financial_leverage', [None])[i]

            # Skip if annual data incomplete
            if not all([annual_revenue, annual_net_income, annual_asset_turnover, annual_financial_leverage]):
                continue

            # Find Q1, Q2, Q3 for this fiscal year
            q1 = q2 = q3 = None
            for q in periods_data:
                if q['fiscal_year'] == fy:
                    if q['fiscal_quarter'] == 1:
                        q1 = q
                    elif q['fiscal_quarter'] == 2:
                        q2 = q
                    elif q['fiscal_quarter'] == 3:
                        q3 = q

            # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
            if all([q1, q2, q3]):
                # Q4 Income statement items (cumulative → subtract Q1-Q3)
                q4_revenue = annual_revenue - (q1['revenue'] + q2['revenue'] + q3['revenue'])
                q4_net_income = annual_net_income - (q1['net_income'] + q2['net_income'] + q3['net_income'])

                # Q4 Balance sheet items (year-end values from 10-K)
                # Back-calculate Total Assets and Stockholders Equity from annual ratios
                # Total Assets = Revenue / Asset Turnover (year-end value)
                total_assets = annual_revenue / annual_asset_turnover if annual_asset_turnover > 0 else None
                # Stockholders Equity = Total Assets / Financial Leverage (year-end value)
                stockholders_equity = total_assets / annual_financial_leverage if (total_assets and annual_financial_leverage > 0) else None

                if all([q4_revenue, total_assets, stockholders_equity]) and q4_revenue > 0 and stockholders_equity > 0:
                    # Calculate Q4 DuPont components
                    q4_profit_margin = (q4_net_income / q4_revenue) * 100
                    q4_asset_turnover = q4_revenue / total_assets
                    q4_financial_leverage = total_assets / stockholders_equity
                    q4_roe = (q4_net_income / stockholders_equity) * 100

                    periods_data.append({
                        'period': f'Q4 {fy}',
                        'fiscal_year': fy,
                        'fiscal_quarter': 4,
                        'roe': round(q4_roe, 2),
                        'profit_margin': round(q4_profit_margin, 2),
                        'asset_turnover': round(q4_asset_turnover, 2),
                        'financial_leverage': round(q4_financial_leverage, 2),
                        'revenue': q4_revenue,
                        'net_income': q4_net_income
                    })

    if not periods_data:
        print("⚠️  Skipping DuPont Analysis: No complete quarterly data available")
        return None

    # Sort by fiscal year, then quarter (for proper chronological order)
    def sort_key(item):
        year = item['fiscal_year']
        quarter = item.get('fiscal_quarter', 4)
        return (year, quarter)

    periods_data.sort(key=sort_key)

    # Calculate global Y-axis range for consistent scaling across all periods
    all_values = []
    for p in periods_data:
        all_values.extend([p['profit_margin'], p['asset_turnover'], p['financial_leverage'], p['roe']])

    y_min = 0  # Always start at 0
    y_max = max(all_values) * 1.1  # Add 10% padding

    # Create figure with subplots
    fig = go.Figure()

    # Create one grouped bar chart trace set per fiscal year
    for idx, period_data in enumerate(periods_data):
        period_label = period_data['period']

        # Visibility: Only most recent period visible by default
        visible = (idx == len(periods_data) - 1)

        # Bar 1: Profit Margin
        fig.add_trace(go.Bar(
            name='Profit Margin (%)',
            x=['Profit Margin'],
            y=[period_data['profit_margin']],
            marker_color='#3498db',  # Blue
            text=[f"{period_data['profit_margin']:.2f}%"],
            textposition='outside',
            visible=visible,
            showlegend=(idx == 0)  # Only show legend for first trace set
        ))

        # Bar 2: Asset Turnover
        fig.add_trace(go.Bar(
            name='Asset Turnover (x)',
            x=['Asset Turnover'],
            y=[period_data['asset_turnover']],
            marker_color='#e67e22',  # Orange
            text=[f"{period_data['asset_turnover']:.2f}x"],
            textposition='outside',
            visible=visible,
            showlegend=(idx == 0)
        ))

        # Bar 3: Financial Leverage
        fig.add_trace(go.Bar(
            name='Financial Leverage (x)',
            x=['Financial Leverage'],
            y=[period_data['financial_leverage']],
            marker_color='#9b59b6',  # Purple
            text=[f"{period_data['financial_leverage']:.2f}x"],
            textposition='outside',
            visible=visible,
            showlegend=(idx == 0)
        ))

        # Bar 4: ROE (Result)
        fig.add_trace(go.Bar(
            name='ROE (%)',
            x=['ROE (Result)'],
            y=[period_data['roe']],
            marker_color='#27ae60',  # Green
            text=[f"{period_data['roe']:.2f}%"],
            textposition='outside',
            visible=visible,
            showlegend=(idx == 0)
        ))

    # Create dropdown menu buttons (reverse order for most recent first)
    buttons = []
    for idx_rev in range(len(periods_data) - 1, -1, -1):
        period_data = periods_data[idx_rev]
        # Calculate visibility array (4 traces per period)
        visible_array = [False] * (len(periods_data) * 4)
        start_idx = idx_rev * 4
        visible_array[start_idx:start_idx + 4] = [True, True, True, True]

        buttons.append({
            'label': period_data['period'],
            'method': 'update',
            'args': [
                {'visible': visible_array},
                {
                    'title': {
                        'text': f"Target: DuPont Analysis ({period_data['period']})<br><sub>ROE = Profit Margin × Asset Turnover × Financial Leverage</sub>",
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.97,
                        'yanchor': 'top'
                    },
                    'yaxis': {'range': [y_min, y_max]}  # Preserve fixed Y-axis range
                }
            ]
        })

    # Layout
    most_recent = periods_data[-1]['period']
    fig.update_layout(
        title={
            'text': f"Target: DuPont Analysis ({most_recent})<br><sub>ROE = Profit Margin × Asset Turnover × Financial Leverage</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.97,
            'yanchor': 'top'
        },
        xaxis_title="DuPont Components",
        yaxis_title="Value",
        yaxis=dict(range=[y_min, y_max]),  # Fixed Y-axis range for consistent scaling
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.02,
            'xanchor': 'left',
            'y': 1.15,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': '#BDBDBD',
            'borderwidth': 1
        }],
        margin=dict(t=140, b=80, l=80, r=40)
    )

    # Save chart
    output_path = 'output/chart_dupont_analysis.html'
    fig.write_html(output_path)
    print(f"✅ Chart 19 created: {output_path}")
    return fig


def _detect_ccc_data_availability(data):
    """
    Detect if quarterly CCC data is available for charting.

    This function scans all periods to determine whether the company reports
    receivables in quarterly 10-Q filings (enabling quarterly CCC visualization)
    or only in annual 10-K filings (requiring fallback to annual visualization).

    Returns:
        dict: {
            'quarterly_count': int - Number of quarterly periods with complete CCC
            'annual_count': int - Number of annual periods with complete CCC
            'use_quarterly': bool - True if quarterly data sufficient (>=8 quarters)
            'message': str - Info message about data source for console output
        }
    """
    quarterly_count = 0
    annual_count = 0

    for i, period in enumerate(data['periods']):
        # Get CCC components
        dsi = data['metrics']['inventory'].get('days_sales_of_inventory', [None])[i]
        dso = data['metrics']['efficiency'].get('days_sales_outstanding', [None])[i]
        dpo = data['metrics']['efficiency'].get('days_payable_outstanding', [None])[i]

        # Check if all components present (required for complete CCC calculation)
        if all(v is not None for v in [dsi, dso, dpo]):
            if period['filing_type'] == '10-Q':
                quarterly_count += 1
            elif period['filing_type'] == '10-K':
                annual_count += 1

    # Decision: Use quarterly if at least 8 quarters available (2 years of data)
    # This threshold ensures sufficient data for meaningful trend analysis
    use_quarterly = quarterly_count >= 8

    if use_quarterly:
        message = f"Using {quarterly_count} quarterly periods (receivables available in 10-Q filings)"
    else:
        message = f"Using {annual_count} annual periods (receivables only in 10-K filings)"

    return {
        'quarterly_count': quarterly_count,
        'annual_count': annual_count,
        'use_quarterly': use_quarterly,
        'message': message
    }


def create_cash_conversion_cycle_chart(data):
    """
    Chart 20: Cash Conversion Cycle Trend (Pillar 3: Operational Efficiency)

    Shows the number of days it takes to convert resource inputs into cash.
    Formula: CCC = DSI + DSO - DPO

    Intelligently selects quarterly or annual data based on availability:
    - Quarterly data (15 periods): If receivables reported in 10-Q filings (>=8 quarters)
    - Annual data (5-10 periods): If receivables only in 10-K filings

    Lower CCC is better - indicates faster cash conversion.

    Args:
        data: Time-series data dictionary from target_timeseries.json

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    # Step 1: Detect data availability
    availability = _detect_ccc_data_availability(data)
    use_quarterly = availability['use_quarterly']

    print(f"\n📊 Chart 20 Data Detection: {availability['message']}")

    # Step 2: Collect periods based on availability
    periods = []
    dsi_values = []
    dso_values = []
    dpo_values = []
    ccc_values = []

    if use_quarterly:
        # QUARTERLY APPROACH: Collect Q1-Q3 from 10-Q filings
        quarterly_data = []

        for i, period in enumerate(data['periods']):
            if period['filing_type'] == '10-Q':
                period_label = period.get('period')

                # Get values
                dsi = data['metrics']['inventory'].get('days_sales_of_inventory', [None])[i]
                dso = data['metrics']['efficiency'].get('days_sales_outstanding', [None])[i]
                dpo = data['metrics']['efficiency'].get('days_payable_outstanding', [None])[i]
                ccc = data['metrics']['efficiency'].get('cash_conversion_cycle_days', [None])[i]

                # Only include if all values present
                if all(v is not None for v in [dsi, dso, dpo, ccc]):
                    quarterly_data.append({
                        'period': period_label,
                        'fiscal_year': period.get('fiscal_year'),
                        'fiscal_quarter': period.get('fiscal_quarter'),
                        'dsi': dsi,
                        'dso': dso,
                        'dpo': dpo,
                        'ccc': ccc
                    })

        # CALCULATE Q4 from annual 10-K reports
        for i, period in enumerate(data['periods']):
            if period['filing_type'] == '10-K':
                fy = period.get('fiscal_year')

                # Get annual raw values for Q4 calculation
                annual_revenue = data['metrics']['revenue'].get('net_sales_billion', [None])[i]
                annual_cogs = data['metrics']['revenue'].get('cost_of_sales_billion', [None])[i]
                annual_inventory = data['metrics']['inventory'].get('inventory_billion', [None])[i]

                # Check for current_receivables_billion - this is the key field needed for DSO
                annual_receivables = None
                if 'liquidity' in data['metrics'] and 'current_receivables_billion' in data['metrics']['liquidity']:
                    annual_receivables = data['metrics']['liquidity'].get('current_receivables_billion', [None])[i]

                # Fallback: check if receivables is in efficiency metrics
                if annual_receivables is None:
                    annual_receivables = data['metrics'].get('efficiency', {}).get('current_receivables_billion', [None])[i] if isinstance(data['metrics'].get('efficiency'), dict) else None

                # Check for current_payables_billion
                annual_payables = None
                if 'liquidity' in data['metrics'] and 'current_payables_billion' in data['metrics']['liquidity']:
                    annual_payables = data['metrics']['liquidity'].get('current_payables_billion', [None])[i]

                # Fallback: check if payables is in efficiency metrics
                if annual_payables is None:
                    annual_payables = data['metrics'].get('efficiency', {}).get('current_payables_billion', [None])[i] if isinstance(data['metrics'].get('efficiency'), dict) else None

                # Find Q1, Q2, Q3 for this fiscal year
                q1 = q2 = q3 = None
                for q in quarterly_data:
                    if q['fiscal_year'] == fy:
                        if q['fiscal_quarter'] == 1:
                            q1 = q
                        elif q['fiscal_quarter'] == 2:
                            q2 = q
                        elif q['fiscal_quarter'] == 3:
                            q3 = q

                # Calculate Q4 if all quarters present and balance sheet data available
                if all([q1, q2, q3]) and all(v is not None for v in [annual_revenue, annual_cogs, annual_inventory, annual_receivables, annual_payables]):
                    # Q4 DSI: Uses annual COGS and year-end inventory
                    # Formula: DSI = 365 / (COGS / Inventory) = (365 * Inventory) / COGS
                    q4_dsi = (365 * annual_inventory) / annual_cogs if annual_cogs > 0 else None

                    # Q4 DSO: Uses annual revenue and year-end receivables
                    # Formula: DSO = 365 / (Revenue / Receivables) = (365 * Receivables) / Revenue
                    q4_dso = (365 * annual_receivables) / annual_revenue if annual_revenue > 0 else None

                    # Q4 DPO: Uses annual COGS and year-end payables
                    # Formula: DPO = 365 / (COGS / Payables) = (365 * Payables) / COGS
                    q4_dpo = (365 * annual_payables) / annual_cogs if annual_cogs > 0 else None

                    # Q4 CCC
                    if all(v is not None for v in [q4_dsi, q4_dso, q4_dpo]):
                        q4_ccc = q4_dsi + q4_dso - q4_dpo

                        quarterly_data.append({
                            'period': f'Q4 {fy}',
                            'fiscal_year': fy,
                            'fiscal_quarter': 4,
                            'dsi': q4_dsi,
                            'dso': q4_dso,
                            'dpo': q4_dpo,
                            'ccc': q4_ccc
                        })

        # Sort chronologically
        quarterly_data.sort(key=lambda x: (x['fiscal_year'], x['fiscal_quarter']))

        # Extract lists for plotting
        for q in quarterly_data:
            periods.append(q['period'])
            dsi_values.append(q['dsi'])
            dso_values.append(q['dso'])
            dpo_values.append(q['dpo'])
            ccc_values.append(q['ccc'])

    else:
        # ANNUAL APPROACH: Use 10-K filings only (fallback for companies without quarterly receivables)
        for i, period in enumerate(data['periods']):
            if period['filing_type'] != '10-K':
                continue

            period_label = f"FY{period.get('fiscal_year')}"

            # Get values
            dsi = data['metrics']['inventory'].get('days_sales_of_inventory', [None])[i]
            dso = data['metrics']['efficiency'].get('days_sales_outstanding', [None])[i]
            dpo = data['metrics']['efficiency'].get('days_payable_outstanding', [None])[i]
            ccc = data['metrics']['efficiency'].get('cash_conversion_cycle_days', [None])[i]

            # Only include if all values present
            if all(v is not None for v in [dsi, dso, dpo, ccc]):
                periods.append(period_label)
                dsi_values.append(dsi)
                dso_values.append(dso)
                dpo_values.append(dpo)
                ccc_values.append(ccc)

    # Create figure
    fig = go.Figure()

    # Line 1: DSI (Days Sales of Inventory)
    fig.add_trace(go.Scatter(
        x=periods,
        y=dsi_values,
        mode='lines+markers',
        name='DSI (Days in Inventory)',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=8, line=dict(color='white', width=2)),
        hovertemplate='<b>DSI</b>: %{y:.1f} days<extra></extra>'
    ))

    # Line 2: DSO (Days Sales Outstanding)
    fig.add_trace(go.Scatter(
        x=periods,
        y=dso_values,
        mode='lines+markers',
        name='DSO (Days to Collect Receivables)',
        line=dict(color='#f39c12', width=3),
        marker=dict(size=8, line=dict(color='white', width=2)),
        hovertemplate='<b>DSO</b>: %{y:.1f} days<extra></extra>'
    ))

    # Line 3: DPO (Days Payables Outstanding)
    fig.add_trace(go.Scatter(
        x=periods,
        y=dpo_values,
        mode='lines+markers',
        name='DPO (Days to Pay Suppliers)',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8, line=dict(color='white', width=2)),
        hovertemplate='<b>DPO</b>: %{y:.1f} days<extra></extra>'
    ))

    # Line 4: CCC (Cash Conversion Cycle)
    fig.add_trace(go.Scatter(
        x=periods,
        y=ccc_values,
        mode='lines+markers',
        name='CCC (Total Cycle)',
        line=dict(color='#27ae60', width=4, dash='solid'),
        marker=dict(size=10, line=dict(color='white', width=2)),
        hovertemplate='<b>CCC</b>: %{y:.1f} days<extra></extra>'
    ))

    # Add reference line at 60 days (retail industry benchmark)
    fig.add_hline(
        y=60,
        line_dash="dash",
        line_color="gray",
        annotation_text="Retail Benchmark (60 days)",
        annotation_position="right"  # Changed from left to right to avoid cut-off
    )

    # Add reference line at 0 (for context)
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="black",
        opacity=0.3
    )

    # Determine data frequency for subtitle
    data_freq = "Quarterly" if use_quarterly else "Annual"
    period_range = f"{periods[0]} - {periods[-1]}" if periods else "N/A"

    # Layout
    fig.update_layout(
        title={
            'text': f"Target: Cash Conversion Cycle Trend<br><sub>Lower is better - Shows days to convert resources into cash (CCC = DSI + DSO - DPO)<br>{data_freq} data: {period_range}</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title="Fiscal Year",
            tickangle=0,  # Keep horizontal (only 5 labels, should fit with 1000px width)
            tickmode='linear'  # Show all 5 labels explicitly
        ),
        yaxis_title="Days",
        height=600,
        width=1000,  # Increase from default ~700px to 1000px for better spacing
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, b=120, l=100, r=100)  # Balanced margins to center chart and prevent cut-off
    )

    # Save chart with config to center it properly
    output_path = 'output/chart_cash_conversion_cycle.html'
    config = {
        'displayModeBar': True,
        'responsive': True
    }
    fig.write_html(output_path, config=config)

    # Console output with data source information
    print(f"✅ Chart 20 created: {output_path}")
    print(f"   Data source: {availability['message']}")
    print(f"   Periods displayed: {len(periods)}")

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

    # Create all 18 charts (7 from Phase 3 + 4 from Phase 4 + 2 new + 1 Phase 6 + 1 Phase 7 + 3 Pillar 2)
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
    create_ebitda_bridge_waterfall(data)  # Chart 15 (Phase 7)
    create_margin_bridge_waterfall(data)
    create_risk_trends_chart()
    create_risk_heatmap_grid()

    # Pillar 2: Liquidity & Solvency visualizations
    create_current_ratio_gauge(data)  # Chart 16
    create_capital_structure_donut(data)  # Chart 17
    create_debt_to_ebitda_trend(data)  # Chart 18

    # Pillar 3: Operational Efficiency visualizations
    create_dupont_analysis_breakdown(data)  # Chart 19
    create_cash_conversion_cycle_chart(data)  # Chart 20

    print("\n✅ All 20 visualizations created in output/ directory")
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
    print("     - chart_ebitda_bridge.html (Chart 15 - Phase 7)")
    print("     - chart_margin_bridge.html (Phase 4)")
    print("     - chart_risk_trends.html (Phase 4)")
    print("     - chart_risk_heatmap_grid.html (Phase 4)")
    print("     - chart_current_ratio_gauge.html (Chart 16 - Pillar 2)")
    print("     - chart_capital_structure_donut.html (Chart 17 - Pillar 2)")
    print("     - chart_debt_to_ebitda_trend.html (Chart 18 - Pillar 2)")
    print("     - chart_dupont_analysis.html (Chart 19 - Pillar 3)")
    print("     - chart_cash_conversion_cycle.html (Chart 20 - Pillar 3)")


if __name__ == "__main__":
    main()
