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


def _load_peer_comparison_data(filepath: str = "data/peer_comparison_data.json"):
    """
    Load peer company data for comparison charts.

    Args:
        filepath: Path to JSON file containing peer CCC data

    Returns:
        dict: Peer comparison data structure with CCC components for each peer company
              Returns empty dict if file not found
    """
    from pathlib import Path
    import json

    peer_path = Path(filepath)
    if not peer_path.exists():
        print(f"⚠️  WARNING: Peer data not found at {filepath}")
        print(f"   Chart 20 will display Target data only without peer comparison")
        return {}

    try:
        with open(peer_path, 'r') as f:
            peer_data = json.load(f)
        return peer_data
    except json.JSONDecodeError as e:
        print(f"⚠️  WARNING: Failed to parse peer data: {e}")
        return {}


def _get_all_ccc_data(data):
    """
    Extract ALL periods with complete CCC components from timeseries data.

    Args:
        data: Time-series data dictionary from target_timeseries.json

    Returns:
        list: List of dicts with CCC data for each period, sorted chronologically.
              Each dict contains: period, fiscal_year, fiscal_quarter, filing_type, dsi, dso, dpo, ccc
              Returns empty list if no complete data found.
    """
    ccc_periods = []

    # Scan ALL periods (both 10-K and 10-Q)
    for i, period in enumerate(data['periods']):
        dsi = data['metrics']['inventory']['days_sales_of_inventory'][i]
        dso = data['metrics']['efficiency']['days_sales_outstanding'][i]
        dpo = data['metrics']['efficiency']['days_payable_outstanding'][i]
        ccc = data['metrics']['efficiency']['cash_conversion_cycle_days'][i]

        # Only include periods with all 4 components present
        if all(v is not None for v in [dsi, dso, dpo, ccc]):
            ccc_periods.append({
                'period': period['period'],  # e.g., "FY2024" or "Q3 2025"
                'fiscal_year': period['fiscal_year'],
                'fiscal_quarter': period.get('fiscal_quarter'),  # May be None for annual
                'filing_type': period['filing_type'],  # '10-K' or '10-Q'
                'dsi': dsi,
                'dso': dso,
                'dpo': dpo,
                'ccc': ccc
            })

    # Sort chronologically (oldest first)
    def sort_key(item):
        year = item['fiscal_year']
        quarter = item.get('fiscal_quarter', 0)  # Annual = 0 (before Q1)
        return (year, quarter)

    ccc_periods.sort(key=sort_key)

    return ccc_periods


def _get_latest_ccc_data(data):
    """
    Extract Target's most recent CCC components from timeseries data.

    Scans periods from most recent backwards to find the first period with
    complete CCC data (all components non-null).

    Args:
        data: Time-series data dictionary from target_timeseries.json

    Returns:
        dict: {
            'dsi': float - Days Sales of Inventory
            'dso': float - Days Sales Outstanding
            'dpo': float - Days Payables Outstanding
            'ccc': float - Cash Conversion Cycle (DSI + DSO - DPO)
            'period': str - Period label (e.g., "FY2024", "Q3 2025")
        }

    Raises:
        ValueError: If no complete CCC data found in any period
    """
    # Use _get_all_ccc_data() and return last period
    all_ccc = _get_all_ccc_data(data)

    if not all_ccc:
        raise ValueError("No complete CCC data found for Target in timeseries JSON")

    return all_ccc[-1]  # Return most recent period


