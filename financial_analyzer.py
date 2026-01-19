"""
Target Corporation Financial Analyzer
=====================================
A comprehensive tool to analyze Target's 10-K and 10-Q filings.

Three-Phase Analysis:
1. Phase 1: Extract baseline "Vital Signs" from 10-K
2. Phase 2: Compare quarterly trends from 10-Qs against baseline
3. Phase 3: Output structured JSON for each period
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from decimal import Decimal
from sec_data_fetcher import SECDataFetcher


class TargetFinancialAnalyzer:
    """Analyzes Target Corporation SEC filings for key financial metrics."""

    def __init__(self, data_dir: str, auto_download: bool = False,
                 user_name: str = None, user_email: str = None):
        """
        Initialize analyzer with data directory.

        Args:
            data_dir: Path to directory containing Target 10-Q/10-K files
            auto_download: Enable automatic SEC EDGAR filing downloads
            user_name: Your name (required if auto_download=True, for SEC User-Agent)
            user_email: Your email (required if auto_download=True, for SEC User-Agent)
        """
        self.data_dir = Path(data_dir)
        self.baseline = None
        self.results = []
        self.auto_download = auto_download
        self.fetcher = None

        if auto_download:
            if not user_name or not user_email:
                raise ValueError("User name and email required for SEC downloads")
            self.fetcher = SECDataFetcher(user_name, user_email, str(data_dir))

    def download_required_filings(self, ticker: str = "TGT",
                                  cik: str = "0000027419") -> bool:
        """
        Download 5 years of 10-Ks and 12 quarters of 10-Qs from SEC EDGAR.

        Args:
            ticker: Stock ticker symbol (default: "TGT")
            cik: Central Index Key (default: "0000027419")

        Returns:
            True if download successful, False otherwise
        """
        if not self.fetcher:
            print("⚠️  Auto-download not enabled. Skipping download.")
            return False

        print("📥 Downloading filings from SEC EDGAR...")
        try:
            metadata = self.fetcher.download_filings(ticker, cik, num_10k=5, num_10q=12)
            print(f"✅ Downloaded {len(metadata.get('10-K', []))} 10-Ks")
            print(f"✅ Downloaded {len(metadata.get('10-Q', []))} 10-Qs")
            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def analyze_all_filings(self) -> List[Dict]:
        """
        Process all filings in correct order:
        1. 2024 10-K (Baseline)
        2. Q1 2025 10-Q
        3. Q2 2025 10-Q
        4. Q3 2025 10-Q

        Returns:
            List of analysis results for each filing
        """
        # If auto-download enabled, fetch filings first
        if self.auto_download and self.fetcher:
            self.download_required_filings()

        # Get filing list (from fetcher if available, else use hardcoded list)
        if self.fetcher:
            filings = self.fetcher.get_filing_list()
            print(f"📁 Found {len(filings)} downloaded filings")
        else:
            # Fall back to original hardcoded list for backward compatibility
            filings = [
                ("10-K FY2024", "0000027419-25-000018-xbrl/tgt-20250201.htm"),
                ("Q1 2025", "0000027419-25-000101-xbrl/tgt-20250503.htm"),
                ("Q2 2025", "tgt-20250802.htm"),
                ("Q3 2025", "tgt-20251101.htm"),
            ]

        for period, filename in filings:
            filepath = self.data_dir / filename

            if not filepath.exists():
                print(f"⚠️  Warning: {filename} not found, skipping...")
                continue

            print(f"\n{'='*60}")
            print(f"📊 Analyzing: {period}")
            print(f"{'='*60}")

            # Determine filing type based on period label
            is_10k = period.startswith("FY") or period == "10-K FY2024"

            if is_10k:
                result = self.analyze_10k(filepath, period)
                self.baseline = result
            else:
                result = self.analyze_10q(filepath, period)

            self.results.append(result)
            self._print_summary(result)

        return self.results

    def analyze_10k(self, filepath: Path, period: str) -> Dict:
        """
        Phase 1: Extract baseline vital signs from 10-K.

        Args:
            filepath: Path to 10-K HTML file
            period: Period label (e.g., "10-K FY2024")

        Returns:
            Dictionary with vital signs and strategic insights
        """
        html_content = self._read_html(filepath)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract financial data
        vital_signs = self._extract_vital_signs(soup, is_annual=True)
        comp_sales = self._extract_comparable_sales(soup, is_annual=True)

        # Extract qualitative data
        strategic_promise = self._extract_strategic_promise(soup)

        return {
            "period": period,
            "filing_type": "10-K",
            "vital_signs": vital_signs,
            "comparable_sales": comp_sales,
            "strategic_promise": strategic_promise,
            "risk_flags": []
        }

    def analyze_10q(self, filepath: Path, period: str) -> Dict:
        """
        Phase 2: Extract quarterly data and compare to baseline.

        Args:
            filepath: Path to 10-Q HTML file
            period: Period label (e.g., "Q1 2025")

        Returns:
            Dictionary with quarterly metrics and trend analysis
        """
        html_content = self._read_html(filepath)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract financial data
        vital_signs = self._extract_vital_signs(soup, is_annual=False)
        comp_sales = self._extract_comparable_sales(soup, is_annual=False)

        # Extract risk flags
        risk_flags = self._extract_risk_flags(soup)

        # Compare to baseline if available
        if self.baseline:
            vital_signs['vs_baseline'] = self._compare_to_baseline(vital_signs)

        return {
            "period": period,
            "filing_type": "10-Q",
            "vital_signs": vital_signs,
            "comparable_sales": comp_sales,
            "risk_flags": risk_flags
        }

    def _read_html(self, filepath: Path) -> str:
        """Read HTML file content."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_vital_signs(self, soup: BeautifulSoup, is_annual: bool) -> Dict:
        """
        Extract core financial metrics (Net Sales, Margins, Inventory).

        This is the most complex part - XBRL data is embedded in the HTML.
        """
        vital_signs = {}

        # Strategy: Look for specific XBRL tags
        # Net Sales: dei:EntityCommonStockSharesOutstanding or us-gaap:Revenues
        # We'll use regex patterns to find financial statement tables

        # Find Consolidated Statements of Operations
        operations_table = self._find_table_by_title(
            soup,
            r"Consolidated\s+Statements?\s+of\s+(Operations|Income)"
        )

        if operations_table:
            # Extract Net Sales (first line item usually)
            net_sales = self._extract_metric_from_table(
                operations_table,
                r"(Total\s+revenue|Net\s+sales)",
                column_index=0  # Most recent period
            )
            vital_signs['net_sales_billion'] = net_sales

            # Extract Cost of Sales
            cost_of_sales = self._extract_metric_from_table(
                operations_table,
                r"Cost\s+of\s+(sales|goods\s+sold)",
                column_index=0
            )

            # Extract Operating Income
            operating_income = self._extract_metric_from_table(
                operations_table,
                r"Operating\s+income",
                column_index=0
            )
            vital_signs['operating_income_billion'] = operating_income

            # Calculate margins
            if net_sales and cost_of_sales:
                gross_margin = ((net_sales - cost_of_sales) / net_sales) * 100
                vital_signs['gross_margin_percent'] = round(gross_margin, 2)

            if net_sales and operating_income:
                operating_margin = (operating_income / net_sales) * 100
                vital_signs['operating_margin_percent'] = round(operating_margin, 2)

        # Find Balance Sheet for Inventory
        balance_sheet = self._find_table_by_title(
            soup,
            r"Consolidated\s+Balance\s+Sheets?"
        )

        if balance_sheet:
            inventory = self._extract_metric_from_table(
                balance_sheet,
                r"Inventory|Inventories",
                column_index=0
            )
            vital_signs['inventory_billion'] = inventory

        return vital_signs

    def _extract_comparable_sales(self, soup: BeautifulSoup, is_annual: bool) -> Dict:
        """
        Extract comparable sales data from MD&A section.

        Looks for patterns like:
        - "Comparable sales increased 2.3%"
        - "Store-originated digital comparable sales grew 8.4%"
        """
        comp_sales = {}

        # Find MD&A section (Item 7 for 10-K, Item 2 for 10-Q)
        mda_section = self._find_mda_section(soup, is_annual)

        if mda_section:
            text = mda_section.get_text()

            # Pattern: "comparable sales increased/decreased X.X%"
            total_pattern = r"comparable\s+sales?\s+(?:increased|decreased|growth|decline)\s+(\d+\.?\d*)%?"
            match = re.search(total_pattern, text, re.IGNORECASE)
            if match:
                comp_sales['total_change_percent'] = float(match.group(1))

            # Store-originated
            store_pattern = r"store(?:-originated)?\s+(?:comparable\s+)?sales?\s+(?:increased|decreased|growth)\s+(\d+\.?\d*)%?"
            match = re.search(store_pattern, text, re.IGNORECASE)
            if match:
                comp_sales['store_change_percent'] = float(match.group(1))

            # Digital-originated
            digital_pattern = r"digit(?:al|ally)(?:-originated)?\s+(?:comparable\s+)?sales?\s+(?:increased|grew|growth)\s+(\d+\.?\d*)%?"
            match = re.search(digital_pattern, text, re.IGNORECASE)
            if match:
                comp_sales['digital_change_percent'] = float(match.group(1))

        return comp_sales

    def _extract_strategic_promise(self, soup: BeautifulSoup) -> Dict:
        """
        Extract CEO's top priorities and risk factors from 10-K.
        """
        strategic = {
            "top_priorities": [],
            "top_risks": []
        }

        # Find CEO letter or Business section
        # Look for forward-looking statements about priorities
        business_section = self._find_section_by_item(soup, "Item 1")

        if business_section:
            text = business_section.get_text()

            # Look for strategy keywords
            # This is heuristic - may need refinement based on actual content
            priority_keywords = [
                "strategic priority", "focus on", "initiative",
                "investment in", "expanding", "improving"
            ]

            # Extract sentences containing priority keywords
            sentences = text.split('.')
            for sentence in sentences[:100]:  # Check first 100 sentences
                for keyword in priority_keywords:
                    if keyword.lower() in sentence.lower():
                        strategic["top_priorities"].append(sentence.strip()[:200])
                        break

        # Find Risk Factors (Item 1A)
        risk_section = self._find_section_by_item(soup, "Item 1A")

        if risk_section:
            # Extract first 2-3 major risk headings
            risk_headers = risk_section.find_all(['h2', 'h3', 'b', 'strong'])
            for header in risk_headers[:3]:
                risk_text = header.get_text().strip()
                if len(risk_text) > 10 and len(risk_text) < 200:
                    strategic["top_risks"].append(risk_text)

        return strategic

    def _extract_risk_flags(self, soup: BeautifulSoup) -> List[str]:
        """
        Phase 2: Monitor for markdown and shrink mentions in quarterly filings.
        """
        flags = []

        # Find MD&A section
        mda_section = self._find_mda_section(soup, is_annual=False)

        if mda_section:
            text = mda_section.get_text()

            # Check for shrink mentions
            shrink_pattern = r"shrink|inventory\s+shortage|theft"
            if re.search(shrink_pattern, text, re.IGNORECASE):
                # Try to extract basis point impact
                bp_pattern = r"(\d+)\s*basis\s+points?"
                match = re.search(bp_pattern, text, re.IGNORECASE)
                if match:
                    flags.append(f"Shrink reduced gross margin by {match.group(1)} basis points")
                else:
                    flags.append("Shrink/theft mentioned in MD&A")

            # Check for markdown/clearance mentions
            markdown_pattern = r"markdown|clearance|promotional|discount"
            if re.search(markdown_pattern, text, re.IGNORECASE):
                flags.append("Increased markdown/promotional activity noted")

            # Check for margin pressure
            margin_pattern = r"margin\s+pressure|margin\s+decline|margin\s+compression"
            if re.search(margin_pattern, text, re.IGNORECASE):
                flags.append("Margin pressure mentioned")

        return flags

    def _compare_to_baseline(self, current_vital_signs: Dict) -> Dict:
        """Compare current quarter to baseline 10-K metrics."""
        comparison = {}

        if not self.baseline:
            return comparison

        baseline_vital = self.baseline['vital_signs']

        # Compare operating margin (key metric)
        if 'operating_margin_percent' in current_vital_signs and 'operating_margin_percent' in baseline_vital:
            baseline_margin = baseline_vital['operating_margin_percent']
            current_margin = current_vital_signs['operating_margin_percent']
            diff = current_margin - baseline_margin

            comparison['operating_margin_change'] = round(diff, 2)
            comparison['operating_margin_trend'] = "improving" if diff > 0 else "declining"

        # Compare gross margin
        if 'gross_margin_percent' in current_vital_signs and 'gross_margin_percent' in baseline_vital:
            baseline_gross = baseline_vital['gross_margin_percent']
            current_gross = current_vital_signs['gross_margin_percent']
            diff = current_gross - baseline_gross

            comparison['gross_margin_change'] = round(diff, 2)

            if diff < -0.5:  # More than 50 bps decline
                comparison['markdown_flag'] = "Potential inventory clearance/discounting"

        return comparison

    # Helper methods for HTML parsing

    def _find_table_by_title(self, soup: BeautifulSoup, title_pattern: str):
        """Find financial statement table by title pattern."""
        # Look for table preceded by matching heading
        headings = soup.find_all(['h1', 'h2', 'h3', 'p', 'div'])

        for heading in headings:
            if re.search(title_pattern, heading.get_text(), re.IGNORECASE):
                # Find next table element
                next_table = heading.find_next('table')
                if next_table:
                    return next_table

        return None

    def _extract_metric_from_table(self, table, row_pattern: str, column_index: int = 0) -> Optional[float]:
        """Extract numeric value from table by row label and column."""
        if not table:
            return None

        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # Check if first cell matches pattern
            first_cell_text = cells[0].get_text()
            if re.search(row_pattern, first_cell_text, re.IGNORECASE):
                # Extract value from specified column
                if len(cells) > column_index + 1:
                    value_text = cells[column_index + 1].get_text()
                    # Clean and convert to float (billions)
                    return self._parse_financial_value(value_text)

        return None

    def _parse_financial_value(self, text: str) -> Optional[float]:
        """
        Parse financial value from text.
        Handles formats like: "$24,523", "(1,234)", "24.5" (already in billions)
        """
        # Remove common formatting
        text = text.strip()
        text = text.replace('$', '').replace(',', '').replace(' ', '')

        # Handle parentheses (negative)
        is_negative = False
        if text.startswith('(') and text.endswith(')'):
            is_negative = True
            text = text[1:-1]

        # Try to extract number
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            value = float(match.group(1))

            # Convert to billions if value seems to be in millions
            # (values > 1000 are likely in millions)
            if value > 1000:
                value = value / 1000.0

            return -value if is_negative else value

        return None

    def _find_mda_section(self, soup: BeautifulSoup, is_annual: bool):
        """Find Management Discussion & Analysis section."""
        item_number = "Item 7" if is_annual else "Item 2"
        return self._find_section_by_item(soup, item_number)

    def _find_section_by_item(self, soup: BeautifulSoup, item_number: str):
        """Find section by Item number (e.g., 'Item 1A', 'Item 7')."""
        pattern = rf"{re.escape(item_number)}[.\s]"

        headings = soup.find_all(['h1', 'h2', 'h3', 'div', 'p'])
        for heading in headings:
            if re.search(pattern, heading.get_text(), re.IGNORECASE):
                # Return the heading's parent or next sibling section
                return heading.parent or heading

        return None

    def _print_summary(self, result: Dict):
        """Print formatted summary of analysis results."""
        print(f"\n📈 {result['period']} ({result['filing_type']})")
        print("-" * 60)

        vital = result['vital_signs']
        print("\n💰 Vital Signs:")
        if vital.get('net_sales_billion') is not None:
            print(f"   Net Sales: ${vital['net_sales_billion']:.2f}B")
        if vital.get('gross_margin_percent') is not None:
            print(f"   Gross Margin: {vital['gross_margin_percent']:.2f}%")
        if vital.get('operating_income_billion') is not None:
            print(f"   Operating Income: ${vital['operating_income_billion']:.2f}B")
        if vital.get('operating_margin_percent') is not None:
            print(f"   Operating Margin: {vital['operating_margin_percent']:.2f}%")
        if vital.get('inventory_billion') is not None:
            print(f"   Inventory: ${vital['inventory_billion']:.2f}B")

        if 'vs_baseline' in vital:
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

        if 'strategic_promise' in result:
            strat = result['strategic_promise']
            if strat.get('top_priorities'):
                print("\n🎯 Strategic Priorities:")
                for i, priority in enumerate(strat['top_priorities'][:3], 1):
                    print(f"   {i}. {priority[:100]}...")

    def export_json(self, output_path: str):
        """Export all results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✅ Results exported to: {output_path}")

    def export_summary_report(self, output_path: str):
        """Export executive summary report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TARGET CORPORATION - FINANCIAL ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        for result in self.results:
            report_lines.append(f"\n{result['period']} ({result['filing_type']})")
            report_lines.append("-" * 80)

            vital = result['vital_signs']
            report_lines.append("\nVital Signs:")
            for key, value in vital.items():
                if key != 'vs_baseline':
                    report_lines.append(f"  {key}: {value}")

            if 'vs_baseline' in vital:
                report_lines.append("\nTrend Analysis:")
                for key, value in vital['vs_baseline'].items():
                    report_lines.append(f"  {key}: {value}")

            if result.get('risk_flags'):
                report_lines.append("\nRisk Flags:")
                for flag in result['risk_flags']:
                    report_lines.append(f"  • {flag}")

            report_lines.append("")

        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))

        print(f"✅ Summary report exported to: {output_path}")


