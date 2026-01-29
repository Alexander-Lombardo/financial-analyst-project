#!/usr/bin/env python3
"""
DuPont Analysis Validation Tool

Generates:
1. output/dupont_validation.md - Side-by-side validation document showing calculations
2. output/chart_dupont_annual_trend.html - 5-year line chart comparing DuPont components

Usage:
    python3 dupont_validation.py
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Target's fiscal year ends on the Saturday nearest January 31st
FISCAL_YEAR_END_DATES = {
    'FY2024': 'February 1, 2025',
    'FY2023': 'February 3, 2024',
    'FY2022': 'January 28, 2023',
    'FY2021': 'January 29, 2022',
    'FY2020': 'January 30, 2021',
    'FY2019': 'February 1, 2020',
    'FY2018': 'February 2, 2019',
    'FY2017': 'February 3, 2018',
    'FY2016': 'January 28, 2017',
    'FY2015': 'January 30, 2016',
}


def get_fiscal_year_end_date(period: str) -> str:
    """Get the fiscal year end date for a given period (e.g., 'FY2024')."""
    return FISCAL_YEAR_END_DATES.get(period, 'Unknown')


def load_analysis_data(filepath: str = "output/target_analysis.json") -> Dict:
    """Load the detailed analysis data with raw values."""
    with open(filepath, 'r') as f:
        return json.load(f)


def load_timeseries_data(filepath: str = "output/target_timeseries.json") -> Dict:
    """Load time-series data for validation."""
    with open(filepath, 'r') as f:
        return json.load(f)


def filter_annual_periods(analysis_data: Dict, years: int = 5) -> List[Dict]:
    """
    Filter to annual 10-K periods only, returning the most recent N years.

    Args:
        analysis_data: Full analysis data from target_analysis.json
        years: Number of years to include (default 5)

    Returns:
        List of annual filing data sorted by fiscal year (ascending)
    """
    annual_filings = []

    for filing in analysis_data.get('filings', []):
        period = filing.get('period', '')
        filing_type = filing.get('filing_type', '')

        # Only include 10-K annual reports
        if filing_type == '10-K' and period.startswith('FY'):
            annual_filings.append(filing)

    # Sort by fiscal year (ascending)
    annual_filings.sort(key=lambda x: int(x['period'].replace('FY', '')))

    # Return most recent N years
    return annual_filings[-years:] if len(annual_filings) >= years else annual_filings


def extract_dupont_data(filing: Dict, prior_filing: Dict = None) -> Dict:
    """
    Extract all DuPont-related data from a single filing.

    Uses average total assets and average stockholders equity for Asset Turnover
    and Financial Leverage calculations (proper DuPont methodology since income
    statement items are flow values while balance sheet items are point-in-time).

    Args:
        filing: Single filing data from target_analysis.json
        prior_filing: Prior year's filing for calculating averages (optional)

    Returns:
        Dict with all raw values, calculated components, and validation
    """
    vital_signs = filing.get('vital_signs', {})
    debt_metrics = filing.get('debt_metrics', {})

    # Raw values from SEC filing (current period - end of year)
    net_income = vital_signs.get('net_income_billion')
    revenue = vital_signs.get('net_sales_billion')
    total_assets = vital_signs.get('total_assets_billion')
    stockholders_equity = vital_signs.get('stockholders_equity_billion')

    # Get prior year values for averaging (if available)
    prior_total_assets = None
    prior_stockholders_equity = None
    avg_total_assets = total_assets
    avg_stockholders_equity = stockholders_equity

    if prior_filing:
        prior_vital = prior_filing.get('vital_signs', {})
        prior_total_assets = prior_vital.get('total_assets_billion')
        prior_stockholders_equity = prior_vital.get('stockholders_equity_billion')

        if prior_total_assets and total_assets:
            avg_total_assets = (prior_total_assets + total_assets) / 2
        if prior_stockholders_equity and stockholders_equity:
            avg_stockholders_equity = (prior_stockholders_equity + stockholders_equity) / 2

    # Pre-calculated DuPont components (from financial_analyzer.py)
    profit_margin_pct = vital_signs.get('net_profit_margin_percent')
    asset_turnover = debt_metrics.get('dupont_asset_turnover')
    financial_leverage = debt_metrics.get('dupont_financial_leverage')
    roe_extracted = debt_metrics.get('return_on_equity_percent')
    roe_validation = debt_metrics.get('dupont_roe_validation')

    # Manual calculations for validation document (using averages)
    calculated = {}
    if all(v is not None for v in [net_income, revenue, avg_total_assets, avg_stockholders_equity]):
        if revenue > 0 and avg_total_assets > 0 and avg_stockholders_equity > 0:
            calculated['profit_margin'] = (net_income / revenue) * 100
            calculated['asset_turnover'] = revenue / avg_total_assets
            calculated['financial_leverage'] = avg_total_assets / avg_stockholders_equity
            calculated['roe_direct'] = (net_income / avg_stockholders_equity) * 100
            calculated['roe_dupont'] = (
                (calculated['profit_margin'] / 100) *
                calculated['asset_turnover'] *
                calculated['financial_leverage'] * 100
            )

    return {
        'period': filing.get('period'),
        'raw': {
            'net_income_billion': net_income,
            'revenue_billion': revenue,
            'total_assets_billion': total_assets,
            'stockholders_equity_billion': stockholders_equity,
            'prior_total_assets_billion': prior_total_assets,
            'prior_stockholders_equity_billion': prior_stockholders_equity,
            'avg_total_assets_billion': avg_total_assets,
            'avg_stockholders_equity_billion': avg_stockholders_equity
        },
        'extracted': {
            'profit_margin_percent': profit_margin_pct,
            'asset_turnover': asset_turnover,
            'financial_leverage': financial_leverage,
            'roe_percent': roe_extracted,
            'roe_validation': roe_validation
        },
        'calculated': calculated
    }


def generate_validation_html(annual_data: List[Dict], output_path: str) -> None:
    """
    Generate styled HTML validation document with side-by-side calculations.

    Args:
        annual_data: List of extracted DuPont data for each year
        output_path: Path to write HTML file
    """
    html_parts = ['''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuPont Analysis Validation - Target Corporation</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .formula-box {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            border-left: 4px solid #cc0000;
        }
        .formula-box h2 {
            color: #cc0000;
            margin-bottom: 15px;
        }
        .formula-code {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.95em;
            overflow-x: auto;
        }
        .period-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }
        .period-card h2 {
            color: #cc0000;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
        }
        .data-table th {
            background: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }
        .data-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        .data-table tr:hover {
            background: #fafafa;
        }
        .gaap-tag {
            font-family: monospace;
            font-size: 0.85em;
            color: #666;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .calc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .calc-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e0e0e0;
        }
        .calc-card h3 {
            color: #555;
            font-size: 1em;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .calc-card .formula {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        .calc-card .calculation {
            font-family: monospace;
            color: #333;
            margin-bottom: 8px;
        }
        .calc-card .result {
            font-size: 1.4em;
            font-weight: 700;
            color: #cc0000;
        }
        .calc-card.roe {
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border-color: #4caf50;
        }
        .calc-card.roe h3 {
            color: #2e7d32;
        }
        .calc-card.roe .result {
            color: #2e7d32;
        }
        .validation-row {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .validation-row span {
            padding: 4px 10px;
            border-radius: 4px;
        }
        .pass {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .check {
            background: #fff3e0;
            color: #e65100;
        }
        .match-table {
            width: 100%;
            border-collapse: collapse;
        }
        .match-table th {
            background: #f0f0f0;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
        }
        .match-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }
        .match-y {
            color: #2e7d32;
            font-weight: 600;
        }
        .match-n {
            color: #c62828;
            font-weight: 600;
        }
        .summary-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }
        .summary-section h2 {
            color: #cc0000;
            margin-bottom: 20px;
        }
        .summary-table {
            width: 100%;
            border-collapse: collapse;
        }
        .summary-table th {
            background: #cc0000;
            color: white;
            padding: 12px 15px;
            text-align: center;
            font-weight: 600;
        }
        .summary-table td {
            padding: 12px 15px;
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
        }
        .summary-table tr:nth-child(even) {
            background: #fafafa;
        }
        .observations {
            background: #fff8e1;
            border-radius: 12px;
            padding: 25px;
            margin-top: 25px;
            border: 1px solid #ffcc02;
        }
        .observations h2 {
            color: #f57c00;
            margin-bottom: 15px;
        }
        .observation-item {
            margin-bottom: 10px;
        }
        .positive { color: #2e7d32; }
        .negative { color: #c62828; }
        footer {
            text-align: center;
            color: #999;
            font-size: 0.85em;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DuPont Analysis Validation Report</h1>
            <p><strong>Company:</strong> Target Corporation (TGT)</p>
            <p><strong>Periods Analyzed:</strong> ''' + f"{annual_data[0]['period']} - {annual_data[-1]['period']}" + '''</p>
        </header>

        <div class="formula-box">
            <h2>DuPont Formula</h2>
            <div class="formula-code">
ROE = Profit Margin &times; Asset Turnover &times; Financial Leverage

Where:
  Profit Margin      = Net Income / Revenue &times; 100
  Asset Turnover     = Revenue / <strong>Average</strong> Total Assets
  Financial Leverage = <strong>Average</strong> Total Assets / <strong>Average</strong> Stockholders Equity
  ROE (direct)       = Net Income / <strong>Average</strong> Stockholders Equity

<em>Average = (Beginning of Year + End of Year) / 2</em>
            </div>
            <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                <strong>Note:</strong> Average values are used for balance sheet items (Assets, Equity) because
                income statement items (Revenue, Net Income) are flow values over the entire period,
                while balance sheet items are point-in-time snapshots.
            </p>
        </div>
''']

    # Generate section for each fiscal year (most recent first)
    for data in reversed(annual_data):
        period = data['period']
        fy_end_date = get_fiscal_year_end_date(period)
        raw = data['raw']
        extracted = data['extracted']
        calculated = data.get('calculated', {})

        html_parts.append(f'''
        <section class="period-card">
            <h2>{period}<span style="font-weight: normal; font-size: 0.7em; color: #666; margin-left: 15px;">For the fiscal year ended {fy_end_date}</span></h2>

            <h3 style="color: #555; margin-bottom: 15px;">Raw Data from SEC 10-K Filing</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>GAAP Tag</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Net Income</td>
                        <td><strong>${raw['net_income_billion']:.3f}B</strong></td>
                        <td><span class="gaap-tag">us-gaap:NetIncomeLoss</span></td>
                    </tr>
                    <tr>
                        <td>Revenue</td>
                        <td><strong>${raw['revenue_billion']:.3f}B</strong></td>
                        <td><span class="gaap-tag">us-gaap:RevenueFromContractWithCustomer...</span></td>
                    </tr>
                    <tr>
                        <td>Total Assets (End of Year)</td>
                        <td><strong>${raw['total_assets_billion']:.3f}B</strong></td>
                        <td><span class="gaap-tag">us-gaap:Assets</span></td>
                    </tr>
                    <tr>
                        <td>Stockholders Equity (End of Year)</td>
                        <td><strong>${raw['stockholders_equity_billion']:.3f}B</strong></td>
                        <td><span class="gaap-tag">us-gaap:StockholdersEquity</span></td>
                    </tr>''')

        # Add prior year and average rows if available
        if raw.get('prior_total_assets_billion') is not None:
            html_parts.append(f'''
                    <tr style="background: #f0f8ff;">
                        <td>Total Assets (Prior Year End)</td>
                        <td>${raw['prior_total_assets_billion']:.3f}B</td>
                        <td><em>For averaging</em></td>
                    </tr>
                    <tr style="background: #e8f5e9;">
                        <td><strong>Average Total Assets</strong></td>
                        <td><strong>${raw['avg_total_assets_billion']:.3f}B</strong></td>
                        <td><em>(Prior + Current) / 2</em></td>
                    </tr>''')
        else:
            html_parts.append(f'''
                    <tr style="background: #fff8e1;">
                        <td><strong>Average Total Assets</strong></td>
                        <td><strong>${raw['avg_total_assets_billion']:.3f}B</strong></td>
                        <td><em>First year: using end of year</em></td>
                    </tr>''')

        if raw.get('prior_stockholders_equity_billion') is not None:
            html_parts.append(f'''
                    <tr style="background: #f0f8ff;">
                        <td>Stockholders Equity (Prior Year End)</td>
                        <td>${raw['prior_stockholders_equity_billion']:.3f}B</td>
                        <td><em>For averaging</em></td>
                    </tr>
                    <tr style="background: #e8f5e9;">
                        <td><strong>Average Stockholders Equity</strong></td>
                        <td><strong>${raw['avg_stockholders_equity_billion']:.3f}B</strong></td>
                        <td><em>(Prior + Current) / 2</em></td>
                    </tr>''')
        else:
            html_parts.append(f'''
                    <tr style="background: #fff8e1;">
                        <td><strong>Average Stockholders Equity</strong></td>
                        <td><strong>${raw['avg_stockholders_equity_billion']:.3f}B</strong></td>
                        <td><em>First year: using end of year</em></td>
                    </tr>''')

        html_parts.append('''
                </tbody>
            </table>
''')

        if calculated:
            roe_variance = abs(calculated['roe_dupont'] - calculated['roe_direct'])
            validation_status = "PASS" if roe_variance < 0.5 else "CHECK"
            status_class = "pass" if validation_status == "PASS" else "check"

            # Build Asset Turnover calculation display
            if raw.get('prior_total_assets_billion') is not None:
                at_avg_display = f"(${raw['prior_total_assets_billion']:.3f}B + ${raw['total_assets_billion']:.3f}B) / 2 = ${raw['avg_total_assets_billion']:.3f}B"
                at_calc_display = f"${raw['revenue_billion']:.3f}B &divide; ${raw['avg_total_assets_billion']:.3f}B"
            else:
                at_avg_display = f"${raw['avg_total_assets_billion']:.3f}B <em>(first year)</em>"
                at_calc_display = f"${raw['revenue_billion']:.3f}B &divide; ${raw['avg_total_assets_billion']:.3f}B"

            # Build Financial Leverage calculation display
            if raw.get('prior_stockholders_equity_billion') is not None:
                fl_avg_assets = f"${raw['avg_total_assets_billion']:.3f}B"
                fl_avg_equity = f"${raw['avg_stockholders_equity_billion']:.3f}B"
                fl_calc_display = f"{fl_avg_assets} &divide; {fl_avg_equity}"
            else:
                fl_calc_display = f"${raw['total_assets_billion']:.3f}B &divide; ${raw['stockholders_equity_billion']:.3f}B <em>(first year)</em>"

            html_parts.append(f'''
            <h3 style="color: #555; margin-bottom: 15px;">DuPont Component Calculations</h3>
            <div class="calc-grid">
                <div class="calc-card">
                    <h3>1. Profit Margin</h3>
                    <p class="formula">Net Income &divide; Revenue &times; 100</p>
                    <p class="calculation">${raw['net_income_billion']:.3f}B &divide; ${raw['revenue_billion']:.3f}B &times; 100</p>
                    <p class="result">{calculated['profit_margin']:.2f}%</p>
                </div>
                <div class="calc-card">
                    <h3>2. Asset Turnover</h3>
                    <p class="formula">Revenue &divide; <strong>Average</strong> Total Assets</p>
                    <p class="calculation" style="font-size: 0.85em;">Avg Assets: {at_avg_display}</p>
                    <p class="calculation">{at_calc_display}</p>
                    <p class="result">{calculated['asset_turnover']:.2f}x</p>
                </div>
                <div class="calc-card">
                    <h3>3. Financial Leverage</h3>
                    <p class="formula"><strong>Avg</strong> Total Assets &divide; <strong>Avg</strong> Stockholders Equity</p>
                    <p class="calculation">{fl_calc_display}</p>
                    <p class="result">{calculated['financial_leverage']:.2f}x</p>
                </div>
                <div class="calc-card roe">
                    <h3>4. ROE Validation</h3>
                    <p class="formula">Profit Margin &times; Asset Turnover &times; Financial Leverage</p>
                    <p class="calculation">{calculated['profit_margin']:.2f}% &times; {calculated['asset_turnover']:.2f}x &times; {calculated['financial_leverage']:.2f}x</p>
                    <p class="result">{calculated['roe_dupont']:.2f}%</p>
                    <div class="validation-row">
                        <span>Direct ROE (NI/Avg Equity): {calculated['roe_direct']:.2f}%</span>
                        <span class="{status_class}">Variance: {roe_variance:.2f}% {validation_status}</span>
                    </div>
                </div>
            </div>

            <h3 style="color: #555; margin-bottom: 15px;">Validation Against Extracted Values</h3>
            <table class="match-table">
                <thead>
                    <tr>
                        <th>Component</th>
                        <th>Calculated</th>
                        <th>Extracted</th>
                        <th>Match</th>
                    </tr>
                </thead>
                <tbody>
''')
            # Check profit margin
            pm_match = "Y" if extracted['profit_margin_percent'] and abs(calculated['profit_margin'] - extracted['profit_margin_percent']) < 0.1 else "N"
            pm_class = "match-y" if pm_match == "Y" else "match-n"
            html_parts.append(f'''
                    <tr>
                        <td>Profit Margin</td>
                        <td>{calculated['profit_margin']:.2f}%</td>
                        <td>{extracted['profit_margin_percent']}%</td>
                        <td class="{pm_class}">{pm_match}</td>
                    </tr>
''')

            # Check asset turnover
            at_match = "Y" if extracted['asset_turnover'] and abs(calculated['asset_turnover'] - extracted['asset_turnover']) < 0.1 else "N"
            at_class = "match-y" if at_match == "Y" else "match-n"
            html_parts.append(f'''
                    <tr>
                        <td>Asset Turnover</td>
                        <td>{calculated['asset_turnover']:.2f}x</td>
                        <td>{extracted['asset_turnover']}x</td>
                        <td class="{at_class}">{at_match}</td>
                    </tr>
''')

            # Check financial leverage
            fl_match = "Y" if extracted['financial_leverage'] and abs(calculated['financial_leverage'] - extracted['financial_leverage']) < 0.1 else "N"
            fl_class = "match-y" if fl_match == "Y" else "match-n"
            html_parts.append(f'''
                    <tr>
                        <td>Financial Leverage</td>
                        <td>{calculated['financial_leverage']:.2f}x</td>
                        <td>{extracted['financial_leverage']}x</td>
                        <td class="{fl_class}">{fl_match}</td>
                    </tr>
''')

            # Check ROE
            roe_match = "Y" if extracted['roe_percent'] and abs(calculated['roe_direct'] - extracted['roe_percent']) < 0.5 else "N"
            roe_class = "match-y" if roe_match == "Y" else "match-n"
            html_parts.append(f'''
                    <tr>
                        <td>ROE</td>
                        <td>{calculated['roe_direct']:.2f}%</td>
                        <td>{extracted['roe_percent']}%</td>
                        <td class="{roe_class}">{roe_match}</td>
                    </tr>
                </tbody>
            </table>
''')
        else:
            html_parts.append('''
            <p style="color: #999; font-style: italic;">Insufficient data for calculations</p>
''')

        html_parts.append('        </section>')

    # Summary table
    html_parts.append('''
        <section class="summary-section">
            <h2>Summary: 5-Year DuPont Trend</h2>
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Profit Margin</th>
                        <th>Asset Turnover</th>
                        <th>Financial Leverage</th>
                        <th>ROE</th>
                    </tr>
                </thead>
                <tbody>
''')

    for data in annual_data:
        calc = data.get('calculated', {})
        period = data['period']
        fy_end_date = get_fiscal_year_end_date(period)
        if calc:
            html_parts.append(f'''
                    <tr>
                        <td><strong>{period}</strong><br><span style="font-size: 0.8em; color: #666;">ended {fy_end_date}</span></td>
                        <td>{calc['profit_margin']:.2f}%</td>
                        <td>{calc['asset_turnover']:.2f}x</td>
                        <td>{calc['financial_leverage']:.2f}x</td>
                        <td><strong>{calc['roe_direct']:.2f}%</strong></td>
                    </tr>
''')
        else:
            html_parts.append(f'''
                    <tr>
                        <td><strong>{period}</strong><br><span style="font-size: 0.8em; color: #666;">ended {fy_end_date}</span></td>
                        <td>N/A</td>
                        <td>N/A</td>
                        <td>N/A</td>
                        <td>N/A</td>
                    </tr>
''')

    html_parts.append('''
                </tbody>
            </table>
        </section>
''')

    # Add observations
    if len(annual_data) >= 2:
        first = annual_data[0].get('calculated', {})
        last = annual_data[-1].get('calculated', {})

        if first and last:
            roe_change = last['roe_direct'] - first['roe_direct']
            pm_change = last['profit_margin'] - first['profit_margin']
            at_change = last['asset_turnover'] - first['asset_turnover']
            fl_change = last['financial_leverage'] - first['financial_leverage']

            pm_class = "positive" if pm_change > 0 else "negative"
            at_class = "positive" if at_change > 0 else "negative"
            fl_class = "positive" if fl_change > 0 else "negative"
            roe_class = "positive" if roe_change > 0 else "negative"

            html_parts.append(f'''
        <div class="observations">
            <h2>Key Observations</h2>
            <p class="observation-item"><strong>ROE Change ({annual_data[0]['period']} to {annual_data[-1]['period']}):</strong> <span class="{roe_class}">{roe_change:+.2f}%</span></p>
            <p style="margin-top: 15px; margin-bottom: 10px;"><strong>Component Drivers:</strong></p>
            <ul style="margin-left: 20px;">
                <li class="observation-item">Profit Margin: <span class="{pm_class}">{pm_change:+.2f}%</span> ({'improving' if pm_change > 0 else 'declining'})</li>
                <li class="observation-item">Asset Turnover: <span class="{at_class}">{at_change:+.2f}x</span> ({'improving' if at_change > 0 else 'declining'})</li>
                <li class="observation-item">Financial Leverage: <span class="{fl_class}">{fl_change:+.2f}x</span> ({'increasing' if fl_change > 0 else 'decreasing'})</li>
            </ul>
        </div>
''')

    html_parts.append('''
        <footer>
            <p>Generated by DuPont Analysis Validation Tool | Target Corporation Financial Analyzer</p>
        </footer>
    </div>
</body>
</html>
''')

    # Write file
    with open(output_path, 'w') as f:
        f.write(''.join(html_parts))

    print(f"HTML validation document created: {output_path}")


def generate_validation_document(annual_data: List[Dict], output_path: str) -> None:
    """
    Generate markdown validation document with side-by-side calculations.

    Args:
        annual_data: List of extracted DuPont data for each year
        output_path: Path to write markdown file
    """
    lines = [
        "# DuPont Analysis Validation Report",
        "",
        "**Company**: Target Corporation (TGT)",
        f"**Periods Analyzed**: {annual_data[0]['period']} - {annual_data[-1]['period']}",
        "**Generated**: Automated validation tool",
        "",
        "---",
        "",
        "## DuPont Formula",
        "",
        "```",
        "ROE = Profit Margin x Asset Turnover x Financial Leverage",
        "",
        "Where:",
        "  Profit Margin      = Net Income / Revenue",
        "  Asset Turnover     = Revenue / Average Total Assets",
        "  Financial Leverage = Average Total Assets / Average Stockholders Equity",
        "  ROE (direct)       = Net Income / Average Stockholders Equity",
        "",
        "Average = (Beginning of Year + End of Year) / 2",
        "```",
        "",
        "**Note**: Average values are used for balance sheet items (Assets, Equity) because",
        "income statement items (Revenue, Net Income) are flow values over the entire period,",
        "while balance sheet items are point-in-time snapshots.",
        "",
        "---",
        ""
    ]

    # Generate section for each fiscal year (most recent first)
    for data in reversed(annual_data):
        period = data['period']
        fy_end_date = get_fiscal_year_end_date(period)
        raw = data['raw']
        extracted = data['extracted']
        calculated = data.get('calculated', {})

        lines.extend([
            f"## {period} — For the fiscal year ended {fy_end_date}",
            "",
            "### Raw Data Extracted from SEC 10-K Filing",
            "",
            "| Metric | Value | GAAP Tag |",
            "|--------|-------|----------|",
        ])

        # Format raw values
        if raw['net_income_billion'] is not None:
            lines.append(f"| Net Income | ${raw['net_income_billion']:.3f}B | us-gaap:NetIncomeLoss |")
        else:
            lines.append("| Net Income | N/A | us-gaap:NetIncomeLoss |")

        if raw['revenue_billion'] is not None:
            lines.append(f"| Revenue | ${raw['revenue_billion']:.3f}B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |")
        else:
            lines.append("| Revenue | N/A | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |")

        if raw['total_assets_billion'] is not None:
            lines.append(f"| Total Assets (End of Year) | ${raw['total_assets_billion']:.3f}B | us-gaap:Assets |")
        else:
            lines.append("| Total Assets (End of Year) | N/A | us-gaap:Assets |")

        if raw['stockholders_equity_billion'] is not None:
            lines.append(f"| Stockholders Equity (End of Year) | ${raw['stockholders_equity_billion']:.3f}B | us-gaap:StockholdersEquity |")
        else:
            lines.append("| Stockholders Equity (End of Year) | N/A | us-gaap:StockholdersEquity |")

        # Show prior year values and averages if available
        if raw.get('prior_total_assets_billion') is not None:
            lines.append(f"| Total Assets (Prior Year End) | ${raw['prior_total_assets_billion']:.3f}B | — |")
            lines.append(f"| **Average Total Assets** | **${raw['avg_total_assets_billion']:.3f}B** | (Prior + Current) / 2 |")
        else:
            lines.append(f"| **Average Total Assets** | **${raw['avg_total_assets_billion']:.3f}B** | *(First year: using end of year)* |")

        if raw.get('prior_stockholders_equity_billion') is not None:
            lines.append(f"| Stockholders Equity (Prior Year End) | ${raw['prior_stockholders_equity_billion']:.3f}B | — |")
            lines.append(f"| **Average Stockholders Equity** | **${raw['avg_stockholders_equity_billion']:.3f}B** | (Prior + Current) / 2 |")
        else:
            lines.append(f"| **Average Stockholders Equity** | **${raw['avg_stockholders_equity_billion']:.3f}B** | *(First year: using end of year)* |")

        lines.extend(["", "### DuPont Component Calculations", ""])

        if calculated:
            # 1. Profit Margin
            lines.extend([
                "**1. Profit Margin**",
                "- Formula: Net Income / Revenue x 100",
                f"- Calculation: ${raw['net_income_billion']:.3f}B / ${raw['revenue_billion']:.3f}B x 100",
                f"- Result: **{calculated['profit_margin']:.2f}%**",
                ""
            ])

            # 2. Asset Turnover (using average)
            if raw.get('prior_total_assets_billion') is not None:
                avg_calc = f"(${raw['prior_total_assets_billion']:.3f}B + ${raw['total_assets_billion']:.3f}B) / 2 = ${raw['avg_total_assets_billion']:.3f}B"
                lines.extend([
                    "**2. Asset Turnover**",
                    "- Formula: Revenue / Average Total Assets",
                    f"- Average Total Assets: {avg_calc}",
                    f"- Calculation: ${raw['revenue_billion']:.3f}B / ${raw['avg_total_assets_billion']:.3f}B",
                    f"- Result: **{calculated['asset_turnover']:.2f}x**",
                    ""
                ])
            else:
                lines.extend([
                    "**2. Asset Turnover**",
                    "- Formula: Revenue / Average Total Assets",
                    f"- Average Total Assets: ${raw['avg_total_assets_billion']:.3f}B *(first year: using end of year)*",
                    f"- Calculation: ${raw['revenue_billion']:.3f}B / ${raw['avg_total_assets_billion']:.3f}B",
                    f"- Result: **{calculated['asset_turnover']:.2f}x**",
                    ""
                ])

            # 3. Financial Leverage (using averages)
            if raw.get('prior_stockholders_equity_billion') is not None:
                avg_assets_calc = f"(${raw['prior_total_assets_billion']:.3f}B + ${raw['total_assets_billion']:.3f}B) / 2 = ${raw['avg_total_assets_billion']:.3f}B"
                avg_equity_calc = f"(${raw['prior_stockholders_equity_billion']:.3f}B + ${raw['stockholders_equity_billion']:.3f}B) / 2 = ${raw['avg_stockholders_equity_billion']:.3f}B"
                lines.extend([
                    "**3. Financial Leverage**",
                    "- Formula: Average Total Assets / Average Stockholders Equity",
                    f"- Avg Total Assets: {avg_assets_calc}",
                    f"- Avg Stockholders Equity: {avg_equity_calc}",
                    f"- Calculation: ${raw['avg_total_assets_billion']:.3f}B / ${raw['avg_stockholders_equity_billion']:.3f}B",
                    f"- Result: **{calculated['financial_leverage']:.2f}x**",
                    ""
                ])
            else:
                lines.extend([
                    "**3. Financial Leverage**",
                    "- Formula: Average Total Assets / Average Stockholders Equity",
                    f"- Using end of year values *(first year: no prior year average available)*",
                    f"- Calculation: ${raw['total_assets_billion']:.3f}B / ${raw['stockholders_equity_billion']:.3f}B",
                    f"- Result: **{calculated['financial_leverage']:.2f}x**",
                    ""
                ])

            # 4. ROE Validation
            roe_variance = abs(calculated['roe_dupont'] - calculated['roe_direct'])
            validation_status = "PASS" if roe_variance < 0.5 else "CHECK"

            lines.extend([
                "**4. ROE Validation**",
                "- Formula: Profit Margin x Asset Turnover x Financial Leverage",
                f"- Calculation: {calculated['profit_margin']:.4f}% x {calculated['asset_turnover']:.4f} x {calculated['financial_leverage']:.4f}",
                f"- Calculated ROE (DuPont): **{calculated['roe_dupont']:.2f}%**",
                f"- Direct ROE (NI/Equity): **{calculated['roe_direct']:.2f}%**",
                f"- Variance: {roe_variance:.2f}% {validation_status}",
                ""
            ])

            # Comparison with extracted values
            lines.extend([
                "### Validation Against Extracted Values",
                "",
                "| Component | Calculated | Extracted | Match |",
                "|-----------|------------|-----------|-------|",
            ])

            # Check profit margin
            pm_match = "Y" if extracted['profit_margin_percent'] and abs(calculated['profit_margin'] - extracted['profit_margin_percent']) < 0.1 else "N"
            lines.append(f"| Profit Margin | {calculated['profit_margin']:.2f}% | {extracted['profit_margin_percent']}% | {pm_match} |")

            # Check asset turnover
            at_match = "Y" if extracted['asset_turnover'] and abs(calculated['asset_turnover'] - extracted['asset_turnover']) < 0.1 else "N"
            lines.append(f"| Asset Turnover | {calculated['asset_turnover']:.2f}x | {extracted['asset_turnover']}x | {at_match} |")

            # Check financial leverage
            fl_match = "Y" if extracted['financial_leverage'] and abs(calculated['financial_leverage'] - extracted['financial_leverage']) < 0.1 else "N"
            lines.append(f"| Financial Leverage | {calculated['financial_leverage']:.2f}x | {extracted['financial_leverage']}x | {fl_match} |")

            # Check ROE
            roe_match = "Y" if extracted['roe_percent'] and abs(calculated['roe_direct'] - extracted['roe_percent']) < 0.5 else "N"
            lines.append(f"| ROE | {calculated['roe_direct']:.2f}% | {extracted['roe_percent']}% | {roe_match} |")

        else:
            lines.append("*Insufficient data for calculations*")

        lines.extend(["", "---", ""])

    # Summary table
    lines.extend([
        "## Summary: 5-Year DuPont Trend",
        "",
        "| Period | Profit Margin | Asset Turnover | Financial Leverage | ROE |",
        "|--------|---------------|----------------|--------------------|----|",
    ])

    for data in annual_data:
        calc = data.get('calculated', {})
        period = data['period']
        fy_end_date = get_fiscal_year_end_date(period)
        period_label = f"{period} (ended {fy_end_date})"
        if calc:
            lines.append(
                f"| {period_label} | {calc['profit_margin']:.2f}% | "
                f"{calc['asset_turnover']:.2f}x | {calc['financial_leverage']:.2f}x | "
                f"{calc['roe_direct']:.2f}% |"
            )
        else:
            lines.append(f"| {period_label} | N/A | N/A | N/A | N/A |")

    lines.extend([
        "",
        "---",
        "",
        "## Key Observations",
        "",
    ])

    # Add observations based on data
    if len(annual_data) >= 2:
        first = annual_data[0].get('calculated', {})
        last = annual_data[-1].get('calculated', {})

        if first and last:
            roe_change = last['roe_direct'] - first['roe_direct']
            pm_change = last['profit_margin'] - first['profit_margin']
            at_change = last['asset_turnover'] - first['asset_turnover']
            fl_change = last['financial_leverage'] - first['financial_leverage']

            lines.append(f"**ROE Change ({annual_data[0]['period']} to {annual_data[-1]['period']})**: {roe_change:+.2f}%")
            lines.append("")
            lines.append("**Component Drivers**:")
            lines.append(f"- Profit Margin: {pm_change:+.2f}% ({'improving' if pm_change > 0 else 'declining'})")
            lines.append(f"- Asset Turnover: {at_change:+.2f}x ({'improving' if at_change > 0 else 'declining'})")
            lines.append(f"- Financial Leverage: {fl_change:+.2f}x ({'increasing' if fl_change > 0 else 'decreasing'})")

    # Write file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Validation document created: {output_path}")


def create_annual_trend_chart(annual_data: List[Dict], output_path: str) -> go.Figure:
    """
    Create 5-year line chart comparing DuPont components.

    Args:
        annual_data: List of extracted DuPont data for each year
        output_path: Path to write HTML chart

    Returns:
        Plotly Figure object
    """
    # Extract data for plotting
    periods = []
    profit_margins = []
    asset_turnovers = []
    financial_leverages = []
    roes = []

    for data in annual_data:
        calc = data.get('calculated', {})
        if calc:
            periods.append(data['period'])
            profit_margins.append(calc['profit_margin'])
            asset_turnovers.append(calc['asset_turnover'])
            financial_leverages.append(calc['financial_leverage'])
            roes.append(calc['roe_direct'])

    if not periods:
        print("No data available for chart")
        return None

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Left Y-axis: Percentages (Profit Margin, ROE)
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=profit_margins,
            name='Profit Margin (%)',
            mode='lines+markers',
            line=dict(color='#3498db', width=2),
            marker=dict(size=10, symbol='circle'),
            hovertemplate='<b>%{x}</b><br>Profit Margin: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=periods,
            y=roes,
            name='ROE (%)',
            mode='lines+markers',
            line=dict(color='#27ae60', width=3),
            marker=dict(size=12, symbol='diamond'),
            hovertemplate='<b>%{x}</b><br>ROE: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=False
    )

    # Right Y-axis: Multipliers (Asset Turnover, Financial Leverage)
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=asset_turnovers,
            name='Asset Turnover (x)',
            mode='lines+markers',
            line=dict(color='#e67e22', width=2, dash='dash'),
            marker=dict(size=10, symbol='square'),
            hovertemplate='<b>%{x}</b><br>Asset Turnover: %{y:.2f}x<extra></extra>'
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(
            x=periods,
            y=financial_leverages,
            name='Financial Leverage (x)',
            mode='lines+markers',
            line=dict(color='#9b59b6', width=2, dash='dash'),
            marker=dict(size=10, symbol='triangle-up'),
            hovertemplate='<b>%{x}</b><br>Financial Leverage: %{y:.2f}x<extra></extra>'
        ),
        secondary_y=True
    )

    # Add annotations for significant changes
    if len(roes) >= 2:
        max_roe_idx = roes.index(max(roes))
        min_roe_idx = roes.index(min(roes))

        # Annotate max ROE
        fig.add_annotation(
            x=periods[max_roe_idx],
            y=roes[max_roe_idx],
            text=f"Peak: {roes[max_roe_idx]:.1f}%",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            ax=0,
            ay=-40,
            font=dict(size=10, color='#27ae60'),
            bgcolor='white',
            bordercolor='#27ae60',
            borderwidth=1,
            borderpad=3
        )

        # Annotate min ROE (if different from max)
        if min_roe_idx != max_roe_idx:
            fig.add_annotation(
                x=periods[min_roe_idx],
                y=roes[min_roe_idx],
                text=f"Low: {roes[min_roe_idx]:.1f}%",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1,
                ax=0,
                ay=40,
                font=dict(size=10, color='#e74c3c'),
                bgcolor='white',
                bordercolor='#e74c3c',
                borderwidth=1,
                borderpad=3
            )

    # Update layout
    fig.update_layout(
        title={
            'text': 'Target: DuPont Analysis - 5-Year Annual Trend<br><sub>ROE = Profit Margin x Asset Turnover x Financial Leverage</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top',
            'font': dict(size=16)
        },
        xaxis_title='Fiscal Year',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#BDBDBD',
            borderwidth=1
        ),
        height=600,
        margin=dict(t=120, b=80, l=80, r=80),
        hovermode='x unified',
        plot_bgcolor='white'
    )

    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#E0E0E0',
        showline=True,
        linewidth=1,
        linecolor='#BDBDBD'
    )

    fig.update_yaxes(
        title_text='Percentage (%)',
        secondary_y=False,
        showgrid=True,
        gridwidth=1,
        gridcolor='#E0E0E0',
        showline=True,
        linewidth=1,
        linecolor='#BDBDBD',
        rangemode='tozero'
    )

    fig.update_yaxes(
        title_text='Multiplier (x)',
        secondary_y=True,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#BDBDBD',
        rangemode='tozero'
    )

    # Save chart
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"Annual trend chart created: {output_path}")

    return fig


def main():
    """Main entry point for DuPont validation tool."""
    print("=" * 60)
    print("DuPont Analysis Validation Tool")
    print("=" * 60)
    print()

    # Check for required input files
    analysis_path = Path("output/target_analysis.json")
    if not analysis_path.exists():
        print("ERROR: target_analysis.json not found.")
        print("Run 'python3 financial_analyzer.py' first.")
        return 1

    # Load data
    print("Loading analysis data...")
    analysis_data = load_analysis_data(str(analysis_path))

    # Filter to annual periods (last 5 years)
    print("Filtering to annual periods...")
    annual_filings = filter_annual_periods(analysis_data, years=5)

    if not annual_filings:
        print("ERROR: No annual filing data found")
        return 1

    print(f"Found {len(annual_filings)} annual periods: {[f['period'] for f in annual_filings]}")

    # Extract DuPont data for each period (with prior year for averaging)
    print("\nExtracting DuPont components (using average assets/equity)...")
    annual_data = []
    for i, filing in enumerate(annual_filings):
        prior = annual_filings[i - 1] if i > 0 else None
        annual_data.append(extract_dupont_data(filing, prior))

    # Generate validation documents
    print("\nGenerating validation documents...")
    generate_validation_document(annual_data, "output/dupont_validation.md")
    generate_validation_html(annual_data, "output/dupont_validation.html")

    # Create line chart
    print("\nCreating annual trend chart...")
    create_annual_trend_chart(annual_data, "output/chart_dupont_annual_trend.html")

    print()
    print("=" * 60)
    print("DuPont Validation Complete")
    print("=" * 60)
    print()
    print("Outputs:")
    print("  1. output/dupont_validation.md - Validation document (Markdown)")
    print("  2. output/dupont_validation.html - Validation document (HTML)")
    print("  3. output/chart_dupont_annual_trend.html - 5-year trend chart")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
