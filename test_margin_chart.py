"""Quick test script for margin analysis chart only."""
import json
from pathlib import Path
from visualize_data import create_margin_analysis_chart

def load_timeseries_data(filepath: str = "output/target_timeseries.json"):
    """Load time-series JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    print("📊 Testing margin analysis chart...")

    # Check if data exists
    timeseries_path = Path("output/target_timeseries.json")
    if not timeseries_path.exists():
        print("❌ Error: output/target_timeseries.json not found")
        return

    # Load data
    data = load_timeseries_data()
    print(f"   Loaded {data['metadata']['total_periods']} periods")

    # Create margin analysis chart
    create_margin_analysis_chart(data)

    print("\n✅ Margin analysis chart created!")
    print("   File: output/chart_margin_analysis.html")

if __name__ == "__main__":
    main()
