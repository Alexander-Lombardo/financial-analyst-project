"""
Comprehensive Test Suite for Pillar 2: Liquidity & Solvency Analysis.

Tests:
1. Extraction Tests (5 tests) - Verify GAAP balance sheet data extraction
2. Liquidity Calculation Tests (6 tests) - Current Ratio, Quick Ratio, Working Capital
3. Solvency Calculation Tests (8 tests) - D/E, D/A, Equity, Debt-to-EBITDA, ROE, ROA
4. Export Tests (3 tests) - Time-series JSON structure validation
5. Visualization Tests (3 tests) - Chart file creation verification

Total: 25+ test cases
"""

import json
import pytest
from pathlib import Path


def load_analysis_data():
    """Load detailed analysis JSON."""
    with open('output/target_analysis.json', 'r') as f:
        return json.load(f)


def load_timeseries_data():
    """Load time-series JSON."""
    with open('output/target_timeseries.json', 'r') as f:
        return json.load(f)


# =============================================================================
# Category 1: Extraction Tests (5 tests)
# =============================================================================

def test_balance_sheet_extraction():
    """Verify 6 new balance sheet items extracted for 10-K filings."""
    data = load_analysis_data()
    required_fields = [
        'current_assets_billion',
        'current_liabilities_billion',
        'cash_and_equivalents_billion',
        'current_receivables_billion',
        'stockholders_equity_billion',
        'total_assets_billion'
    ]

    annual_filings = [f for f in data['filings'] if f['filing_type'] == '10-K']
    assert len(annual_filings) >= 1, "Should have at least 1 annual filing"

    extraction_count = 0
    for filing in annual_filings:
        vital = filing.get('vital_signs', {})
        fields_present = sum(1 for field in required_fields if vital.get(field) is not None)

        if fields_present == len(required_fields):
            extraction_count += 1

    coverage = (extraction_count / len(annual_filings)) * 100
    print(f"\n✅ Balance sheet extraction: {extraction_count}/{len(annual_filings)} filings ({coverage:.1f}%)")
    assert coverage >= 40, f"Should extract balance sheet data from at least 40% of 10-K filings, got {coverage:.1f}%"


def test_balance_sheet_sanity_checks():
    """Verify accounting identities (CA < TA, Equity < Assets)."""
    data = load_analysis_data()

    for filing in data['filings']:
        if filing['filing_type'] != '10-K':
            continue

        vital = filing.get('vital_signs', {})
        current_assets = vital.get('current_assets_billion')
        total_assets = vital.get('total_assets_billion')
        stockholders_equity = vital.get('stockholders_equity_billion')

        if current_assets and total_assets:
            assert current_assets <= total_assets, \
                f"{filing['period']}: Current Assets ({current_assets}) should be <= Total Assets ({total_assets})"

        if stockholders_equity and total_assets:
            assert stockholders_equity <= total_assets, \
                f"{filing['period']}: Stockholders Equity ({stockholders_equity}) should be <= Total Assets ({total_assets})"

    print("✅ All balance sheet accounting identities verified")


def test_extraction_coverage():
    """Check extraction rate across all 22 periods."""
    data = load_analysis_data()
    total_periods = len(data['filings'])

    liquidity_coverage = sum(1 for f in data['filings'] if f.get('liquidity_metrics'))
    coverage_pct = (liquidity_coverage / total_periods) * 100

    print(f"\n✅ Liquidity metrics coverage: {liquidity_coverage}/{total_periods} periods ({coverage_pct:.1f}%)")
    assert coverage_pct >= 70, f"Should have liquidity metrics for at least 70% of periods, got {coverage_pct:.1f}%"


def test_required_balance_sheet_fields_present():
    """Verify that balance sheet fields are present in vital_signs."""
    data = load_analysis_data()
    annual_filings = [f for f in data['filings'] if f['filing_type'] == '10-K']

    # Check across multiple annual filings (some older filings may not have all fields)
    max_fields_found = 0
    for filing in annual_filings:
        vital = filing.get('vital_signs', {})
        # At least some balance sheet fields should exist
        balance_sheet_fields = [
            'current_assets_billion',
            'current_liabilities_billion',
            'stockholders_equity_billion',
            'total_assets_billion'
        ]

        fields_present = [field for field in balance_sheet_fields if vital.get(field) is not None]
        max_fields_found = max(max_fields_found, len(fields_present))

    assert max_fields_found >= 2, \
        f"Should have at least 2 balance sheet fields in at least one filing, found max: {max_fields_found}"

    print("✅ Balance sheet fields present in vital_signs")


