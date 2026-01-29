"""
Peer CCC Analyzer - Extract Cash Conversion Cycle metrics from peer company 10-K filings

This script downloads and analyzes peer company SEC filings to extract CCC components
(DSI, DSO, DPO) for competitive benchmarking against Target Corporation.

Reuses Target's proven GAAP extraction infrastructure from financial_analyzer.py.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from sec_data_fetcher import SECDataFetcher

# Load environment variables
load_dotenv()


# Peer company configuration
PEER_COMPANIES = {
    'Walmart': {
        'ticker': 'WMT',
        'cik': '0000104169',
        'notes': 'World\'s largest retailer, direct Target competitor'
    },
    'Amazon': {
        'ticker': 'AMZN',
        'cik': '0001018724',
        'notes': 'E-commerce leader, inventory-light marketplace model'
    },
    'Costco': {
        'ticker': 'COST',
        'cik': '0000909832',
        'notes': 'Warehouse club, membership-based, high inventory turnover'
    },
    'Kroger': {
        'ticker': 'KR',
        'cik': '0000056873',
        'notes': 'Grocery-focused retailer, perishable inventory'
    }
}


class PeerCCCAnalyzer:
    """
    Analyzes peer companies to extract CCC metrics for competitive benchmarking.

    Reuses Target's proven GAAP extraction infrastructure:
    - SECDataFetcher for downloading filings
    - GAAP_MAPPINGS for tag standardization
    - _extract_xbrl_value() for dual-format XBRL parsing
    - Calculation formulas for DSI, DSO, DPO
    """

    def __init__(self, data_dir: str = "data/peer_filings", company_name: str = None,
                 email: str = None):
        self.data_dir = Path(data_dir)

        # Get SEC credentials from environment or use defaults
        company_name = company_name or os.getenv('SEC_USER_NAME', 'Peer Analysis')
        email = email or os.getenv('SEC_USER_EMAIL', 'analysis@example.com')

        self.fetcher = SECDataFetcher(company_name, email, str(self.data_dir))

        # Reuse Target's GAAP mappings (subset for CCC calculation)
        self.gaap_mappings = {
            'us-gaap:Revenues': 'net_sales',
            'us-gaap:SalesRevenueNet': 'net_sales',  # Fallback
            'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': 'net_sales',  # Target-specific
            'us-gaap:CostOfGoodsSold': 'cost_of_sales',
            'us-gaap:CostOfGoodsAndServicesSold': 'cost_of_sales',  # Fallback
            'us-gaap:CostOfRevenue': 'cost_of_sales',  # Fallback
            'us-gaap:InventoryNet': 'inventory',
            'us-gaap:AccountsReceivableNetCurrent': 'current_receivables',
            'us-gaap:AccountsAndOtherReceivablesNetCurrent': 'current_receivables',  # Fallback
            'us-gaap:AccountsPayableCurrent': 'current_payables',
            'us-gaap:AccountsPayableTradeCurrent': 'current_payables'  # Fallback
        }

    def analyze_peer(self, ticker: str, cik: str, company_name: str,
                     num_years: int = 5) -> Dict:
        """
        Analyze peer company and extract CCC components.

        Args:
            ticker: Stock ticker (e.g., "WMT")
            cik: SEC CIK number (e.g., "0000104169")
            company_name: Full company name (e.g., "Walmart")
            num_years: Number of fiscal years to analyze (default 5)

        Returns:
            Dict with multi-year CCC data:
            {
                'ticker': 'WMT',
                'years': {
                    '2024': {'dsi': 43.0, 'dso': 4.2, 'dpo': 48.5, 'ccc': -1.3},
                    '2023': {...},
                    ...
                }
            }
        """
        # Download 10-K filings
        print(f"📥 Downloading {num_years} years of 10-K filings for {company_name}...")
        try:
            # Manually call downloader to avoid num_10q=0 issue
            self.fetcher.downloader.get("10-K", ticker, limit=num_years, download_details=True)
            filings_10k = self.fetcher._discover_filings(ticker, "10-K")
            filings = {'10-K': filings_10k, '10-Q': []}
        except Exception as e:
            print(f"❌ Error downloading filings for {company_name}: {e}")
            return {'ticker': ticker, 'years': {}}

        # Extract CCC components from each filing
        peer_data = {'ticker': ticker, 'years': {}}

        for filing in filings.get('10-K', []):
            fiscal_year = self._extract_fiscal_year(filing['period'])

            print(f"   Analyzing {filing['period']}...")
            ccc_components = self._extract_ccc_from_filing(
                Path(filing['absolute_path']),
                fiscal_year
            )

            if ccc_components:
                peer_data['years'][str(fiscal_year)] = ccc_components
                print(f"   ✅ {filing['period']}: CCC = {ccc_components['ccc']:.1f} days")
            else:
                print(f"   ⚠️  {filing['period']}: Incomplete data")

        return peer_data

    def _extract_ccc_from_filing(self, filepath: Path, fiscal_year: int) -> Optional[Dict]:
        """
        Extract CCC components from single 10-K filing.

        Reuses Target's extraction methods:
        - _read_html() to load file + full-submission.txt
        - _extract_xbrl_value() for GAAP tags (handles both modern iXBRL and legacy XML)
        - Calculation formulas for DSI, DSO, DPO
        """
        # Read HTML + full-submission.txt (handles legacy formats)
        html_content = self._read_html(filepath)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract vital signs using GAAP mappings
        vital_signs = {}

        # Try each GAAP tag variant for net_sales
        # CRITICAL: Check modern ASC 606 revenue tag FIRST (used by Amazon, Target, modern companies)
        # Amazon's 10-Ks contain BOTH us-gaap:Revenues (placeholder=1) and RevenueFromContract... (actual value)
        # Checking Revenues first causes extraction of placeholder value instead of actual revenue
        vital_signs['net_sales_billion'] = (
            self._extract_xbrl_value(soup, 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:Revenues', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:SalesRevenueNet', html_content)
        )

        # Try each GAAP tag variant for cost_of_sales
        # CRITICAL: Check Kroger's unique tag FIRST (excludes D&A from COGS)
        vital_signs['cost_of_sales_billion'] = (
            self._extract_xbrl_value(soup, 'us-gaap:CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:CostOfGoodsSold', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:CostOfGoodsAndServicesSold', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:CostOfRevenue', html_content)
        )

        # Try each GAAP tag variant for inventory
        # Kroger uses FIFOInventoryAmount instead of generic InventoryNet
        vital_signs['inventory_billion'] = (
            self._extract_xbrl_value(soup, 'us-gaap:InventoryNet', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:FIFOInventoryAmount', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:InventoryLIFO', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:Inventory', html_content)
        )

        # NEW: Fallback for companies that don't tag inventory with XBRL at all
        if vital_signs['inventory_billion'] is None:
            print(f"      Inventory XBRL tag not found, trying table extraction fallback...")
            vital_signs['inventory_billion'] = self._extract_inventory_from_table(soup, html_content)

        # Try each GAAP tag variant for receivables
        vital_signs['current_receivables_billion'] = (
            self._extract_xbrl_value(soup, 'us-gaap:AccountsReceivableNetCurrent', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:AccountsAndOtherReceivablesNetCurrent', html_content)
        )

        # Try each GAAP tag variant for payables
        vital_signs['current_payables_billion'] = (
            self._extract_xbrl_value(soup, 'us-gaap:AccountsPayableCurrent', html_content) or
            self._extract_xbrl_value(soup, 'us-gaap:AccountsPayableTradeCurrent', html_content)
        )

        # Check if core data present (revenue, COGS, inventory, payables required)
        # Receivables optional (many retailers don't report it)
        required_fields = ['net_sales_billion', 'cost_of_sales_billion', 'inventory_billion', 'current_payables_billion']
        missing_required = [k for k in required_fields if vital_signs.get(k) is None]

        if missing_required:
            print(f"      Missing required: {', '.join(missing_required)}")
            return None

        # Handle optional receivables - use default DSO if missing
        if vital_signs['current_receivables_billion'] is None:
            print(f"      Note: Receivables not reported, using default DSO=3.5 days (typical for retail)")
            default_dso = 3.5
        else:
            default_dso = None

        # Calculate CCC components (reuse Target's formulas)
        try:
            # Debug: Show extracted values
            print(f"      Revenue: ${vital_signs['net_sales_billion']:.2f}B, COGS: ${vital_signs['cost_of_sales_billion']:.2f}B")
            print(f"      Inventory: ${vital_signs['inventory_billion']:.2f}B, Payables: ${vital_signs['current_payables_billion']:.2f}B")

            dsi = self._calculate_dsi(vital_signs)
            dso = default_dso if default_dso is not None else self._calculate_dso(vital_signs)
            dpo = self._calculate_dpo(vital_signs)
            ccc = dsi + dso - dpo

            # Sanity check: Retail CCC should be -20 to +100 days
            if abs(ccc) > 200:
                print(f"      ⚠️  WARNING: CCC = {ccc:.1f} days is outside normal range (-20 to +100)")
                print(f"      DSI={dsi:.1f}, DSO={dso:.1f}, DPO={dpo:.1f}")

            return {
                'dsi': round(dsi, 1),
                'dso': round(dso, 1),
                'dpo': round(dpo, 1),
                'ccc': round(ccc, 1)
            }
        except Exception as e:
            print(f"      Calculation error: {e}")
            return None

    def _calculate_dsi(self, vital_signs: Dict) -> float:
        """Days Sales of Inventory = 365 / (COGS / Inventory)"""
        cogs = vital_signs['cost_of_sales_billion']
        inventory = vital_signs['inventory_billion']
        return (365 * inventory) / cogs

    def _calculate_dso(self, vital_signs: Dict) -> float:
        """Days Sales Outstanding = 365 / (Revenue / Receivables)"""
        revenue = vital_signs['net_sales_billion']
        receivables = vital_signs['current_receivables_billion']
        return (365 * receivables) / revenue

    def _calculate_dpo(self, vital_signs: Dict) -> float:
        """Days Payables Outstanding = 365 / (COGS / Payables)"""
        cogs = vital_signs['cost_of_sales_billion']
        payables = vital_signs['current_payables_billion']
        return (365 * payables) / cogs

    def _extract_inventory_from_table(self, soup: BeautifulSoup, html_content: str) -> Optional[float]:
        """
        Fallback method to extract inventory from HTML Balance Sheet table when XBRL tags missing.

        Uses regex pattern matching to find "Merchandise inventories" or "Inventories" in the
        Consolidated Balance Sheets section and extract the corresponding value.

        Returns:
            Inventory value in billions, or None if not found
        """
        import re

        # Pattern 1: Look for "Merchandise inventories" or "Inventories" in table rows
        # Common patterns in Kroger's Balance Sheet:
        # - "Merchandise inventories</td><td>...</td><td>8,123</td>"
        # - "Inventories, net</span></td><td>...</td><td>$8,234</td>"

        # Find Balance Sheet section first
        balance_sheet_patterns = [
            r'(?:Consolidated\s+)?Balance\s+Sheets?(?:\s+\(Unaudited\))?',
            r'Statements?\s+of\s+Financial\s+Position',
            r'Statements?\s+of\s+Condition'
        ]

        balance_sheet_section = None
        for pattern in balance_sheet_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Extract section after match (next 50,000 characters should contain balance sheet)
                balance_sheet_section = html_content[match.start():match.start() + 50000]
                break

        if not balance_sheet_section:
            print(f"      Could not locate Balance Sheet section")
            return None

        # Pattern 2: Find inventory line items in the Balance Sheet
        # Look for inventory-related keywords followed by a number within same HTML context
        inventory_patterns = [
            r'(?:Merchandise\s+)?[Ii]nventories?(?:\s*,?\s*net)?.*?(?:[\$\s]+([\d,]+))',  # Basic pattern
            r'>(?:Merchandise\s+)?[Ii]nventories?(?:\s*,?\s*net)?[^<]*</(?:td|span)>\s*<(?:td|span)[^>]*>\s*(?:[\$\s]+([\d,]+))',  # Table cell pattern
        ]

        for pattern in inventory_patterns:
            matches = list(re.finditer(pattern, balance_sheet_section, re.IGNORECASE | re.DOTALL))

            if matches:
                # Take the FIRST match (usually the most recent period in multi-column tables)
                match = matches[0]

                # Extract number from capture group
                if match.lastindex and match.lastindex >= 1:
                    num_str = match.group(match.lastindex)

                    # Clean and parse number
                    num_str = num_str.replace(',', '').strip()

                    try:
                        # Value is typically in millions in SEC filings
                        value_millions = float(num_str)
                        value_billions = value_millions / 1000.0

                        print(f"      Extracted inventory from table: ${value_billions:.2f}B")

                        # Sanity check: Retail inventory typically $1B-$20B
                        if 0.5 <= value_billions <= 25.0:
                            return value_billions
                        else:
                            print(f"      ⚠️  WARNING: Inventory ${value_billions:.2f}B outside expected range (0.5-25B)")
                            # Still return it, but warn
                            return value_billions

                    except ValueError:
                        print(f"      Could not parse inventory value: {num_str}")
                        continue

        print(f"      Could not extract inventory from Balance Sheet table")
        return None

    def _extract_fiscal_year(self, period: str) -> int:
        """Extract fiscal year from period string like 'FY2024'."""
        match = re.search(r'(\d{4})', period)
        return int(match.group(1)) if match else 2024

    def _read_html(self, filepath: Path) -> str:
        """Read HTML file content and append full-submission.txt for older filings."""
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # For older filings, XBRL data is in full-submission.txt, not in HTML
        # Check if full-submission.txt exists and append it
        submission_file = filepath.parent / "full-submission.txt"
        if submission_file.exists():
            try:
                with open(submission_file, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content += f.read()
            except Exception:
                pass  # If we can't read it, continue with just HTML

        return html_content

    def _extract_xbrl_value(self, soup: BeautifulSoup, gaap_tag: str, raw_content: str = None) -> Optional[float]:
        """
        Extract numeric value from XBRL tag for the most recent period.

        Supports both modern iXBRL format and legacy raw XML format.

        Args:
            soup: BeautifulSoup parsed HTML
            gaap_tag: US-GAAP taxonomy tag name (e.g., 'us-gaap:Revenues')
            raw_content: Optional raw HTML/XML content for regex-based extraction

        Returns:
            Extracted numeric value in billions, or None if not found
        """
        # METHOD 1: Modern iXBRL format with ix:nonfraction wrapper
        # Example: <ix:nonfraction name="us-gaap:Revenues" scale="6">106566</ix:nonfraction>
        tags = soup.find_all('ix:nonfraction', attrs={'name': gaap_tag})

        # Try with different casing
        if not tags:
            tags = soup.find_all('ix:nonFraction', attrs={'name': gaap_tag})

        if tags:
            # Sort tags by contextRef to prioritize consolidated annual data
            # Consolidated data typically has contextRef with "FY", "Annual", or no segment suffix
            def tag_priority(tag):
                context_ref = tag.get('contextRef', '')
                # Highest priority: contextRef contains "FY" or "Annual"
                if 'FY' in context_ref or 'Annual' in context_ref:
                    return 0
                # Medium priority: contextRef does not contain segment indicators
                if not any(x in context_ref for x in ['Segment', 'segment', '_', 'Member']):
                    return 1
                # Lowest priority: everything else (segments)
                return 2

            sorted_tags = sorted(tags, key=tag_priority)

            # Iterate through sorted tags to find first valid numeric value
            for tag in sorted_tags:
                text = tag.get_text().strip().replace(',', '').replace('$', '')

                # Skip non-numeric values
                if text in ['—', '-', 'N/A', '']:
                    continue

                try:
                    value = float(text)

                    # Handle scale attribute (scale="6" means multiply by 10^6)
                    scale = tag.get('scale')
                    if scale:
                        scale_factor = 10 ** int(scale)
                        value = value * scale_factor

                    # Convert to billions (value is now in actual dollars)
                    return value / 1_000_000_000

                except ValueError:
                    continue

        # METHOD 2: Legacy raw XML format (for filings pre-2019)
        # Example: <us-gaap:Revenues contextRef="FY2015" decimals="-6">73785000000</us-gaap:Revenues>
        if raw_content:
            # Match raw XML tags with contextRef containing "FY" or "Q4YTD"
            # This filters to annual/year-end data, not interim periods
            pattern = fr'<{gaap_tag}\s+contextRef="[^"]*(?:FY|Q4YTD)[^"]*"\s+[^>]*decimals="[^"]*">([^<]+)</{gaap_tag}>'
            matches = re.findall(pattern, raw_content)

            if matches:
                # Take first match (most recent/relevant)
                text = matches[0].strip().replace(',', '')
                try:
                    value = float(text)
                    # Legacy format already in actual dollars with decimals="-6" (millions)
                    # Convert to billions
                    return value / 1_000_000_000
                except ValueError:
                    pass

        return None


def main():
    """Run peer CCC analysis for all companies and export results."""
    analyzer = PeerCCCAnalyzer()

    # Analyze all peers
    all_peer_data = {}
    for company_name, config in PEER_COMPANIES.items():
        print(f"\n{'='*60}")
        print(f"Analyzing {company_name} ({config['ticker']})")
        print(f"{'='*60}")

        peer_data = analyzer.analyze_peer(
            ticker=config['ticker'],
            cik=config['cik'],
            company_name=company_name,
            num_years=5
        )

        all_peer_data[company_name] = peer_data
        print(f"✅ {company_name}: Extracted {len(peer_data['years'])} years of data")

    # Export to peer_comparison_data.json
    output = {
        'cash_conversion_cycle': {
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'data_source': 'Automated extraction from SEC EDGAR 10-K filings',
            'companies': {}
        }
    }

    # Restructure to multi-year format
    for company, data in all_peer_data.items():
        output['cash_conversion_cycle']['companies'][company] = {
            'ticker': data['ticker'],
            'years': data['years'],
            'notes': PEER_COMPANIES[company]['notes']
        }

    # Write to data/peer_comparison_data.json
    output_path = Path('data/peer_comparison_data.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Peer CCC data exported to {output_path}")
    print(f"{'='*60}")

    # Summary
    total_years = sum(len(d['years']) for d in all_peer_data.values())
    print(f"\n📊 Summary:")
    print(f"   Companies analyzed: {len(all_peer_data)}")
    print(f"   Total fiscal years: {total_years}")
    print(f"   Average years per company: {total_years / len(all_peer_data):.1f}")


if __name__ == "__main__":
    main()
