#!/usr/bin/env python3
"""
Target Financial Analyzer - Main Entry Point
=============================================

Run this script to:
1. Download SEC filings (10-K and 10-Q) from SEC EDGAR
2. Analyze financial data using XBRL parsing
3. Generate 24 interactive Plotly charts
4. Create a professional PowerPoint presentation

Usage:
    python run_analysis.py

Requirements:
    - Python 3.8+
    - Dependencies from requirements.txt
    - SEC credentials in .env file (see .env.example)
"""

import os
import sys
from pathlib import Path


def main():
    """Run the complete Target financial analysis pipeline."""

    print("=" * 60)
    print("   Target Financial Analyzer")
    print("   Automated SEC Filing Analysis & Visualization")
    print("=" * 60)
    print()

    # Check for .env file
    if not Path(".env").exists():
        print("ERROR: .env file not found")
        print()
        print("Please create a .env file with your SEC credentials:")
        print("  SEC_USER_NAME=Your Name")
        print("  SEC_USER_EMAIL=your.email@example.com")
        print()
        print("See .env.example for a template.")
        sys.exit(1)

    # Step 1: Run financial analysis
    print("STEP 1/3: Analyzing SEC Filings")
    print("-" * 40)
    from financial_analyzer import main as analyze
    analyze()
    print()

    # Step 2: Generate visualizations
    print("STEP 2/3: Generating Charts")
    print("-" * 40)
    from visualize_data import main as visualize
    visualize()
    print()

    # Step 3: Create PowerPoint presentation
    print("STEP 3/3: Creating PowerPoint Presentation")
    print("-" * 40)
    from create_presentation import create_target_presentation
    output_path = create_target_presentation()
    print()

    # Summary
    print("=" * 60)
    print("   Analysis Complete!")
    print("=" * 60)
    print()
    print("Output files:")
    print("  - output/Target_Financial_Analysis.pptx  (presentation)")
    print("  - output/chart_*.html                    (24 interactive charts)")
    print("  - output/target_timeseries.json          (time-series data)")
    print("  - output/target_analysis.json            (detailed analysis)")
    print()
    print("Next steps:")
    print("  1. Open output/Target_Financial_Analysis.pptx")
    print("  2. Browse interactive charts in output/ directory")
    print()


if __name__ == "__main__":
    main()