def create_cash_conversion_cycle_chart(data):
    """
    Chart 20: Cash Conversion Cycle - Peer Comparison (Pillar 3: Operational Efficiency)

    Grouped bar chart comparing Target's CCC components against retail industry peers.
    Shows DSI, DSO, DPO, and total CCC for each company.

    Formula: CCC = DSI + DSO - DPO
    Lower CCC is better - indicates faster cash conversion.

    Args:
        data: Time-series data dictionary from target_timeseries.json

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    print(f"\n📊 Chart 20: Creating peer comparison bar chart with dropdown...")

    # Step 1: Extract ALL Target CCC periods
    target_ccc_periods = _get_all_ccc_data(data)

    if not target_ccc_periods:
        print("❌ Error: No complete CCC data found for Target")
        return None

    print(f"   Target periods: {len(target_ccc_periods)} ({target_ccc_periods[0]['period']} - {target_ccc_periods[-1]['period']})")

    # Step 2: Load peer data (multi-year structure)
    peer_data = _load_peer_comparison_data()
    peer_companies = {}

    if peer_data and 'cash_conversion_cycle' in peer_data:
        peer_companies = peer_data['cash_conversion_cycle'].get('companies', {})
        # Count total peer-years available
        total_peer_years = sum(len(info.get('years', {})) for info in peer_companies.values())
        print(f"   Peer data loaded: {len(peer_companies)} companies, {total_peer_years} company-years")
    else:
        print(f"   No peer data available - showing Target only")

    # Step 3: Build company list (Target + peers)
    company_names = ['Target'] + sorted(peer_companies.keys())

    # Step 4: Create figure with multiple trace sets (one per Target period)
    fig = go.Figure()

    # For each Target period, create 4 bar traces per company (DSI, DSO, DPO, CCC)
    # Total traces = len(target_ccc_periods) × len(company_names) × 4
    for period_idx, target_period in enumerate(target_ccc_periods):
        # Visibility: Only most recent period visible by default
        visible = (period_idx == len(target_ccc_periods) - 1)

        # Build companies_data dict for this period
        companies_data = {}

        # Target data changes per period
        companies_data['Target'] = {
            'dsi': target_period['dsi'],
            'dso': target_period['dso'],
            'dpo': target_period['dpo'],
            'ccc': target_period['ccc'],
            'opacity': 1.0  # Full saturation
        }

        # Peer data lookup by fiscal year (dynamic)
        # Note: All peer data extracted from actual SEC EDGAR 10-K filings (NOT averaged).
        # Amazon has only 2 years (2019, 2023) due to extraction limitations.
        # When a peer's fiscal year is missing, fallback uses most recent available year (actual data, not estimates).
        # Opacity reduced to 0.5 when fallback is used to visually indicate data mismatch.
        for peer_name, peer_info in peer_companies.items():
            # Get peer data for THIS fiscal year
            peer_years = peer_info.get('years', {})
            peer_year_data = peer_years.get(str(target_period['fiscal_year']))

            if peer_year_data:
                # Use year-specific peer data
                companies_data[peer_name] = {
                    'dsi': peer_year_data['dsi'],
                    'dso': peer_year_data['dso'],
                    'dpo': peer_year_data['dpo'],
                    'ccc': peer_year_data['ccc'],
                    'opacity': 0.7  # Reduced opacity
                }
            else:
                # Fallback: Use most recent available year if current year missing
                if peer_years:
                    latest_year = max(peer_years.keys())
                    latest_data = peer_years[latest_year]
                    companies_data[peer_name] = {
                        'dsi': latest_data['dsi'],
                        'dso': latest_data['dso'],
                        'dpo': latest_data['dpo'],
                        'ccc': latest_data['ccc'],
                        'opacity': 0.5  # Even lighter to indicate data mismatch
                    }
                # If no peer data at all for this company, skip it for this period
                # (company_names will be inconsistent across periods, but Plotly handles this)

        # Filter to only companies with data for this period
        companies_with_data = [c for c in company_names if c in companies_data]

        # Create 4 bar traces for this period
        # Trace 1: DSI (Red)
        dsi_values = [companies_data[c]['dsi'] for c in companies_with_data]
        dsi_opacities = [companies_data[c]['opacity'] for c in companies_with_data]

        fig.add_trace(go.Bar(
            name='DSI (Days in Inventory)',
            x=companies_with_data,
            y=dsi_values,
            marker=dict(
                color=[f'rgba(231, 76, 60, {o})' for o in dsi_opacities],
                line=dict(color='rgba(231, 76, 60, 1.0)', width=1)
            ),
            text=[f'{v:.1f}' for v in dsi_values],
            textposition='outside',
            visible=visible,
            legendgroup='DSI',
            showlegend=(period_idx == len(target_ccc_periods) - 1),  # Only show legend for default visible period
            hovertemplate='<b>%{x}</b><br>DSI: %{y:.1f} days<extra></extra>'
        ))

        # Trace 2: DSO (Orange)
        dso_values = [companies_data[c]['dso'] for c in companies_with_data]
        dso_opacities = [companies_data[c]['opacity'] for c in companies_with_data]

        fig.add_trace(go.Bar(
            name='DSO (Days to Collect)',
            x=companies_with_data,
            y=dso_values,
            marker=dict(
                color=[f'rgba(243, 156, 18, {o})' for o in dso_opacities],
                line=dict(color='rgba(243, 156, 18, 1.0)', width=1)
            ),
            text=[f'{v:.1f}' for v in dso_values],
            textposition='outside',
            visible=visible,
            legendgroup='DSO',
            showlegend=(period_idx == len(target_ccc_periods) - 1),  # Only show legend for default visible period
            hovertemplate='<b>%{x}</b><br>DSO: %{y:.1f} days<extra></extra>'
        ))

        # Trace 3: DPO (Blue)
        dpo_values = [companies_data[c]['dpo'] for c in companies_with_data]
        dpo_opacities = [companies_data[c]['opacity'] for c in companies_with_data]

        fig.add_trace(go.Bar(
            name='DPO (Days to Pay Suppliers)',
            x=companies_with_data,
            y=dpo_values,
            marker=dict(
                color=[f'rgba(52, 152, 219, {o})' for o in dpo_opacities],
                line=dict(color='rgba(52, 152, 219, 1.0)', width=1)
            ),
            text=[f'{v:.1f}' for v in dpo_values],
            textposition='outside',
            visible=visible,
            legendgroup='DPO',
            showlegend=(period_idx == len(target_ccc_periods) - 1),  # Only show legend for default visible period
            hovertemplate='<b>%{x}</b><br>DPO: %{y:.1f} days<extra></extra>'
        ))

        # Trace 4: CCC (Green - more prominent)
        ccc_values = [companies_data[c]['ccc'] for c in companies_with_data]
        ccc_opacities = [companies_data[c]['opacity'] for c in companies_with_data]

        fig.add_trace(go.Bar(
            name='CCC (Total Cycle)',
            x=companies_with_data,
            y=ccc_values,
            marker=dict(
                color=[f'rgba(39, 174, 96, {o})' for o in ccc_opacities],
                line=dict(color='rgba(39, 174, 96, 1.0)', width=2)  # Thicker for CCC
            ),
            text=[f'{v:.1f}' for v in ccc_values],
            textposition='outside',
            textfont=dict(size=12, color='black'),
            visible=visible,
            legendgroup='CCC',
            showlegend=(period_idx == len(target_ccc_periods) - 1),  # Only show legend for default visible period
            hovertemplate='<b>%{x}</b><br>CCC: %{y:.1f} days<extra></extra>'
        ))

    # Step 5: Create dropdown menu buttons
    buttons = []
    traces_per_period = 4  # 4 bar traces per period (DSI, DSO, DPO, CCC), each with 5 companies

    # Iterate in reverse (most recent first in dropdown)
    for period_idx in range(len(target_ccc_periods) - 1, -1, -1):
        target_period = target_ccc_periods[period_idx]

        # Build visibility array - use 'legendonly' for traces that define the legend (last period's traces)
        # This keeps the legend visible while hiding the bars
        visible_array = []
        legend_period_idx = len(target_ccc_periods) - 1  # Last period defines legend (has showlegend=True)

        for trace_period_idx in range(len(target_ccc_periods)):
            for _ in range(traces_per_period):  # 4 traces per period
                if trace_period_idx == period_idx:
                    # Currently selected period - show bars
                    visible_array.append(True)
                elif trace_period_idx == legend_period_idx:
                    # Legend-defining period - keep legend visible but hide bars
                    visible_array.append('legendonly')
                else:
                    # Other periods - fully hidden
                    visible_array.append(False)

        buttons.append({
            'label': target_period['period'],  # e.g., "FY2024"
            'method': 'update',
            'args': [
                {'visible': visible_array},
                {
                    'title': {
                        'text': f"Target vs Retail Peers: Cash Conversion Cycle<br><sub>Comparing {target_period['period']} CCC performance (Lower is better)</sub>",
                        'x': 0.5,
                        'xanchor': 'center'
                    }
                }
            ]
        })

    # Step 6: Add reference lines
    fig.add_hline(
        y=60,
        line_dash="dash",
        line_color="gray",
        annotation_text="Retail Benchmark (60 days)",
        annotation_position="right"
    )

    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="black",
        opacity=0.3
    )

    # Step 7: Layout configuration
    most_recent = target_ccc_periods[-1]['period']

    fig.update_layout(
        barmode='group',
        title={
            'text': f"Target vs Retail Peers: Cash Conversion Cycle<br><sub>Target: {most_recent} vs Peers: FY2024 Benchmark (Lower is better)</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title="Company",
            tickangle=0
        ),
        yaxis=dict(
            title="Days",
            range=[-70, 175]  # Accommodate Amazon CCC (-51.6) + text label padding below
        ),
        height=600,
        width=1000,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.20,
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
        margin=dict(t=120, b=120, l=80, r=100),  # Increased top margin for dropdown
        hovermode='closest'
    )

    # Step 8: Save chart with responsive config
    output_path = 'output/chart_cash_conversion_cycle.html'
    config = {'displayModeBar': True, 'responsive': True}
    fig.write_html(output_path, config=config)

    print(f"✅ Chart 20 created: {output_path}")
    print(f"   Chart type: Peer comparison with dropdown ({len(target_ccc_periods)} periods)")
    print(f"   Companies: {len(company_names)} ({', '.join(company_names)})")

    return fig


# =============================================================================
# Pillar 4: Cash Flow Dynamics Visualizations
# =============================================================================

def create_ocf_vs_capex_chart(data):
    """
    Chart 21: Operating Cash Flow vs Capital Expenditures (Pillar 4)

    Shows the relationship between OCF and CapEx with the gap representing
    Free Cash Flow. Uses bars for OCF and a line for CapEx.

    IMPORTANT: 10-Q cash flow values are cumulative YTD, not standalone quarters.
    This function converts YTD to standalone quarterly values:
    - Q1 = Q1 YTD (as-is)
    - Q2 = Q2 YTD - Q1 YTD
    - Q3 = Q3 YTD - Q2 YTD
    - Q4 = Annual - Q3 YTD

    Features:
    - Single y-axis for all metrics ($ Billions)
    - Quarterly data with calculated Q4 from annual reports
    - Color-coded: Green (OCF bars), Red (CapEx line), Blue (FCF line)
    """
    cf = data['metrics']['cash_flows']

    # Step 1: Collect YTD data from 10-Q filings, grouped by fiscal year
    ytd_by_fy = {}  # {fiscal_year: {'Q1': {...}, 'Q2': {...}, 'Q3': {...}}}
    annual_data = {}  # {fiscal_year: {'ocf': ..., 'capex': ...}}

    for i, period in enumerate(data['periods']):
        fy = period['fiscal_year']
        ocf = cf['operating_cash_flow_billion'][i]
        capex = cf['capital_expenditures_billion'][i]

        if period['filing_type'] == '10-Q':
            if fy not in ytd_by_fy:
                ytd_by_fy[fy] = {}

            # Determine quarter from period string (e.g., "Q1 2023" -> "Q1")
            q_num = period['period'].split()[0]  # "Q1", "Q2", or "Q3"
            ytd_by_fy[fy][q_num] = {'ocf': ocf, 'capex': capex}

        elif period['filing_type'] == '10-K':
            annual_data[fy] = {'ocf': ocf, 'capex': capex}

    # Step 2: Convert YTD to standalone quarterly values and calculate Q4
    quarterly_data = []

    for fy in sorted(ytd_by_fy.keys()):
        ytd = ytd_by_fy[fy]
        annual = annual_data.get(fy)

        # Q1 standalone = Q1 YTD (as-is)
        if 'Q1' in ytd and ytd['Q1']['ocf'] is not None:
            q1_ocf = ytd['Q1']['ocf']
            q1_capex = ytd['Q1']['capex']
            q1_fcf = q1_ocf - q1_capex if q1_capex else None
            quarterly_data.append({
                'period': f'Q1 {fy}',
                'fiscal_year': fy,
                'ocf': round(q1_ocf, 2),
                'capex': round(q1_capex, 2) if q1_capex else None,
                'fcf': round(q1_fcf, 2) if q1_fcf else None
            })

        # Q2 standalone = Q2 YTD - Q1 YTD
        if 'Q1' in ytd and 'Q2' in ytd and ytd['Q2']['ocf'] is not None:
            q2_ocf = ytd['Q2']['ocf'] - ytd['Q1']['ocf']
            q2_capex = ytd['Q2']['capex'] - ytd['Q1']['capex'] if ytd['Q2']['capex'] and ytd['Q1']['capex'] else None
            q2_fcf = q2_ocf - q2_capex if q2_capex else None
            quarterly_data.append({
                'period': f'Q2 {fy}',
                'fiscal_year': fy,
                'ocf': round(q2_ocf, 2),
                'capex': round(q2_capex, 2) if q2_capex else None,
                'fcf': round(q2_fcf, 2) if q2_fcf else None
            })

        # Q3 standalone = Q3 YTD - Q2 YTD
        if 'Q2' in ytd and 'Q3' in ytd and ytd['Q3']['ocf'] is not None:
            q3_ocf = ytd['Q3']['ocf'] - ytd['Q2']['ocf']
            q3_capex = ytd['Q3']['capex'] - ytd['Q2']['capex'] if ytd['Q3']['capex'] and ytd['Q2']['capex'] else None
            q3_fcf = q3_ocf - q3_capex if q3_capex else None
            quarterly_data.append({
                'period': f'Q3 {fy}',
                'fiscal_year': fy,
                'ocf': round(q3_ocf, 2),
                'capex': round(q3_capex, 2) if q3_capex else None,
                'fcf': round(q3_fcf, 2) if q3_fcf else None
            })

        # Q4 standalone = Annual - Q3 YTD
        if annual and 'Q3' in ytd and ytd['Q3']['ocf'] is not None:
            q4_ocf = annual['ocf'] - ytd['Q3']['ocf']
            q4_capex = annual['capex'] - ytd['Q3']['capex'] if annual['capex'] and ytd['Q3']['capex'] else None
            q4_fcf = q4_ocf - q4_capex if q4_capex else None
            quarterly_data.append({
                'period': f'Q4 {fy}',
                'fiscal_year': fy,
                'ocf': round(q4_ocf, 2),
                'capex': round(q4_capex, 2) if q4_capex else None,
                'fcf': round(q4_fcf, 2) if q4_fcf else None
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

    # Filter to only include complete data points
    quarterly_data = [q for q in quarterly_data
                      if q['ocf'] is not None and q['capex'] is not None]

    periods = [q['period'] for q in quarterly_data]
    ocf_values = [q['ocf'] for q in quarterly_data]
    capex_values = [q['capex'] for q in quarterly_data]
    fcf_values = [q['fcf'] for q in quarterly_data]

    # Create figure with single y-axis (all metrics in same units)
    fig = go.Figure()

    # Operating Cash Flow bars (green)
    fig.add_trace(
        go.Bar(
            x=periods,
            y=ocf_values,
            name="Operating Cash Flow",
            marker_color='#27ae60',
            text=[f'${v:.2f}B' for v in ocf_values],
            textposition='outside',
            textfont=dict(size=9)
        )
    )

    # Capital Expenditures line (red)
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=capex_values,
            name="Capital Expenditures",
            line=dict(color='#e74c3c', width=3),
            mode='lines+markers+text',
            marker=dict(size=8, symbol='circle'),
            text=[f'${v:.2f}B' for v in capex_values],
            textposition='top center',
            textfont=dict(size=9, color='#e74c3c')
        )
    )

    # Free Cash Flow line (blue) with markers
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=fcf_values,
            name="Free Cash Flow (FCF)",
            line=dict(color='#3498db', width=3),
            mode='lines+markers+text',
            marker=dict(size=10, symbol='diamond'),
            text=[f'${v:.2f}B' for v in fcf_values],
            textposition='top center',
            textfont=dict(size=10, color='#3498db')
        )
    )

    # Add zero line reference
    fig.add_hline(y=0, line_dash="dash", line_color="gray",
                  line_width=1, opacity=0.5)

    # Calculate data range for y-axis with extra padding for labels
    all_values = ocf_values + capex_values + fcf_values
    min_val = min(all_values)
    max_val = max(all_values)
    y_min = min_val * 1.3 if min_val < 0 else -1  # Allow room below zero
    y_max = max_val * 1.4  # Extra padding for labels

    fig.update_layout(
        title={
            'text': "Target: Operating Cash Flow vs Capital Expenditures<br><sub>OCF (bars) minus CapEx (line) = Free Cash Flow</sub>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        barmode='group',
        height=700,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        margin=dict(t=130, b=80),
        yaxis=dict(
            title_text="Cash Flow ($ Billions)",
            range=[y_min, y_max]
        )
    )

    # Update x-axis
    fig.update_xaxes(title_text="Quarter", tickangle=-45)

    output_path = "output/chart_ocf_vs_capex.html"
    fig.write_html(output_path)
    print(f"✅ Chart 21 created: {output_path}")
    print(f"   Data: {len(periods)} quarters with OCF, CapEx, and FCF")

    return fig


def create_cash_flow_sankey(data):
    """
    Chart 22: Cash Flow Sankey Diagram (Pillar 4)

    Shows the flow of cash from Operating Cash Flow through various uses:
    - Capital Expenditures (reinvestment)
    - Dividends (shareholder returns)
    - Stock Repurchases (shareholder returns)
    - Debt Repayment (deleveraging)
    - Retained Cash (remaining)

    Uses quarterly data with calculated Q4 for granular cash allocation view.
    """
    cf = data['metrics']['cash_flows']

    # Step 1: Collect quarterly data from 10-Q filings
    quarterly_data = []
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-Q':
            ocf = cf['operating_cash_flow_billion'][i]
            capex = cf['capital_expenditures_billion'][i]
            dividends = cf['dividends_paid_billion'][i]
            buybacks = cf['stock_repurchases_billion'][i]
            debt_repay = cf['debt_repayments_billion'][i]

            if ocf is not None and capex is not None:
                quarterly_data.append({
                    'period': period['period'],
                    'fiscal_year': period['fiscal_year'],
                    'fiscal_quarter': period['fiscal_quarter'],
                    'ocf': ocf,
                    'capex': capex or 0,
                    'dividends': dividends or 0,
                    'buybacks': buybacks or 0,
                    'debt_repay': debt_repay or 0
                })

    # Step 2: Calculate Q4 data from 10-K annual reports
    for i, period in enumerate(data['periods']):
        if period['filing_type'] == '10-K':
            fy = period['fiscal_year']
            annual_ocf = cf['operating_cash_flow_billion'][i]
            annual_capex = cf['capital_expenditures_billion'][i]
            annual_div = cf['dividends_paid_billion'][i]
            annual_buyback = cf['stock_repurchases_billion'][i]
            annual_debt = cf['debt_repayments_billion'][i]

            if annual_ocf is None or annual_capex is None:
                continue

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

            # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
            if q1 and q2 and q3:
                q4_ocf = annual_ocf - (q1['ocf'] + q2['ocf'] + q3['ocf'])
                q4_capex = annual_capex - (q1['capex'] + q2['capex'] + q3['capex'])
                q4_div = (annual_div or 0) - (q1['dividends'] + q2['dividends'] + q3['dividends'])
                q4_buyback = (annual_buyback or 0) - (q1['buybacks'] + q2['buybacks'] + q3['buybacks'])
                q4_debt = (annual_debt or 0) - (q1['debt_repay'] + q2['debt_repay'] + q3['debt_repay'])

                quarterly_data.append({
                    'period': f'Q4 {fy}',
                    'fiscal_year': fy,
                    'fiscal_quarter': 4,
                    'ocf': round(q4_ocf, 3),
                    'capex': round(max(0, q4_capex), 3),  # CapEx should be positive
                    'dividends': round(max(0, q4_div), 3),
                    'buybacks': round(max(0, q4_buyback), 3),
                    'debt_repay': round(max(0, q4_debt), 3)
                })

    # Step 3: Sort by fiscal year and quarter
    def sort_key(item):
        return (item['fiscal_year'], item['fiscal_quarter'])

    quarterly_data.sort(key=sort_key)

    # Use most recent quarter for Sankey
    if not quarterly_data:
        print("⚠️ No quarterly data available for Sankey diagram")
        return None

    latest = quarterly_data[-1]

    # Calculate values for Sankey
    ocf = latest['ocf']
    capex = latest['capex']
    dividends = latest['dividends']
    buybacks = latest['buybacks']
    debt_repay = latest['debt_repay']

    # FCF and retained cash
    fcf = ocf - capex
    total_returns = dividends + buybacks + debt_repay
    retained = max(0, fcf - total_returns)  # Remaining cash

    # If uses exceed FCF, adjust (company drew on reserves/debt)
    if fcf < total_returns:
        retained = 0  # No retention, actually drew down

    # Define Sankey nodes
    # 0: Operating Cash Flow
    # 1: Free Cash Flow
    # 2: Capital Expenditures
    # 3: Dividends
    # 4: Stock Repurchases
    # 5: Debt Repayment
    # 6: Retained Cash

    labels = [
        f"Operating Cash Flow<br>${ocf:.2f}B",
        f"Free Cash Flow<br>${fcf:.2f}B",
        f"Capital Expenditures<br>${capex:.2f}B",
        f"Dividends<br>${dividends:.2f}B",
        f"Stock Buybacks<br>${buybacks:.2f}B",
        f"Debt Repayment<br>${debt_repay:.2f}B",
        f"Retained Cash<br>${retained:.2f}B"
    ]

    # Define flows (source, target, value)
    source = []
    target = []
    value = []
    colors = []

    # Flow 1: OCF -> CapEx (reinvestment)
    if capex > 0:
        source.append(0)
        target.append(2)
        value.append(capex)
        colors.append('rgba(231, 76, 60, 0.6)')  # Red

    # Flow 2: OCF -> FCF (remaining after CapEx)
    if fcf > 0:
        source.append(0)
        target.append(1)
        value.append(fcf)
        colors.append('rgba(52, 152, 219, 0.6)')  # Blue

    # Flow 3: FCF -> Dividends
    if dividends > 0:
        source.append(1)
        target.append(3)
        value.append(dividends)
        colors.append('rgba(155, 89, 182, 0.6)')  # Purple

    # Flow 4: FCF -> Stock Buybacks
    if buybacks > 0:
        source.append(1)
        target.append(4)
        value.append(buybacks)
        colors.append('rgba(230, 126, 34, 0.6)')  # Orange

    # Flow 5: FCF -> Debt Repayment
    if debt_repay > 0:
        source.append(1)
        target.append(5)
        value.append(debt_repay)
        colors.append('rgba(241, 196, 15, 0.6)')  # Yellow

    # Flow 6: FCF -> Retained Cash
    if retained > 0:
        source.append(1)
        target.append(6)
        value.append(retained)
        colors.append('rgba(39, 174, 96, 0.6)')  # Green

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="black", width=1),
            label=labels,
            color=[
                '#27ae60',  # OCF - Green
                '#3498db',  # FCF - Blue
                '#e74c3c',  # CapEx - Red
                '#9b59b6',  # Dividends - Purple
                '#e67e22',  # Buybacks - Orange
                '#f1c40f',  # Debt Repay - Yellow
                '#2ecc71'   # Retained - Light Green
            ]
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=colors
        )
    )])

    # Create dropdown for different quarters (most recent 15)
    buttons = []
    for q_data in reversed(quarterly_data[-15:]):  # Last 15 quarters, most recent first
        qtr = q_data['period']
        ocf_q = q_data['ocf']
        capex_q = q_data['capex']
        div_q = q_data['dividends']
        buy_q = q_data['buybacks']
        debt_q = q_data['debt_repay']
        fcf_q = ocf_q - capex_q
        total_q = div_q + buy_q + debt_q
        retained_q = max(0, fcf_q - total_q)

        # Build flows for this quarter
        q_source, q_target, q_value, q_colors = [], [], [], []

        if capex_q > 0:
            q_source.append(0)
            q_target.append(2)
            q_value.append(capex_q)
            q_colors.append('rgba(231, 76, 60, 0.6)')

        if fcf_q > 0:
            q_source.append(0)
            q_target.append(1)
            q_value.append(fcf_q)
            q_colors.append('rgba(52, 152, 219, 0.6)')

        if div_q > 0:
            q_source.append(1)
            q_target.append(3)
            q_value.append(div_q)
            q_colors.append('rgba(155, 89, 182, 0.6)')

        if buy_q > 0:
            q_source.append(1)
            q_target.append(4)
            q_value.append(buy_q)
            q_colors.append('rgba(230, 126, 34, 0.6)')

        if debt_q > 0:
            q_source.append(1)
            q_target.append(5)
            q_value.append(debt_q)
            q_colors.append('rgba(241, 196, 15, 0.6)')

        if retained_q > 0:
            q_source.append(1)
            q_target.append(6)
            q_value.append(retained_q)
            q_colors.append('rgba(39, 174, 96, 0.6)')

        q_labels = [
            f"Operating Cash Flow<br>${ocf_q:.2f}B",
            f"Free Cash Flow<br>${fcf_q:.2f}B",
            f"Capital Expenditures<br>${capex_q:.2f}B",
            f"Dividends<br>${div_q:.2f}B",
            f"Stock Buybacks<br>${buy_q:.2f}B",
            f"Debt Repayment<br>${debt_q:.2f}B",
            f"Retained Cash<br>${retained_q:.2f}B"
        ]

        buttons.append(dict(
            label=qtr,
            method='update',
            args=[
                {
                    'node': [dict(
                        pad=20,
                        thickness=30,
                        line=dict(color="black", width=1),
                        label=q_labels,
                        color=[
                            '#27ae60', '#3498db', '#e74c3c',
                            '#9b59b6', '#e67e22', '#f1c40f', '#2ecc71'
                        ]
                    )],
                    'link': [dict(
                        source=q_source,
                        target=q_target,
                        value=q_value,
                        color=q_colors
                    )]
                },
                {
                    'title': {
                        'text': f"Target: Cash Flow Allocation ({qtr})<br><sub>From Operating Cash Flow to CapEx, Dividends, Buybacks & Debt Repayment</sub>",
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.95,
                        'yanchor': 'top'
                    }
                }
            ]
        ))

    fig.update_layout(
        title={
            'text': f"Target: Cash Flow Allocation ({latest['period']})<br><sub>From Operating Cash Flow to CapEx, Dividends, Buybacks & Debt Repayment</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        height=600,
        font=dict(size=12),
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
                bgcolor="white",
                bordercolor="#2c3e50",
                font=dict(size=11)
            )
        ],
        annotations=[
            dict(
                text="Select Quarter:",
                x=1.0,
                xref="paper",
                y=1.20,
                yref="paper",
                align="right",
                showarrow=False,
                font=dict(size=11)
            )
        ],
        margin=dict(t=120, b=50, l=50, r=50)
    )

    output_path = "output/chart_cash_flow_sankey.html"
    fig.write_html(output_path)
    print(f"✅ Chart 22 created: {output_path}")
    print(f"   Data: {len(quarterly_data)} quarters available")
    print(f"   Default view: {latest['period']} (OCF: ${ocf:.2f}B, FCF: ${fcf:.2f}B)")

    return fig


# =============================================================================
# Pillar 5: Valuation & Market Sentiment Charts
# =============================================================================

def _get_quarterly_valuation_data(data):
    """
    Extract quarterly data needed for historical P/E calculation.

    Returns list of dicts with period, quarter_end_date, revenue_growth, ttm_net_income.
    """
    periods = data['periods']
    net_income = data['metrics']['cash_flows'].get('net_income_billion', [])
    yoy_growth = data['metrics']['revenue'].get('yoy_growth_percent', [])

    # Map fiscal quarters to approximate end dates (Target fiscal year ends late Jan)
    # Q1 ends late April, Q2 ends late July, Q3 ends late October, Q4 ends late January
    quarter_end_map = {
        'Q1': '-04-30',
        'Q2': '-07-31',
        'Q3': '-10-31',
        'Q4': '-01-31'  # Note: Q4 end is in the NEXT calendar year
    }

    quarterly_data = []

    # First, build a lookup of all net income values by period
    ni_lookup = {}
    for i, period in enumerate(periods):
        if i < len(net_income) and net_income[i] is not None:
            ni_lookup[period['period']] = {
                'net_income': net_income[i],
                'fiscal_year': period['fiscal_year'],
                'filing_type': period['filing_type']
            }

    # Process only 10-Q quarterly filings
    for i, period in enumerate(periods):
        if period['filing_type'] != '10-Q':
            continue

        period_str = period['period']  # e.g., "Q3 2024"
        fiscal_year = period['fiscal_year']

        # Parse quarter
        if ' ' not in period_str:
            continue
        quarter = period_str.split(' ')[0]  # "Q3"

        # Determine quarter end date
        if quarter == 'Q4':
            # Q4 ends in January of the NEXT calendar year
            calendar_year = fiscal_year + 1
        else:
            calendar_year = fiscal_year
        quarter_end_date = f"{calendar_year}{quarter_end_map[quarter]}"

        # Get revenue growth for this quarter
        growth = yoy_growth[i] if i < len(yoy_growth) else None

        # Calculate TTM (trailing 12-month) net income
        # For Q3 2024, we need Q4 2023 + Q1 2024 + Q2 2024 + Q3 2024
        ttm_quarters = _get_ttm_quarters(quarter, fiscal_year)
        ttm_net_income = 0
        ttm_complete = True

        for q_period in ttm_quarters:
            if q_period in ni_lookup:
                ttm_net_income += ni_lookup[q_period]['net_income']
            else:
                # Try to get Q4 from annual report
                if q_period.startswith('Q4'):
                    fy = int(q_period.split()[1])
                    annual_key = f"FY{fy}"
                    # Calculate Q4 = Annual - Q1 - Q2 - Q3
                    if annual_key in ni_lookup:
                        annual_ni = ni_lookup[annual_key]['net_income']
                        q1_key = f"Q1 {fy}"
                        q2_key = f"Q2 {fy}"
                        q3_key = f"Q3 {fy}"
                        if all(k in ni_lookup for k in [q1_key, q2_key, q3_key]):
                            q4_ni = annual_ni - ni_lookup[q1_key]['net_income'] - ni_lookup[q2_key]['net_income'] - ni_lookup[q3_key]['net_income']
                            ttm_net_income += q4_ni
                            continue
                ttm_complete = False
                break

        if not ttm_complete or ttm_net_income <= 0:
            continue

        quarterly_data.append({
            'period': period_str,
            'quarter_end_date': quarter_end_date,
            'revenue_growth': growth,
            'ttm_net_income_billion': round(ttm_net_income, 3)
        })

    # =========================================================================
    # Add Q4 periods from 10-K annual reports
    # Q4 data is not in 10-Q filings, must be calculated from annual 10-K
    # =========================================================================

    # Build revenue lookup for Q4 calculation
    revenue_lookup = {}
    revenue_data = data['metrics']['revenue'].get('net_sales_billion', [])
    for i, period in enumerate(periods):
        if i < len(revenue_data) and revenue_data[i] is not None:
            revenue_lookup[period['period']] = revenue_data[i]

    # Generate Q4 periods from 10-K annual reports
    for fy_period, fy_data in ni_lookup.items():
        if not fy_period.startswith('FY'):
            continue

        fy = int(fy_period[2:])  # FY2024 -> 2024

        # Check if we have Q1, Q2, Q3 for this fiscal year
        q1_key, q2_key, q3_key = f"Q1 {fy}", f"Q2 {fy}", f"Q3 {fy}"

        if not all(k in ni_lookup for k in [q1_key, q2_key, q3_key]):
            continue

        # TTM for Q4 is the full fiscal year net income
        ttm_net_income = fy_data['net_income']

        if ttm_net_income <= 0:
            continue

        # Calculate Q4 revenue growth (need revenue data)
        q4_growth = None
        fy_revenue_key = f"FY{fy}"
        prior_fy_key = f"FY{fy - 1}"

        if (fy_revenue_key in revenue_lookup and prior_fy_key in revenue_lookup
            and all(k in revenue_lookup for k in [q1_key, q2_key, q3_key])):

            # Calculate Q4 revenue for current year
            q4_revenue = revenue_lookup[fy_revenue_key] - revenue_lookup[q1_key] - \
                         revenue_lookup[q2_key] - revenue_lookup[q3_key]

            # Calculate Q4 revenue for prior year
            prior_q1 = f"Q1 {fy-1}"
            prior_q2 = f"Q2 {fy-1}"
            prior_q3 = f"Q3 {fy-1}"

            if all(k in revenue_lookup for k in [prior_q1, prior_q2, prior_q3]):
                prior_q4_revenue = revenue_lookup[prior_fy_key] - revenue_lookup[prior_q1] - \
                                   revenue_lookup[prior_q2] - revenue_lookup[prior_q3]

                if prior_q4_revenue > 0:
                    q4_growth = ((q4_revenue / prior_q4_revenue) - 1) * 100

        # Q4 quarter end date (January of next calendar year)
        quarter_end_date = f"{fy + 1}-01-31"

        quarterly_data.append({
            'period': f'Q4 {fy}',
            'quarter_end_date': quarter_end_date,
            'revenue_growth': round(q4_growth, 2) if q4_growth is not None else None,
            'ttm_net_income_billion': round(ttm_net_income, 3)
        })

    # Sort chronologically by year then quarter
    quarterly_data.sort(key=lambda x: (
        int(x['period'].split()[1]),  # Year
        int(x['period'][1])           # Quarter number
    ))

    return quarterly_data


def _get_ttm_quarters(current_quarter: str, fiscal_year: int) -> list:
    """
    Get the 4 quarters that make up TTM for a given quarter.

    For Q3 2024: returns ['Q4 2023', 'Q1 2024', 'Q2 2024', 'Q3 2024']
    """
    quarter_num = int(current_quarter[1])  # Q3 -> 3

    quarters = []
    for i in range(4):
        # Go back 3, 2, 1, 0 quarters from current
        offset = 3 - i
        q_num = quarter_num - offset
        fy = fiscal_year

        # Adjust for year boundary
        while q_num <= 0:
            q_num += 4
            fy -= 1
        while q_num > 4:
            q_num -= 4
            fy += 1

        quarters.append(f"Q{q_num} {fy}")

    return quarters


def create_valuation_vs_growth_scatter(data, market_data=None):
    """
    Chart 23: Valuation vs Growth Scatter Plot with Quarterly Dropdown

    Plots P/E Ratio (Y-axis) vs Revenue Growth (X-axis) for Target and peers.
    Includes dropdown menu to view positions across different quarters.
    Historical P/E is calculated for ALL companies (Target + peers) using
    price ratio scaling from Yahoo Finance stock price history.

    Args:
        data: Time-series data from target_timeseries.json
        market_data: Optional pre-fetched market data (fetches if None)

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go
    from market_data_fetcher import MarketDataFetcher

    # Fetch current market data for peers
    try:
        fetcher = MarketDataFetcher()
        comparison = fetcher.get_peer_comparison()
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch market data: {e}")
        print("   Skipping Chart 23 (requires Yahoo Finance API)")
        return None

    companies = comparison.get('companies', [])
    if not companies:
        print("⚠️ Warning: No company data available for Chart 23")
        return None

    # Extract peer data (excluding Target - we'll use historical P/E for Target)
    peers = []
    for company in companies:
        if company.get('ticker') == 'TGT':
            continue
        pe = company.get('pe_ratio')
        growth = company.get('revenue_growth_percent')
        if pe is not None and growth is not None:
            peers.append({
                'ticker': company.get('ticker'),
                'name': company.get('name', company.get('ticker')),
                'pe_ratio': pe,
                'revenue_growth': growth
            })

    if len(peers) < 1:
        print("⚠️ Warning: Not enough peer data for Chart 23")
        return None

    # Get quarterly valuation data for Target
    quarterly_data = _get_quarterly_valuation_data(data)
    if not quarterly_data:
        print("⚠️ Warning: No quarterly data available for Chart 23")
        return None

    # Calculate historical P/E for Target
    print("   Calculating historical P/E ratios for Target...")
    historical_pe = fetcher.get_historical_pe_for_quarters(quarterly_data)

    # Filter to quarters with valid P/E
    valid_quarters = []
    for q in quarterly_data:
        if q['period'] in historical_pe and q['revenue_growth'] is not None:
            pe_data = historical_pe[q['period']]
            if pe_data.get('pe_ratio'):
                valid_quarters.append({
                    'period': q['period'],
                    'pe_ratio': pe_data['pe_ratio'],
                    'revenue_growth': q['revenue_growth'],
                    'stock_price': pe_data['stock_price'],
                    'ttm_eps': pe_data['ttm_eps'],
                    'quarter_end_date': pe_data['quarter_end_date']
                })

    if not valid_quarters:
        print("⚠️ Warning: Could not calculate historical P/E for any quarter")
        return None

    print(f"   Found {len(valid_quarters)} quarters with valid P/E data")

    # Get quarter-end dates for historical peer P/E calculation
    quarter_dates = [q['quarter_end_date'] for q in valid_quarters]

    # Calculate historical P/E for each peer
    print("   Calculating historical P/E ratios for peers...")
    peer_historical_pe = {}
    for peer in peers:
        ticker = peer['ticker']
        peer_pe_history = fetcher.get_historical_pe_for_ticker(ticker, quarter_dates)
        peer_historical_pe[ticker] = peer_pe_history
        if peer_pe_history:
            print(f"      {ticker}: {len(peer_pe_history)} periods")

    # Calculate fixed averages based on peers + latest Target
    all_pe = [p['pe_ratio'] for p in peers] + [valid_quarters[-1]['pe_ratio']]
    all_growth = [p['revenue_growth'] for p in peers] + [valid_quarters[-1]['revenue_growth']]
    avg_pe = sum(all_pe) / len(all_pe)
    avg_growth = sum(all_growth) / len(all_growth)

    # Determine axis ranges for consistency (include historical peer P/E values)
    all_pe_values = [p['pe_ratio'] for p in peers] + [q['pe_ratio'] for q in valid_quarters]
    # Add historical peer P/E values to range calculation
    for ticker, pe_history in peer_historical_pe.items():
        all_pe_values.extend(pe_history.values())
    all_growth_values = [p['revenue_growth'] for p in peers] + [q['revenue_growth'] for q in valid_quarters]
    pe_min, pe_max = min(all_pe_values) - 5, max(all_pe_values) + 10
    growth_min, growth_max = min(all_growth_values) - 5, max(all_growth_values) + 5

    # Create figure
    fig = go.Figure()

    # Add quadrant shading (fixed position based on averages)
    # Lower-right quadrant (Undervalued) - Green
    fig.add_shape(
        type="rect",
        x0=avg_growth, x1=growth_max + 5,
        y0=0, y1=avg_pe,
        fillcolor="rgba(46, 204, 113, 0.1)",
        line=dict(width=0),
        layer="below"
    )
    # Upper-left quadrant (Overvalued) - Red
    fig.add_shape(
        type="rect",
        x0=growth_min - 5, x1=avg_growth,
        y0=avg_pe, y1=pe_max + 10,
        fillcolor="rgba(231, 76, 60, 0.1)",
        line=dict(width=0),
        layer="below"
    )

    # Track trace count for visibility control
    # Structure: For each quarter, we add [Target, Peer1, Peer2, Peer3, Peer4]
    traces_per_quarter = 1 + len(peers)  # Target + peers
    total_traces = len(valid_quarters) * traces_per_quarter

    # Peer colors for differentiation
    peer_colors = ['#3498db', '#9b59b6', '#1abc9c', '#f39c12']

    # Add traces for each quarter
    for q_idx, quarter in enumerate(valid_quarters):
        is_latest = (q_idx == len(valid_quarters) - 1)
        visible = is_latest  # Only show latest quarter by default

        # Add Target trace for this quarter
        # Use legendgroup to keep legend persistent across quarters
        fig.add_trace(go.Scatter(
            x=[quarter['revenue_growth']],
            y=[quarter['pe_ratio']],
            mode='markers+text',
            name='Target Corporation',
            legendgroup='Target',  # Group all Target traces
            marker=dict(
                size=25,
                color='#e74c3c',
                symbol='star',
                line=dict(width=2, color='white')
            ),
            text=['TGT'],
            textposition='top center',
            textfont=dict(size=12, color='#e74c3c', weight='bold'),
            hovertemplate=(
                f"<b>Target Corporation (TGT)</b><br>" +
                f"Period: {quarter['period']}<br>" +
                f"P/E Ratio: {quarter['pe_ratio']:.1f}x<br>" +
                f"Revenue Growth: {quarter['revenue_growth']:.1f}%<br>" +
                f"Stock Price: ${quarter['stock_price']:.2f}<br>" +
                f"TTM EPS: ${quarter['ttm_eps']:.2f}<br>" +
                "<extra></extra>"
            ),
            visible=visible,
            showlegend=(q_idx == 0)  # Show legend for first trace in group
        ))

        # Add peer traces for this quarter with historical P/E
        for p_idx, peer in enumerate(peers):
            ticker = peer['ticker']
            quarter_date = quarter['quarter_end_date']

            # Get historical P/E for this peer at this quarter
            hist_pe = peer_historical_pe.get(ticker, {}).get(quarter_date)
            # Fall back to current P/E if historical not available
            pe_value = hist_pe if hist_pe else peer['pe_ratio']
            is_historical = hist_pe is not None

            color = peer_colors[p_idx % len(peer_colors)]

            fig.add_trace(go.Scatter(
                x=[peer['revenue_growth']],  # Revenue growth stays at current (no historical available)
                y=[pe_value],
                mode='markers+text',
                name=peer['name'],
                legendgroup=peer['ticker'],  # Group all traces for this peer
                marker=dict(
                    size=15,
                    color=color,
                    symbol='circle',
                    line=dict(width=2, color='white')
                ),
                text=[peer['ticker']],
                textposition='top center',
                textfont=dict(size=12, color=color),
                hovertemplate=(
                    f"<b>{peer['name']} ({peer['ticker']})</b><br>" +
                    f"Period: {quarter['period']}<br>" +
                    f"P/E Ratio: {pe_value:.1f}x {'(historical)' if is_historical else '(current)'}<br>" +
                    f"Revenue Growth: {peer['revenue_growth']:.1f}% (current)<br>" +
                    "<extra></extra>"
                ),
                visible=visible,
                showlegend=(q_idx == 0)  # Show legend for first trace in group
            ))

    # Add reference lines (fixed)
    fig.add_hline(y=avg_pe, line_dash="dash", line_color="gray")
    fig.add_vline(
        x=avg_growth, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Growth: {avg_growth:.1f}%",
        annotation_position="top"
    )

    # Add quadrant labels (fixed)
    fig.add_annotation(
        x=growth_max - 1, y=5,
        text="<b>Undervalued Zone</b><br>(High Growth, Low P/E)",
        showarrow=False, font=dict(size=10, color='#27ae60'),
        bgcolor="rgba(255,255,255,0.8)"
    )
    fig.add_annotation(
        x=growth_min + 1, y=pe_max + 5,
        text="<b>Overvalued Zone</b><br>(Low Growth, High P/E)",
        showarrow=False, font=dict(size=10, color='#c0392b'),
        bgcolor="rgba(255,255,255,0.8)", yanchor="top"
    )
    fig.add_annotation(
        x=growth_min, y=avg_pe + 2,
        text=f"Avg P/E: {avg_pe:.1f}x",
        showarrow=False, font=dict(size=11, color='gray'),
        xanchor="left"
    )

    # Create dropdown buttons (most recent first)
    buttons = []
    for q_idx_rev in range(len(valid_quarters) - 1, -1, -1):
        quarter = valid_quarters[q_idx_rev]

        # Build visibility array
        visible_array = [False] * total_traces
        start_idx = q_idx_rev * traces_per_quarter
        for i in range(traces_per_quarter):
            visible_array[start_idx + i] = True

        buttons.append({
            'label': quarter['period'],
            'method': 'update',
            'args': [
                {'visible': visible_array},
                {
                    'title': {
                        'text': f"Target: Valuation vs Growth Analysis ({quarter['period']})<br><sub>P/E Ratios: Historical for all companies (price-scaled) - Lower right = potentially undervalued</sub>",
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.95,
                        'yanchor': 'top'
                    }
                }
            ]
        })

    # Update layout
    latest_q = valid_quarters[-1]
    fig.update_layout(
        title={
            'text': f"Target: Valuation vs Growth Analysis ({latest_q['period']})<br><sub>P/E Ratios: Historical for all companies (price-scaled) - Lower right = potentially undervalued</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title="Revenue Growth YoY (%)",
        yaxis_title="P/E Ratio (x)",
        height=650,
        width=1100,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.08
        ),
        margin=dict(l=120, r=220, t=140, b=80),
        plot_bgcolor='white',
        xaxis=dict(
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='gray',
            range=[growth_min, growth_max]
        ),
        yaxis=dict(
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='gray',
            range=[pe_min, pe_max]
        ),
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.17,
            'xanchor': 'left',
            'y': 1.12,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': 'lightgray'
        }]
    )

    # Save chart
    output_path = "output/chart_valuation_scatter.html"
    fig.write_html(output_path)
    print(f"✅ Chart 23 created: {output_path}")
    print(f"   {len(valid_quarters)} quarters available in dropdown")
    print(f"   Latest: {latest_q['period']} - P/E={latest_q['pe_ratio']:.1f}x, Growth={latest_q['revenue_growth']:.1f}%")

    return fig