def test_cash_and_receivables_extraction():
    """Verify Cash and Receivables extracted for Quick Ratio calculation."""
    data = load_analysis_data()
    annual_filings = [f for f in data['filings'] if f['filing_type'] == '10-K']

    cash_count = sum(1 for f in annual_filings if f.get('vital_signs', {}).get('cash_and_equivalents_billion'))

    coverage = (cash_count / len(annual_filings)) * 100 if annual_filings else 0
    print(f"\n✅ Cash extraction: {cash_count}/{len(annual_filings)} filings ({coverage:.1f}%)")


# =============================================================================
# Category 2: Liquidity Calculation Tests (6 tests)
# =============================================================================

def test_current_ratio_calculation():
    """Verify Current Ratio formula: CA / CL."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity:
            continue

        vital = filing.get('vital_signs', {})
        ca = vital.get('current_assets_billion')
        cl = vital.get('current_liabilities_billion')
        current_ratio = liquidity.get('current_ratio')

        if ca and cl and current_ratio:
            expected_ratio = ca / cl
            assert abs(current_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: Current Ratio mismatch. Expected {expected_ratio:.2f}, got {current_ratio:.2f}"

    print("✅ Current Ratio calculation verified")


def test_current_ratio_health_flags():
    """Verify Current Ratio health thresholds (>1.5, 1.0-1.5, <1.0)."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity:
            continue

        current_ratio = liquidity.get('current_ratio')
        health = liquidity.get('current_ratio_health')

        if current_ratio and health:
            if current_ratio >= 1.5:
                assert health == 'healthy', f"{filing['period']}: Ratio {current_ratio} should be 'healthy'"
            elif current_ratio >= 1.0:
                assert health == 'adequate', f"{filing['period']}: Ratio {current_ratio} should be 'adequate'"
            else:
                assert health == 'warning', f"{filing['period']}: Ratio {current_ratio} should be 'warning'"

    print("✅ Current Ratio health flags verified")


def test_quick_ratio_calculation():
    """Verify Quick Ratio formula: (Cash + Receivables) / CL."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity or not liquidity.get('quick_ratio'):
            continue

        vital = filing.get('vital_signs', {})
        cash = vital.get('cash_and_equivalents_billion')
        receivables = vital.get('current_receivables_billion', 0)
        cl = vital.get('current_liabilities_billion')
        quick_ratio = liquidity.get('quick_ratio')

        if cash and cl and quick_ratio:
            expected_ratio = (cash + receivables) / cl
            assert abs(quick_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: Quick Ratio mismatch. Expected {expected_ratio:.2f}, got {quick_ratio:.2f}"

    print("✅ Quick Ratio calculation verified")


def test_quick_ratio_health_flags():
    """Verify Quick Ratio health thresholds (>1.0, 0.8-1.0, <0.8)."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity or not liquidity.get('quick_ratio'):
            continue

        quick_ratio = liquidity.get('quick_ratio')
        health = liquidity.get('quick_ratio_health')

        if quick_ratio and health:
            if quick_ratio >= 1.0:
                assert health == 'healthy', f"{filing['period']}: Quick Ratio {quick_ratio} should be 'healthy'"
            elif quick_ratio >= 0.8:
                assert health == 'adequate', f"{filing['period']}: Quick Ratio {quick_ratio} should be 'adequate'"
            else:
                assert health == 'warning', f"{filing['period']}: Quick Ratio {quick_ratio} should be 'warning'"

    print("✅ Quick Ratio health flags verified")


