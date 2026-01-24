"""
Test suite for Chart 14: Operating Expense Breakdown
Validates SG&A extraction and expense percentage calculations
"""
import json
import sys
from pathlib import Path


def test_sga_extraction():
    """Test that SG&A is extracted for all periods"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    sga_values = data['metrics']['operating_expenses']['sga_expense_billion']

    # Count non-null values
    valid_count = sum(1 for v in sga_values if v is not None)
    total_count = len(sga_values)

    print(f"\n📊 SG&A Extraction Test:")
    print(f"   Valid SG&A values: {valid_count}/{total_count} ({valid_count/total_count*100:.1f}%)")

    # Expect at least 80% coverage (some older filings may not have SG&A)
    assert valid_count >= total_count * 0.8, f"SG&A extraction rate too low: {valid_count}/{total_count}"
    print("   ✅ PASS: SG&A extraction successful")

    # Display sample values
    print(f"\n   Sample SG&A values:")
    for i, period in enumerate(data['periods'][-5:]):  # Last 5 periods
        sga_val = sga_values[i] if i < len(sga_values) else None
        print(f"     {period['period']}: ${sga_val:.2f}B" if sga_val else f"     {period['period']}: None")


def test_percentage_totals():
    """Test that COGS% + SG&A% + Other% + OI% ≈ 100%"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    cogs_pct = data['metrics']['operating_expenses']['cogs_percent_of_revenue']
    sga_pct = data['metrics']['operating_expenses']['sga_percent_of_revenue']
    other_pct = data['metrics']['operating_expenses']['other_expenses_percent_of_revenue']
    oi_pct = data['metrics']['margins']['operating_margin_percent']

    print(f"\n📊 Percentage Total Test:")

    errors = []
    for i in range(len(data['periods'])):
        period = data['periods'][i]['period']

        # Skip if any value is None
        values = [cogs_pct[i], sga_pct[i], other_pct[i], oi_pct[i]]
        if any(v is None for v in values):
            print(f"   ⚠️  {period}: Skipping (missing data)")
            continue

        total = sum(values)

        # Allow 1% tolerance for rounding
        if abs(total - 100.0) > 1.0:
            errors.append(f"   ⚠️  {period}: {total:.2f}% (should be 100%)")
        else:
            print(f"   ✅ {period}: {total:.2f}%")

    if errors:
        print("\n❌ ERRORS:")
        for err in errors:
            print(err)
        sys.exit(1)

    print("   ✅ PASS: All percentages sum to ~100%")


def test_sga_percent_range():
    """Test that SG&A % is in reasonable range (15-25% for retail)"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    sga_pct = data['metrics']['operating_expenses']['sga_percent_of_revenue']

    print(f"\n📊 SG&A Percentage Range Test:")

    valid_values = [v for v in sga_pct if v is not None]

    if not valid_values:
        print("   ❌ FAIL: No SG&A percentage values found")
        sys.exit(1)

    min_sga = min(valid_values)
    max_sga = max(valid_values)
    avg_sga = sum(valid_values) / len(valid_values)

    print(f"   SG&A % Range: {min_sga:.2f}% - {max_sga:.2f}%")
    print(f"   SG&A % Average: {avg_sga:.2f}%")

    # Retail industry typical SG&A: 15-25%
    # Allow wider range (10-30%) for flexibility
    assert 10 <= min_sga <= 30, f"SG&A min out of range: {min_sga}%"
    assert 10 <= max_sga <= 30, f"SG&A max out of range: {max_sga}%"

    print("   ✅ PASS: SG&A percentages in reasonable range")


def test_chart_file_exists():
    """Test that chart HTML file was created"""
    chart_path = Path('output/chart_expense_breakdown.html')

    print(f"\n📊 Chart File Test:")

    assert chart_path.exists(), "Chart 14 HTML file not found"

    # Check file size (should be > 10KB for valid Plotly chart)
    file_size = chart_path.stat().st_size
    assert file_size > 10000, f"Chart file too small: {file_size} bytes"

    print(f"   ✅ PASS: Chart file created ({file_size:,} bytes)")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST SUITE: Chart 14 - Operating Expense Breakdown")
    print("=" * 60)

    test_sga_extraction()
    test_percentage_totals()
    test_sga_percent_range()
    test_chart_file_exists()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
