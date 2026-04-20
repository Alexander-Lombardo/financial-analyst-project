#!/usr/bin/env python3
"""
Financial Analyzer - Main Entry Point
======================================

Runs the three-stage pipeline for a given company config:
1. Download and parse SEC filings; write analysis + timeseries JSON
2. Generate all 24 Plotly charts (HTML + PNG)
3. Build the PowerPoint deck

Usage:
    python run_analysis.py                          # uses config/target.yaml
    python run_analysis.py --config config/walmart.yaml
"""

import argparse
import sys
from pathlib import Path

from config_loader import CompanyConfig
from financial_analyzer import run_analysis as run_analysis_stage
from visualize_data import run_charts
from create_presentation import create_presentation


def main():
    parser = argparse.ArgumentParser(description="Run the full financial-analysis pipeline.")
    parser.add_argument("--config", default="config/target.yaml",
                        help="Path to company YAML config (default: config/target.yaml).")
    args = parser.parse_args()

    config = CompanyConfig.from_yaml(args.config)

    print("=" * 60)
    print(f"   {config.name} Financial Analyzer")
    print("   Automated SEC Filing Analysis & Visualization")
    print("=" * 60)
    print()

    if not Path(".env").exists():
        print("ERROR: .env file not found")
        print()
        print("Please create a .env file with your SEC credentials:")
        print("  SEC_USER_NAME=Your Name")
        print("  SEC_USER_EMAIL=your.email@example.com")
        sys.exit(1)

    # Stage 1: Analysis
    print("STEP 1/3: Analyzing SEC Filings")
    print("-" * 40)
    run_analysis_stage(config)
    print()

    # Stage 2: Charts
    print("STEP 2/3: Generating Charts")
    print("-" * 40)
    run_charts(config)
    print()

    # Stage 3: Deck
    print("STEP 3/3: Creating PowerPoint Presentation")
    print("-" * 40)
    output_path = create_presentation(config)
    print()

    print("=" * 60)
    print("   Analysis Complete!")
    print("=" * 60)
    print()
    print("Output files:")
    print(f"  - {output_path}  (presentation)")
    print(f"  - output/chart_*.html                    (24 interactive charts)")
    print(f"  - {config.output_path('timeseries.json')}  (time-series data)")
    print(f"  - {config.output_path('analysis.json')}    (detailed analysis)")


if __name__ == "__main__":
    main()