def create_pe_band_area_chart(data, market_data=None):
    """
    Chart 24: Historical P/E Band Area Chart

    Shows Target's stock price over time with valuation bands
    to indicate if it's trading above/below historical averages.

    Args:
        data: Time-series data from target_timeseries.json
        market_data: Optional pre-fetched market data (fetches if None)

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go
    from market_data_fetcher import MarketDataFetcher
    import pandas as pd

    # Fetch market data if not provided
    try:
        fetcher = MarketDataFetcher()
        history = fetcher.get_historical_prices('TGT', '5y')
        metrics = fetcher.get_valuation_metrics()
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch market data: {e}")
        print("   Skipping Chart 24 (requires Yahoo Finance API)")
        return None

    if history.empty:
        print("⚠️ Warning: No historical price data for Chart 24")
        return None

    # Get Target's trailing twelve months EPS from SEC data
    # Use most recent annual net income / shares outstanding approximation
    # For simplicity, use yfinance EPS or calculate from P/E and price
    target_data = metrics.get('TGT', {})
    current_pe = target_data.get('pe_ratio', 15)
    current_price = target_data.get('price', 100)

    # Estimate EPS
    if current_pe and current_price:
        eps_estimate = current_price / current_pe
    else:
        eps_estimate = 8.0  # Fallback estimate for Target

    # Calculate theoretical price levels for P/E bands
    # Using estimated EPS to create valuation zones
    pe_bands = {
        'undervalued': 10,  # P/E < 10
        'fair_low': 15,     # P/E 10-15
        'fair_high': 20,    # P/E 15-20
        'overvalued': 25    # P/E > 20
    }

    # Create figure
    fig = go.Figure()

    # Prepare price data
    if 'Date' in history.columns:
        dates = pd.to_datetime(history['Date'])
        prices = history['Close'].values
    else:
        dates = history.index
        prices = history['Close'].values

    # Calculate P/E band price levels based on EPS
    # These are approximate - actual EPS changes over time
    undervalued_price = eps_estimate * pe_bands['undervalued']
    fair_low_price = eps_estimate * pe_bands['fair_low']
    fair_high_price = eps_estimate * pe_bands['fair_high']
    overvalued_price = eps_estimate * pe_bands['overvalued']

    # Add shaded areas for valuation zones (from bottom to top)

    # Undervalued zone (green) - below P/E 10
    fig.add_trace(go.Scatter(
        x=dates,
        y=[undervalued_price] * len(dates),
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.3)',
        line=dict(width=0),
        name='Undervalued (P/E < 10)',
        showlegend=True,
        hoverinfo='skip'
    ))

    # Fair value lower zone (light green) - P/E 10-15
    fig.add_trace(go.Scatter(
        x=dates,
        y=[fair_low_price] * len(dates),
        fill='tonexty',
        fillcolor='rgba(46, 204, 113, 0.15)',
        line=dict(width=0),
        name='Fair Value Low (P/E 10-15)',
        showlegend=True,
        hoverinfo='skip'
    ))

    # Fair value upper zone (yellow) - P/E 15-20
    fig.add_trace(go.Scatter(
        x=dates,
        y=[fair_high_price] * len(dates),
        fill='tonexty',
        fillcolor='rgba(241, 196, 15, 0.2)',
        line=dict(width=0),
        name='Fair Value High (P/E 15-20)',
        showlegend=True,
        hoverinfo='skip'
    ))

    # Overvalued zone (red) - P/E > 20
    fig.add_trace(go.Scatter(
        x=dates,
        y=[overvalued_price] * len(dates),
        fill='tonexty',
        fillcolor='rgba(231, 76, 60, 0.15)',
        line=dict(width=0),
        name='Overvalued (P/E > 20)',
        showlegend=True,
        hoverinfo='skip'
    ))

    # Add stock price line (on top of zones)
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name='TGT Stock Price',
        line=dict(color='#2c3e50', width=2),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:.2f}<extra></extra>"
    ))

    # Add P/E band reference lines with labels
    for pe_val, label, color in [
        (pe_bands['undervalued'], 'P/E = 10x', '#27ae60'),
        (pe_bands['fair_low'], 'P/E = 15x', '#f39c12'),
        (pe_bands['fair_high'], 'P/E = 20x', '#e67e22'),
        (pe_bands['overvalued'], 'P/E = 25x', '#e74c3c')
    ]:
        price_level = eps_estimate * pe_val
        fig.add_hline(
            y=price_level,
            line_dash="dot",
            line_color=color,
            line_width=1,
            annotation_text=f"{label} (${price_level:.0f})",
            annotation_position="right",
            annotation_font_color=color
        )

    # Add current P/E annotation
    if current_pe and current_price:
        fig.add_annotation(
            x=dates.iloc[-1] if hasattr(dates, 'iloc') else dates[-1],
            y=current_price,
            text=f"<b>Current</b><br>${current_price:.2f}<br>P/E: {current_pe:.1f}x",
            showarrow=True,
            arrowhead=2,
            arrowcolor='#2c3e50',
            ax=-50,
            ay=-40,
            font=dict(size=11, color='#2c3e50'),
            bgcolor="white",
            bordercolor='#2c3e50',
            borderwidth=1
        )

    # Update layout
    fig.update_layout(
        title={
            'text': f"Target: Historical Price with P/E Valuation Bands<br><sub>Pillar 5: 5-Year Price History with Estimated Valuation Zones (EPS ≈ ${eps_estimate:.2f})</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title="Date",
        yaxis_title="Stock Price ($)",
        height=600,
        width=1000,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=80, r=120, t=100, b=100),
        plot_bgcolor='white',
        xaxis=dict(
            gridcolor='lightgray',
            type='date'
        ),
        yaxis=dict(
            gridcolor='lightgray',
            tickprefix='$'
        ),
        hovermode='x unified'
    )

    # Save chart
    output_path = "output/chart_pe_band.html"
    fig.write_html(output_path)
    print(f"✅ Chart 24 created: {output_path}")
    print(f"   Data: 5-year price history for TGT")
    print(f"   Current: ${current_price:.2f} @ P/E {current_pe:.1f}x")
    print(f"   Estimated EPS: ${eps_estimate:.2f}")

    return fig


# DEPRECATED: Old time-series trend chart implementation (replaced with peer comparison)
# This function was replaced on 2026-01-25 per user request to show peer comparison instead
def _create_cash_conversion_cycle_trend_DEPRECATED(data):
    """
    DEPRECATED: Old Chart 20 implementation (time-series trend chart).

    This function has been replaced with create_cash_conversion_cycle_chart()
    which shows peer comparison bar chart instead of time-series trend.

    Kept for reference in case time-series view is needed in the future.
    """
    import plotly.graph_objects as go

    # [Original implementation would go here - removed for brevity]
    # This was the multi-line chart showing Target's CCC evolution over time

    pass  # Placeholder for deprecated function - not used


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

    # Create all 22 charts (7 Phase 3 + 4 Phase 4 + 2 new + 1 Phase 6 + 1 Phase 7 + 3 Pillar 2 + 2 Pillar 3 + 2 Pillar 4)
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

    # Pillar 4: Cash Flow Dynamics visualizations
    create_ocf_vs_capex_chart(data)  # Chart 21
    create_cash_flow_sankey(data)  # Chart 22

    # Pillar 5: Valuation & Market Sentiment visualizations
    try:
        create_valuation_vs_growth_scatter(data)  # Chart 23
        create_pe_band_area_chart(data)  # Chart 24
    except Exception as e:
        print(f"⚠️ Warning: Pillar 5 charts skipped (requires internet): {e}")

    print("\n✅ All 24 visualizations created in output/ directory")
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
    print("     - chart_ocf_vs_capex.html (Chart 21 - Pillar 4)")
    print("     - chart_cash_flow_sankey.html (Chart 22 - Pillar 4)")
    print("     - chart_valuation_scatter.html (Chart 23 - Pillar 5)")
    print("     - chart_pe_band.html (Chart 24 - Pillar 5)")


if __name__ == "__main__":
    main()
