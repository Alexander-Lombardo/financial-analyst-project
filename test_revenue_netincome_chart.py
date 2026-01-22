"""Quick test script for revenue & net income chart only."""
import json
from pathlib import Path
from visualize_data import create_revenue_netincome_longterm_chart

def load_timeseries_data(filepath: str = "output/target_timeseries.json"):
    """Load time-series JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    print("📊 Testing Revenue & Net Income Long-Term Trajectory chart...")

    # Check if data exists
    timeseries_path = Path("output/target_timeseries.json")
    if not timeseries_path.exists():
        print("❌ Error: output/target_timeseries.json not found")
        return

    # Load data
    data = load_timeseries_data()
    print(f"   Loaded {data['metadata']['total_periods']} periods")

    # Create revenue & net income chart
    create_revenue_netincome_longterm_chart(data)

    print("\n✅ Revenue & Net Income chart created!")
    print("   File: output/chart_revenue_netincome_longterm.html")

if __name__ == "__main__":
    main()
