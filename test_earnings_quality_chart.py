"""Quick test script for earnings quality chart only."""
import json
from pathlib import Path
from visualize_data import create_earnings_quality_chart

def load_timeseries_data(filepath: str = "output/target_timeseries.json"):
    """Load time-series JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    print("📊 Testing earnings quality chart...")

    # Check if data exists
    timeseries_path = Path("output/target_timeseries.json")
    if not timeseries_path.exists():
        print("❌ Error: output/target_timeseries.json not found")
        return

    # Load data
    data = load_timeseries_data()
    print(f"   Loaded {data['metadata']['total_periods']} periods")

    # Check if net_income_billion exists
    if 'net_income_billion' in data['metrics']['cash_flows']:
        net_income_values = data['metrics']['cash_flows']['net_income_billion']
        non_null_count = sum(1 for v in net_income_values if v is not None)
        print(f"   Net income data: {non_null_count}/{len(net_income_values)} periods have values")
    else:
        print("❌ Error: net_income_billion not found in timeseries data")
        print("   Please run financial_analyzer.py first")
        return

    # Create earnings quality chart
    create_earnings_quality_chart(data)

    print("\n✅ Earnings quality chart created!")
    print("   File: output/chart_earnings_quality.html")

if __name__ == "__main__":
    main()