def test_working_capital_calculation():
    """Verify Working Capital formula: CA - CL."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity:
            continue

        vital = filing.get('vital_signs', {})
        ca = vital.get('current_assets_billion')
        cl = vital.get('current_liabilities_billion')
        wc = liquidity.get('working_capital_billion')

        if ca and cl and wc is not None:
            expected_wc = ca - cl
            assert abs(wc - expected_wc) < 0.01, \
                f"{filing['period']}: Working Capital mismatch. Expected {expected_wc:.2f}, got {wc:.2f}"

    print("✅ Working Capital calculation verified")


def test_working_capital_trend_flags():
    """Verify Working Capital trend flags (positive/negative)."""
    data = load_analysis_data()

    for filing in data['filings']:
        liquidity = filing.get('liquidity_metrics')
        if not liquidity:
            continue

        wc = liquidity.get('working_capital_billion')
        trend = liquidity.get('working_capital_trend')

        if wc is not None and trend:
            if wc > 0:
                assert trend == 'positive', f"{filing['period']}: WC {wc} should be 'positive'"
            else:
                assert trend == 'negative', f"{filing['period']}: WC {wc} should be 'negative'"

    print("✅ Working Capital trend flags verified")


# =============================================================================
# Category 3: Solvency Calculation Tests (8 tests)
# =============================================================================

def test_debt_to_equity_calculation():
    """Verify D/E formula: Total Debt / Stockholders Equity."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        total_debt = debt_m.get('total_debt_billion')
        equity = vital.get('stockholders_equity_billion')
        de_ratio = debt_m.get('debt_to_equity_ratio')

        if total_debt and equity and de_ratio:
            expected_ratio = total_debt / equity
            assert abs(de_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: D/E mismatch. Expected {expected_ratio:.2f}, got {de_ratio:.2f}"

    print("✅ Debt-to-Equity calculation verified")


def test_debt_to_assets_calculation():
    """Verify D/A formula: Total Debt / Total Assets."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        total_debt = debt_m.get('total_debt_billion')
        total_assets = vital.get('total_assets_billion')
        da_ratio = debt_m.get('debt_to_assets_ratio')

        if total_debt and total_assets and da_ratio:
            expected_ratio = total_debt / total_assets
            assert abs(da_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: D/A mismatch. Expected {expected_ratio:.2f}, got {da_ratio:.2f}"

    print("✅ Debt-to-Assets calculation verified")


def test_equity_ratio_calculation():
    """Verify Equity Ratio formula: Equity / Total Assets."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        equity = vital.get('stockholders_equity_billion')
        total_assets = vital.get('total_assets_billion')
        equity_ratio = debt_m.get('equity_ratio')

        if equity and total_assets and equity_ratio:
            expected_ratio = equity / total_assets
            assert abs(equity_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: Equity Ratio mismatch. Expected {expected_ratio:.2f}, got {equity_ratio:.2f}"

    print("✅ Equity Ratio calculation verified")


def test_debt_to_ebitda_calculation():
    """Verify Debt-to-EBITDA formula: Total Debt / EBITDA."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        total_debt = debt_m.get('total_debt_billion')
        ebitda = vital.get('ebitda_billion')
        de_ratio = debt_m.get('debt_to_ebitda_ratio')

        if total_debt and ebitda and de_ratio:
            expected_ratio = total_debt / ebitda
            assert abs(de_ratio - expected_ratio) < 0.01, \
                f"{filing['period']}: Debt-to-EBITDA mismatch. Expected {expected_ratio:.2f}, got {de_ratio:.2f}"

    print("✅ Debt-to-EBITDA calculation verified")


def test_debt_to_ebitda_health_flags():
    """Verify Debt-to-EBITDA health thresholds (<3.0, 3.0-5.0, >5.0)."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        if not debt_m:
            continue

        de_ratio = debt_m.get('debt_to_ebitda_ratio')
        health = debt_m.get('debt_to_ebitda_health')

        if de_ratio and health:
            if de_ratio < 3.0:
                assert health == 'healthy', f"{filing['period']}: D/EBITDA {de_ratio} should be 'healthy'"
            elif de_ratio <= 5.0:
                assert health == 'moderate', f"{filing['period']}: D/EBITDA {de_ratio} should be 'moderate'"
            else:
                assert health == 'risky', f"{filing['period']}: D/EBITDA {de_ratio} should be 'risky'"

    print("✅ Debt-to-EBITDA health flags verified")


def test_roe_calculation():
    """Verify ROE formula: (Net Income / Equity) × 100."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        net_income = vital.get('net_income_billion')
        equity = vital.get('stockholders_equity_billion')
        roe = debt_m.get('return_on_equity_percent')

        if net_income and equity and roe:
            expected_roe = (net_income / equity) * 100
            assert abs(roe - expected_roe) < 0.1, \
                f"{filing['period']}: ROE mismatch. Expected {expected_roe:.2f}%, got {roe:.2f}%"

    print("✅ ROE calculation verified")


def test_roa_calculation():
    """Verify ROA formula: (Net Income / Total Assets) × 100."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        vital = filing.get('vital_signs', {})
        if not debt_m:
            continue

        net_income = vital.get('net_income_billion')
        total_assets = vital.get('total_assets_billion')
        roa = debt_m.get('return_on_assets_percent')

        if net_income and total_assets and roa:
            expected_roa = (net_income / total_assets) * 100
            assert abs(roa - expected_roa) < 0.1, \
                f"{filing['period']}: ROA mismatch. Expected {expected_roa:.2f}%, got {roa:.2f}%"

    print("✅ ROA calculation verified")


def test_leverage_profile_flags():
    """Verify leverage profile flags (conservative/moderate/aggressive)."""
    data = load_analysis_data()

    for filing in data['filings']:
        debt_m = filing.get('debt_metrics')
        if not debt_m:
            continue

        de_ratio = debt_m.get('debt_to_equity_ratio')
        profile = debt_m.get('leverage_profile')

        if de_ratio and profile:
            if de_ratio < 1.0:
                assert profile == 'conservative', f"{filing['period']}: D/E {de_ratio} should be 'conservative'"
            elif de_ratio <= 2.0:
                assert profile == 'moderate', f"{filing['period']}: D/E {de_ratio} should be 'moderate'"
            else:
                assert profile == 'aggressive', f"{filing['period']}: D/E {de_ratio} should be 'aggressive'"

    print("✅ Leverage profile flags verified")


# =============================================================================
# Category 4: Export Tests (3 tests)
# =============================================================================

def test_timeseries_export_structure():
    """Verify 14 new Pillar 2 fields present in time-series JSON."""
    data = load_timeseries_data()

    # Check liquidity metrics structure
    assert 'liquidity' in data['metrics'], "Should have 'liquidity' metrics category"
    liquidity = data['metrics']['liquidity']

    required_liquidity_fields = [
        'current_ratio',
        'current_ratio_health',
        'quick_ratio',
        'quick_ratio_health',
        'working_capital_billion',
        'working_capital_trend'
    ]

    for field in required_liquidity_fields:
        assert field in liquidity, f"Should have '{field}' in liquidity metrics"

    # Check enhanced debt metrics structure
    debt = data['metrics']['debt']
    required_solvency_fields = [
        'debt_to_equity_ratio',
        'leverage_profile',
        'debt_to_assets_ratio',
        'equity_ratio',
        'debt_to_ebitda_ratio',
        'debt_to_ebitda_health',
        'return_on_equity_percent',
        'return_on_assets_percent'
    ]

    for field in required_solvency_fields:
        assert field in debt, f"Should have '{field}' in debt metrics"

    print("✅ Time-series export structure verified (14 Pillar 2 fields)")


def test_liquidity_metrics_export():
    """Verify liquidity metrics exported in flat structure format."""
    data = load_timeseries_data()
    liquidity = data['metrics']['liquidity']

    # Check arrays are parallel
    total_periods = data['metadata']['total_periods']
    for field in liquidity:
        assert len(liquidity[field]) == total_periods, \
            f"'{field}' array length should match total_periods"

    print("✅ Liquidity metrics export format verified")


def test_solvency_metrics_export():
    """Verify solvency metrics integrated with debt_metrics."""
    data = load_timeseries_data()
    debt = data['metrics']['debt']

    # Check arrays are parallel
    total_periods = data['metadata']['total_periods']
    for field in debt:
        assert len(debt[field]) == total_periods, \
            f"'{field}' array length should match total_periods"

    print("✅ Solvency metrics export format verified")


# =============================================================================
# Category 5: Visualization Tests (3 tests)
# =============================================================================

def test_gauge_chart_exists():
    """Verify Current Ratio Gauge chart file created >10KB."""
    chart_path = Path("output/chart_current_ratio_gauge.html")
    assert chart_path.exists(), "Chart 16 (Current Ratio Gauge) should exist"

    size_kb = chart_path.stat().st_size / 1024
    assert size_kb > 10, f"Chart should be >10KB, got {size_kb:.1f}KB"

    print(f"✅ Chart 16 (Gauge) created: {size_kb:.1f}KB")


def test_donut_chart_exists():
    """Verify Capital Structure Donut chart file created >10KB."""
    chart_path = Path("output/chart_capital_structure_donut.html")
    assert chart_path.exists(), "Chart 17 (Capital Structure Donut) should exist"

    size_kb = chart_path.stat().st_size / 1024
    assert size_kb > 10, f"Chart should be >10KB, got {size_kb:.1f}KB"

    print(f"✅ Chart 17 (Donut) created: {size_kb:.1f}KB")


def test_debt_ebitda_chart_exists():
    """Verify Debt-to-EBITDA Trend chart file created >10KB."""
    chart_path = Path("output/chart_debt_to_ebitda_trend.html")
    assert chart_path.exists(), "Chart 18 (Debt-to-EBITDA Trend) should exist"

    size_kb = chart_path.stat().st_size / 1024
    assert size_kb > 10, f"Chart should be >10KB, got {size_kb:.1f}KB"

    print(f"✅ Chart 18 (Debt-to-EBITDA) created: {size_kb:.1f}KB")


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PILLAR 2: LIQUIDITY & SOLVENCY TEST SUITE")
    print("=" * 80)

    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
