"""
Test suite for Chart 15: EBITDA Bridge Waterfall
Validates D&A extraction and EBITDA calculations
"""
import json
import sys
from pathlib import Path


def test_da_extraction():
    """Test that D&A is extracted for all periods"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    da_values = data['metrics']['operating_expenses']['depreciation_amortization_billion']

    # Count non-null values
    valid_count = sum(1 for v in da_values if v is not None)
    total_count = len(da_values)

    print(f"\n📊 D&A Extraction Test:")
    print(f"   Valid D&A values: {valid_count}/{total_count} ({valid_count/total_count*100:.1f}%)")

    # Expect 100% coverage
    assert valid_count == total_count, f"D&A extraction incomplete: {valid_count}/{total_count}"
    print("   ✅ PASS: D&A extraction successful")

    # Display sample values
    print(f"\n   Sample D&A values:")
    for i, period in enumerate(data['periods'][-5:]):  # Last 5 periods
        idx = len(data['periods']) - 5 + i
        da_val = da_values[idx] if idx < len(da_values) else None
        print(f"     {period['period']}: ${da_val:.3f}B" if da_val else f"     {period['period']}: None")


def test_ebitda_calculation():
    """Test that EBITDA = Operating Income + D&A"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    # Derive Operating Income: OI = Revenue - COGS - SG&A - Other
    revenue = data['metrics']['revenue']['net_sales_billion']
    cogs = data['metrics']['operating_expenses']['cost_of_sales_billion']
    sga = data['metrics']['operating_expenses']['sga_expense_billion']
    other = data['metrics']['operating_expenses']['other_operating_expenses_billion']

    oi_values = []
    for i in range(len(revenue)):
        if all(v is not None for v in [revenue[i], cogs[i], sga[i], other[i]]):
            oi_values.append(revenue[i] - cogs[i] - sga[i] - other[i])
        else:
            oi_values.append(None)

    da_values = data['metrics']['operating_expenses']['depreciation_amortization_billion']
    ebitda_values = data['metrics']['operating_expenses']['ebitda_billion']

    print(f"\n📊 EBITDA Calculation Test:")

    errors = []
    for i in range(len(data['periods'])):
        period = data['periods'][i]['period']

        # Skip if any value is None
        if any(v is None for v in [oi_values[i], da_values[i], ebitda_values[i]]):
            print(f"   ⚠️  {period}: Skipping (missing data)")
            continue

        expected_ebitda = oi_values[i] + da_values[i]
        actual_ebitda = ebitda_values[i]

        # Allow 0.01B tolerance for rounding
        if abs(expected_ebitda - actual_ebitda) > 0.01:
            errors.append(f"   ⚠️  {period}: Expected ${expected_ebitda:.3f}B, got ${actual_ebitda:.3f}B")
        else:
            print(f"   ✅ {period}: ${actual_ebitda:.3f}B")

    if errors:
        print("\n❌ ERRORS:")
        for err in errors:
            print(err)
        sys.exit(1)

    print("   ✅ PASS: All EBITDA calculations correct")


def test_ebitda_range():
    """Test that EBITDA values are in reasonable range for Target"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    ebitda_values = data['metrics']['operating_expenses']['ebitda_billion']

    print(f"\n📊 EBITDA Range Test:")

    valid_values = [v for v in ebitda_values if v is not None]

    if not valid_values:
        print("   ❌ FAIL: No EBITDA values found")
        sys.exit(1)

    min_ebitda = min(valid_values)
    max_ebitda = max(valid_values)
    avg_ebitda = sum(valid_values) / len(valid_values)

    print(f"   EBITDA Range: ${min_ebitda:.2f}B - ${max_ebitda:.2f}B")
    print(f"   EBITDA Average: ${avg_ebitda:.2f}B")

    # Target's quarterly EBITDA should be in range $1-8B
    assert 0.5 <= min_ebitda <= 10, f"EBITDA min out of range: ${min_ebitda}B"
    assert 0.5 <= max_ebitda <= 15, f"EBITDA max out of range: ${max_ebitda}B"

    print("   ✅ PASS: EBITDA values in reasonable range")


def test_ebitda_margin():
    """Test that EBITDA margin is in reasonable range (5-15% for retail)"""
    with open('output/target_timeseries.json', 'r') as f:
        data = json.load(f)

    ebitda_margin = data['metrics']['operating_expenses']['ebitda_margin_percent']

    print(f"\n📊 EBITDA Margin Test:")

    valid_values = [v for v in ebitda_margin if v is not None]

    if not valid_values:
        print("   ❌ FAIL: No EBITDA margin values found")
        sys.exit(1)

    min_margin = min(valid_values)
    max_margin = max(valid_values)
    avg_margin = sum(valid_values) / len(valid_values)

    print(f"   EBITDA Margin Range: {min_margin:.2f}% - {max_margin:.2f}%")
    print(f"   EBITDA Margin Average: {avg_margin:.2f}%")

    # Retail industry typical EBITDA margin: 5-15%
    assert 3 <= min_margin <= 20, f"EBITDA margin min out of range: {min_margin}%"
    assert 3 <= max_margin <= 20, f"EBITDA margin max out of range: {max_margin}%"

    print("   ✅ PASS: EBITDA margins in reasonable range")


def test_chart_file_exists():
    """Test that chart HTML file was created"""
    chart_path = Path('output/chart_ebitda_bridge.html')

    print(f"\n📊 Chart File Test:")

    assert chart_path.exists(), "Chart 15 HTML file not found"

    # Check file size (should be > 10KB for valid Plotly chart)
    file_size = chart_path.stat().st_size
    assert file_size > 10000, f"Chart file too small: {file_size} bytes"

    print(f"   ✅ PASS: Chart file created ({file_size:,} bytes)")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST SUITE: Chart 15 - EBITDA Bridge Waterfall")
    print("=" * 60)

    test_da_extraction()
    test_ebitda_calculation()
    test_ebitda_range()
    test_ebitda_margin()
    test_chart_file_exists()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
