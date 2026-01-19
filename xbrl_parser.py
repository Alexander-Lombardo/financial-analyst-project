"""
Simplified XBRL Parser for Target Corporation Filings
=====================================================
Extracts financial data directly from XBRL inline tags.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from decimal import Decimal


class TargetXBRLParser:
    """Parse Target SEC filings in XBRL format."""

    # Map GAAP taxonomy to our metrics
    GAAP_MAPPINGS = {
        # Income Statement
        'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': 'revenue',
        'us-gaap:Revenues': 'revenue',
        'us-gaap:CostOfGoodsAndServicesSold': 'cost_of_sales',
        'us-gaap:CostOfRevenue': 'cost_of_sales',
        'us-gaap:GrossProfit': 'gross_profit',
        'us-gaap:OperatingIncomeLoss': 'operating_income',
        'us-gaap:SellingGeneralAndAdministrativeExpense': 'sga_expense',

        # Balance Sheet
        'us-gaap:InventoryNet': 'inventory',
        'us-gaap:CashAndCashEquivalentsAtCarryingValue': 'cash',
        'us-gaap:Assets': 'total_assets',

        # Shares
        'dei:EntityCommonStockSharesOutstanding': 'shares_outstanding',
    }

    def __init__(self, data_dir: str):
        """Initialize parser with data directory."""
        self.data_dir = Path(data_dir)
        self.results = []

    def parse_all_filings(self) -> List[Dict]:
        """Parse all Target filings in order."""
        filings = [
            ("10-K FY2024", "0000027419-25-000018-xbrl/tgt-20250201.htm"),
            ("Q1 2025", "0000027419-25-000101-xbrl/tgt-20250503.htm"),
            ("Q2 2025", "tgt-20250802.htm"),
            ("Q3 2025", "tgt-20251101.htm"),
        ]

        baseline = None

        for period, filename in filings:
            filepath = self.data_dir / filename

            if not filepath.exists():
                print(f"⚠️  Warning: {filename} not found, skipping...")
                continue

            print(f"\n{'='*60}")
            print(f"📊 Parsing: {period}")
            print(f"{'='*60}")

            result = self.parse_filing(filepath, period)

            # Set baseline and compare
            if period == "10-K FY2024":
                baseline = result
            elif baseline:
                result = self.compare_to_baseline(result, baseline)

            self.results.append(result)
            self.print_result(result)

        return self.results

    def parse_filing(self, filepath: Path, period: str) -> Dict:
        """Parse a single XBRL filing."""
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Extract all XBRL numeric data
        data = {}

        # Find all numeric fractions
        for tag in soup.find_all('ix:nonfraction'):
            gaap_name = tag.get('name', '')
            value_text = tag.get_text().strip()

            # Map to our metric names
            if gaap_name in self.GAAP_MAPPINGS:
                metric_name = self.GAAP_MAPPINGS[gaap_name]

                # Parse numeric value
                value = self._parse_number(value_text)

                # Store the most recent period's value
                # (XBRL files contain multiple periods)
                if metric_name not in data or value is not None:
                    # Get context to determine which period this is
                    context_ref = tag.get('contextref', '')

                    # Store with context info
                    if metric_name not in data:
                        data[metric_name] = []
                    data[metric_name].append({
                        'value': value,
                        'context': context_ref,
                        'text': value_text
                    })

        # Pick the most recent values (usually first in list)
        clean_data = {}
        for key, values in data.items():
            if values:
                # Take first non-None value
                for v in values:
                    if v['value'] is not None:
                        clean_data[key] = v['value']
                        break

        # Calculate metrics
        vital_signs = self._calculate_vital_signs(clean_data)

        # Extract comparable sales from text
        comp_sales = self._extract_comp_sales_from_text(soup)

        # Extract risk flags
        risk_flags = self._extract_risk_flags_from_text(soup)

        return {
            "period": period,
            "filing_type": "10-K" if "10-K" in period else "10-Q",
            "vital_signs": vital_signs,
            "comparable_sales": comp_sales,
            "risk_flags": risk_flags,
            "raw_data": clean_data
        }

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from XBRL text."""
        if not text:
            return None

        # Remove formatting
        text = text.replace(',', '').replace('$', '').strip()

        # Handle parentheses (negative)
        is_negative = False
        if text.startswith('(') and text.endswith(')'):
            is_negative = True
            text = text[1:-1]

        # Handle dashes (zero or N/A)
        if text in ['-', '—', 'N/A', '']:
            return None

        try:
            value = float(text)
            return -value if is_negative else value
        except ValueError:
            return None

    def _calculate_vital_signs(self, data: Dict) -> Dict:
        """Calculate vital signs from raw data."""
        vital_signs = {}

        # Revenue (in millions, convert to billions)
        if 'revenue' in data:
            vital_signs['net_sales_billion'] = round(data['revenue'] / 1000, 2)

        # Cost of Sales
        cost_of_sales = data.get('cost_of_sales')
        revenue = data.get('revenue')

        # Operating Income
        if 'operating_income' in data:
            vital_signs['operating_income_billion'] = round(data['operating_income'] / 1000, 2)

        # Calculate Gross Margin %
        if revenue and cost_of_sales:
            gross_profit = revenue - cost_of_sales
            gross_margin_pct = (gross_profit / revenue) * 100
            vital_signs['gross_margin_percent'] = round(gross_margin_pct, 2)

        # Calculate Operating Margin %
        if revenue and 'operating_income' in data:
            operating_margin_pct = (data['operating_income'] / revenue) * 100
            vital_signs['operating_margin_percent'] = round(operating_margin_pct, 2)

        # Inventory (in millions, convert to billions)
        if 'inventory' in data:
            vital_signs['inventory_billion'] = round(data['inventory'] / 1000, 2)

        return vital_signs

    def _extract_comp_sales_from_text(self, soup: BeautifulSoup) -> Dict:
        """Extract comparable sales from MD&A text."""
        comp_sales = {}

        # Get all text
        text = soup.get_text()

        # Look for comparable sales patterns
        patterns = {
            'total_change_percent': r'comparable\s+sales\s+(?:increased|decreased|grew)\s+([\d.]+)%',
            'store_change_percent': r'store(?:-originated)?\s+comparable\s+sales\s+(?:increased|decreased|grew)\s+([\d.]+)%',
            'digital_change_percent': r'digitally\s+originated\s+comparable\s+sales\s+(?:increased|grew)\s+([\d.]+)%',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                # Check if it's a decrease
                if 'decreased' in match.group(0).lower():
                    value = -value
                comp_sales[key] = value

        return comp_sales

    def _extract_risk_flags_from_text(self, soup: BeautifulSoup) -> List[str]:
        """Extract risk flags from filing text."""
        flags = []
        text = soup.get_text().lower()

        # Check for shrink/theft
        if 'shrink' in text or 'inventory shortage' in text:
            # Try to extract basis point impact
            bp_match = re.search(r'(\d+)\s*basis\s+points?', text)
            if bp_match:
                flags.append(f"Shrink reduced gross margin by {bp_match.group(1)} basis points")
            else:
                flags.append("Shrink/theft mentioned in filing")

        # Check for markdown activity
        if 'markdown' in text or 'promotional' in text and 'increased' in text:
            flags.append("Increased markdown/promotional activity noted")

        # Check for margin pressure
        if 'margin pressure' in text or 'margin compression' in text:
            flags.append("Margin pressure mentioned")

        return flags

    def compare_to_baseline(self, current: Dict, baseline: Dict) -> Dict:
        """Compare current quarter to baseline."""
        current_vital = current['vital_signs']
        baseline_vital = baseline['vital_signs']

        comparison = {}

        # Compare operating margin
        if 'operating_margin_percent' in current_vital and 'operating_margin_percent' in baseline_vital:
            current_om = current_vital['operating_margin_percent']
            baseline_om = baseline_vital['operating_margin_percent']
            diff = current_om - baseline_om

            comparison['operating_margin_change'] = round(diff, 2)
            comparison['operating_margin_trend'] = "improving" if diff > 0 else "declining"

        # Compare gross margin
        if 'gross_margin_percent' in current_vital and 'gross_margin_percent' in baseline_vital:
            current_gm = current_vital['gross_margin_percent']
            baseline_gm = baseline_vital['gross_margin_percent']
            diff = current_gm - baseline_gm

            comparison['gross_margin_change'] = round(diff, 2)

            if diff < -0.5:  # More than 50 bps decline
                comparison['markdown_flag'] = "Potential inventory clearance/discounting"

        current['vital_signs']['vs_baseline'] = comparison
        return current

    def print_result(self, result: Dict):
        """Print formatted result."""
        print(f"\n📈 {result['period']} ({result['filing_type']})")
        print("-" * 60)

        vital = result['vital_signs']
        print("\n💰 Vital Signs:")
        if 'net_sales_billion' in vital:
            print(f"   Net Sales: ${vital['net_sales_billion']:.2f}B")
        if 'gross_margin_percent' in vital:
            print(f"   Gross Margin: {vital['gross_margin_percent']:.2f}%")
        if 'operating_income_billion' in vital:
            print(f"   Operating Income: ${vital['operating_income_billion']:.2f}B")
        if 'operating_margin_percent' in vital:
            print(f"   Operating Margin: {vital['operating_margin_percent']:.2f}%")
        if 'inventory_billion' in vital:
            print(f"   Inventory: ${vital['inventory_billion']:.2f}B")

        if 'vs_baseline' in vital and vital['vs_baseline']:
            print("\n📊 vs Baseline:")
            for key, value in vital['vs_baseline'].items():
                print(f"   {key}: {value}")

        comp = result.get('comparable_sales', {})
        if comp:
            print("\n🏪 Comparable Sales:")
            for key, value in comp.items():
                print(f"   {key}: {value:+.2f}%")

        if result.get('risk_flags'):
            print("\n⚠️  Risk Flags:")
            for flag in result['risk_flags']:
                print(f"   • {flag}")

    def export_json(self, output_path: str):
        """Export results to JSON."""
        # Remove raw_data for cleaner export
        clean_results = []
        for r in self.results:
            clean = r.copy()
            if 'raw_data' in clean:
                del clean['raw_data']
            clean_results.append(clean)

        with open(output_path, 'w') as f:
            json.dump(clean_results, f, indent=2)

        print(f"\n✅ Results exported to: {output_path}")


def main():
    """Main execution."""
    print("🎯 Target Corporation XBRL Parser")
    print("=" * 60)

    parser = TargetXBRLParser("data/Target 10Q")
    results = parser.parse_all_filings()

    print("\n" + "=" * 60)
    print("📤 Exporting Results...")
    print("=" * 60)

    parser.export_json("output/target_analysis.json")

    print(f"\n✅ Analysis complete!")
    print(f"   Total filings analyzed: {len(results)}")


if __name__ == "__main__":
    main()