def main():
    """Main execution function."""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    print("🎯 Target Corporation Financial Analyzer")
    print("=" * 60)

    # Configuration
    data_dir = "data/Target 10Q"
    auto_download = True  # Enable automated downloads

    # Get credentials from environment
    user_name = os.getenv("SEC_USER_NAME")
    user_email = os.getenv("SEC_USER_EMAIL")

    if auto_download and (not user_name or not user_email):
        print("❌ Error: SEC credentials not configured")
        print("   Please create a .env file with SEC_USER_NAME and SEC_USER_EMAIL")
        print("   See .env.example for template")
        return

    # Initialize analyzer with download capability
    analyzer = TargetFinancialAnalyzer(
        data_dir=data_dir,
        auto_download=auto_download,
        user_name=user_name,
        user_email=user_email
    )

    # Analyze all filings (will auto-download if enabled)
    results = analyzer.analyze_all_filings()

    # Export results
    print("\n" + "=" * 60)
    print("📤 Exporting Results...")
    print("=" * 60)

    analyzer.export_json("output/target_analysis.json")
    analyzer.export_summary_report("output/target_summary.txt")

    print("\n✅ Analysis complete!")
    print(f"   Total filings analyzed: {len(results)}")
    print(f"   Output files created in: output/")


if __name__ == "__main__":
    main()
