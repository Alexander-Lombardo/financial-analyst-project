#!/usr/bin/env python3
"""
Quick test script to verify Kroger extraction with new fallback logic.
Uses already-downloaded filings to bypass network issues.
"""
import json
from pathlib import Path
import sys

# Import the analyzer
from peer_ccc_analyzer import PeerCCCAnalyzer

def main():
    analyzer = PeerCCCAnalyzer()

    # Path to Kroger's downloaded 10-K filings
    kroger_filings_dir = Path('data/peer_filings/sec-edgar-filings/KR/10-K')

    if not kroger_filings_dir.exists():
        print(f"❌ Error: Kroger filings directory not found: {kroger_filings_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Testing Kroger CCC Extraction with Fallback Logic")
    print("=" * 60)

    # Get all filing directories (sorted by name, which should be chronological)
    filing_dirs = sorted([d for d in kroger_filings_dir.iterdir() if d.is_dir()])

    print(f"\nFound {len(filing_dirs)} Kroger 10-K filings")

    kroger_data = {'ticker': 'KR', 'years': {}}

    for filing_dir in filing_dirs[-5:]:  # Process last 5 filings
        # Find the primary-document.html file
        html_files = list(filing_dir.glob('primary-document.html'))

        if not html_files:
            print(f"\n⚠️  Skipping {filing_dir.name}: No primary-document.html found")
            continue

        filepath = html_files[0]

        print(f"\n📄 Analyzing {filing_dir.name}...")

        # Extract period from filing directory name (accession number format: XXXX-YY-NNNNNN)
        # We'll extract fiscal year from the HTML file title instead
        html_content = analyzer._read_html(filepath)

        # Simple regex to extract fiscal year from title
        import re
        fy_match = re.search(r'(?:fiscal|year|ended).*?(\d{4})', html_content, re.IGNORECASE)
        if fy_match:
            fiscal_year = int(fy_match.group(1))
        else:
            # Fallback: guess from accession number year
            fiscal_year = 2020 + len(kroger_data['years'])

        period = f"FY{fiscal_year}"

        # Extract CCC data
        ccc_components = analyzer._extract_ccc_from_filing(filepath, fiscal_year)

        if ccc_components:
            kroger_data['years'][str(fiscal_year)] = ccc_components
            print(f"   ✅ {period}: DSI={ccc_components['dsi']:.1f}, DSO={ccc_components['dso']:.1f}, DPO={ccc_components['dpo']:.1f}, CCC={ccc_components['ccc']:.1f} days")
        else:
            print(f"   ❌ {period}: Extraction failed (incomplete data)")

    print("\n" + "=" * 60)
    print(f"✅ Kroger Extraction Complete: {len(kroger_data['years'])} years")
    print("=" * 60)

    # Display results
    if kroger_data['years']:
        print("\nKroger CCC Data:")
        for year in sorted(kroger_data['years'].keys()):
            data = kroger_data['years'][year]
            print(f"  FY{year}: DSI={data['dsi']:.1f}, DSO={data['dso']:.1f}, DPO={data['dpo']:.1f}, CCC={data['ccc']:.1f} days")

        # Save to JSON for inspection
        output_file = Path('output/kroger_test_results.json')
        with open(output_file, 'w') as f:
            json.dump(kroger_data, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print("\n❌ No Kroger data extracted")
        sys.exit(1)

if __name__ == "__main__":
    main()
