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

        # Phase 2: Track quarterly results by quarter number for YoY comparison
        self.quarterly_history = {}  # {"Q1": [Q1 2024, Q1 2025], "Q2": [...], ...}

        # Phase 2: Risk heatmap - count mentions across all filings
        self.risk_heatmap = {
            'shrink': [],      # [(period, mention_count), ...]
            'theft': [],
            'markdown': [],
            'margin_pressure': []
        }

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
            metadata = self.fetcher.download_filings(ticker, cik, num_10k=10, num_10q=12)
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

        # Extract financial data (pass raw content for older filings)
        vital_signs = self._extract_vital_signs(soup, is_annual=True, raw_content=html_content)
        comp_sales = self._extract_comparable_sales(soup, is_annual=True)

        # Phase 2: Calculate inventory and debt metrics
        inventory_metrics = self._calculate_inventory_metrics(vital_signs, period)
        debt_metrics = self._calculate_debt_metrics(vital_signs)

        # Pillar 2: Calculate liquidity metrics
        liquidity_metrics = self._calculate_liquidity_metrics(vital_signs, period)

        # Phase 3: Calculate cash flow metrics
        cashflow_metrics = self._calculate_cashflow_metrics(vital_signs)

        # Phase 3: Extract temporal keys
        fiscal_year, fiscal_quarter = self._parse_period_to_fiscal(period)

        # Extract qualitative data
        strategic_promise = self._extract_strategic_promise(soup)

        return {
            "period": period,
            "filing_type": "10-K",
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "vital_signs": vital_signs,
            "comparable_sales": comp_sales,
            "inventory_metrics": inventory_metrics,
            "debt_metrics": debt_metrics,
            "liquidity_metrics": liquidity_metrics,
            "cashflow_metrics": cashflow_metrics,
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

        # Extract financial data (pass raw content for older filings)
        vital_signs = self._extract_vital_signs(soup, is_annual=False, raw_content=html_content)
        comp_sales = self._extract_comparable_sales(soup, is_annual=False)

        # Phase 2: Calculate inventory and debt metrics
        inventory_metrics = self._calculate_inventory_metrics(vital_signs, period)
        debt_metrics = self._calculate_debt_metrics(vital_signs)

        # Pillar 2: Calculate liquidity metrics
        liquidity_metrics = self._calculate_liquidity_metrics(vital_signs, period)

        # Phase 3: Calculate cash flow metrics
        cashflow_metrics = self._calculate_cashflow_metrics(vital_signs)

        # Phase 3: Extract temporal keys
        fiscal_year, fiscal_quarter = self._parse_period_to_fiscal(period)

        # Extract risk flags (with heatmap tracking)
        risk_flags = self._extract_risk_flags(soup, period)

        # Compare to baseline if available
        if self.baseline:
            vital_signs['vs_baseline'] = self._compare_to_baseline(vital_signs)

        # Phase 2: Year-over-Year comparison
        quarter_num = self._extract_quarter_number(period)  # "Q1 2025" → "Q1"
        if quarter_num:
            vital_signs['vs_year_ago'] = self._compare_year_over_year(
                vital_signs, quarter_num, period
            )

            # Store in history for future comparisons
            if quarter_num not in self.quarterly_history:
                self.quarterly_history[quarter_num] = []
            self.quarterly_history[quarter_num].append({
                'period': period,
                'vital_signs': vital_signs.copy()  # Copy to avoid reference issues
            })

        return {
            "period": period,
            "filing_type": "10-Q",
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "vital_signs": vital_signs,
            "comparable_sales": comp_sales,
            "inventory_metrics": inventory_metrics,
            "debt_metrics": debt_metrics,
            "liquidity_metrics": liquidity_metrics,
            "cashflow_metrics": cashflow_metrics,
            "risk_flags": risk_flags
        }

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

    def _extract_vital_signs(self, soup: BeautifulSoup, is_annual: bool, raw_content: str = None) -> Dict:
        """
        Extract core financial metrics using direct XBRL tag parsing.

        Phase 2 Enhancement: Uses GAAP taxonomy mappings to directly extract
        values from <ix:nonFraction> tags instead of table parsing.

        Args:
            soup: BeautifulSoup parsed HTML/XML
            is_annual: True for 10-K, False for 10-Q
            raw_content: Optional raw HTML/XML content for regex-based extraction (older filings)
        """
        vital_signs = {}

        # Define GAAP taxonomy mappings
        # Target uses specific GAAP tags - these were discovered by inspecting actual filings
        GAAP_MAPPINGS = {
            'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': 'net_sales',
            'us-gaap:Revenues': 'net_sales',
            'us-gaap:SalesRevenueNet': 'net_sales',
            'us-gaap:CostOfGoodsAndServicesSold': 'cost_of_sales',
            'us-gaap:CostOfGoodsSold': 'cost_of_sales',
            'us-gaap:CostOfRevenue': 'cost_of_sales',
            'us-gaap:OperatingIncomeLoss': 'operating_income',
            'us-gaap:InventoryNet': 'inventory',
            'us-gaap:InterestExpense': 'interest_expense',
            'us-gaap:LongTermDebt': 'long_term_debt',
            'us-gaap:ShortTermBorrowings': 'short_term_debt',
            'us-gaap:DebtCurrent': 'short_term_debt',
            # Phase 3: Cash Flow Statement metrics
            'us-gaap:NetCashProvidedByUsedInOperatingActivities': 'operating_cash_flow',
            'us-gaap:NetCashProvidedByUsedInInvestingActivities': 'investing_cash_flow',
            'us-gaap:NetCashProvidedByUsedInFinancingActivities': 'financing_cash_flow',
            # Phase 4: Net Income for profit margin calculation
            'us-gaap:NetIncomeLoss': 'net_income',
            'us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic': 'net_income',  # Older filings
            # Phase 6: SG&A expense for operating expense breakdown
            'us-gaap:SellingGeneralAndAdministrativeExpense': 'sga_expense',
            # Phase 7: Depreciation & Amortization for EBITDA bridge
            'us-gaap:DepreciationDepletionAndAmortization': 'depreciation_amortization',
            'us-gaap:Depreciation': 'depreciation_amortization',  # Alternative tag
            # Pillar 2: Balance Sheet items for Liquidity & Solvency analysis
            'us-gaap:AssetsCurrent': 'current_assets',
            'us-gaap:LiabilitiesCurrent': 'current_liabilities',
            'us-gaap:CashCashEquivalentsAndShortTermInvestments': 'cash_and_equivalents',
            'us-gaap:CashAndCashEquivalentsAtCarryingValue': 'cash_and_equivalents',  # Fallback
            'us-gaap:AccountsAndOtherReceivablesNetCurrent': 'current_receivables',
            'us-gaap:AccountsReceivableNetCurrent': 'current_receivables',  # Fallback
            'us-gaap:StockholdersEquity': 'stockholders_equity',
            'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest': 'stockholders_equity',  # Fallback
            'us-gaap:Assets': 'total_assets'
        }

        # Extract all XBRL tagged values
        for gaap_tag, metric_name in GAAP_MAPPINGS.items():
            value = self._extract_xbrl_value(soup, gaap_tag, raw_content)
            if value is not None:
                # Convert to billions (values are usually in millions)
                vital_signs[f'{metric_name}_billion'] = value / 1000.0

        # Calculate derived metrics
        if 'net_sales_billion' in vital_signs and 'cost_of_sales_billion' in vital_signs:
            net_sales = vital_signs['net_sales_billion']
            cost_of_sales = vital_signs['cost_of_sales_billion']
            gross_margin = ((net_sales - cost_of_sales) / net_sales) * 100
            vital_signs['gross_margin_percent'] = round(gross_margin, 2)

        if 'net_sales_billion' in vital_signs and 'operating_income_billion' in vital_signs:
            operating_margin = (vital_signs['operating_income_billion'] / vital_signs['net_sales_billion']) * 100
            vital_signs['operating_margin_percent'] = round(operating_margin, 2)

        # Phase 4: Calculate net profit margin
        if 'net_income_billion' in vital_signs and 'net_sales_billion' in vital_signs:
            net_profit_margin = (vital_signs['net_income_billion'] / vital_signs['net_sales_billion']) * 100
            vital_signs['net_profit_margin_percent'] = round(net_profit_margin, 2)

        # Phase 6: SG&A metrics
        if 'sga_expense_billion' in vital_signs and 'net_sales_billion' in vital_signs:
            sga_percent = (vital_signs['sga_expense_billion'] / vital_signs['net_sales_billion']) * 100
            vital_signs['sga_percent_of_revenue'] = round(sga_percent, 2)

            # Calculate Other Operating Expenses (derived)
            # Other = Net Sales - COGS - SG&A - Operating Income
            if 'cost_of_sales_billion' in vital_signs and 'operating_income_billion' in vital_signs:
                other_expenses = (vital_signs['net_sales_billion'] -
                                 vital_signs['cost_of_sales_billion'] -
                                 vital_signs['sga_expense_billion'] -
                                 vital_signs['operating_income_billion'])
                vital_signs['other_operating_expenses_billion'] = round(other_expenses, 3)

        # Phase 7: EBITDA calculation
        # EBITDA = Operating Income + Depreciation & Amortization
        if 'operating_income_billion' in vital_signs and 'depreciation_amortization_billion' in vital_signs:
            ebitda = vital_signs['operating_income_billion'] + vital_signs['depreciation_amortization_billion']
            vital_signs['ebitda_billion'] = round(ebitda, 3)

            # EBITDA margin
            if 'net_sales_billion' in vital_signs:
                ebitda_margin = (ebitda / vital_signs['net_sales_billion']) * 100
                vital_signs['ebitda_margin_percent'] = round(ebitda_margin, 2)

        return vital_signs

    def _extract_xbrl_value(self, soup: BeautifulSoup, gaap_tag: str, raw_content: str = None) -> Optional[float]:
        """
        Extract numeric value from XBRL tag for the most recent period.

        Supports both modern iXBRL format and legacy raw XML format.

        Args:
            soup: BeautifulSoup parsed HTML
            gaap_tag: US-GAAP taxonomy tag name (e.g., 'us-gaap:Revenues')
            raw_content: Optional raw HTML/XML content for regex-based extraction

        Returns:
            Extracted numeric value in millions, or None if not found
        """
        # METHOD 1: Modern iXBRL format with ix:nonfraction wrapper
        # Example: <ix:nonfraction name="us-gaap:Revenues" scale="6">106566</ix:nonfraction>
        tags = soup.find_all('ix:nonfraction', attrs={'name': gaap_tag})

        # Try with different casing
        if not tags:
            tags = soup.find_all('ix:nonFraction', attrs={'name': gaap_tag})

        if tags:
            # Iterate through all tags to find first valid numeric value
            # (SEC filings often have multiple tags: segments, prior year, N/A values)
            for tag in tags:
                text = tag.get_text().strip().replace(',', '').replace('$', '')

                # Skip non-numeric values (em dash, "N/A", etc.)
                if not text or text in ['—', '–', 'N/A', 'n/a', '-']:
                    continue

                try:
                    value = float(text)
                    if value is None:
                        continue

                    # Check for scale attribute (e.g., scale="6" means multiply by 10^6)
                    scale = tag.get('scale')
                    if scale:
                        scale_factor = int(scale)
                        value = value * (10 ** scale_factor)

                    # Convert from dollars to millions
                    value_in_millions = value / 1_000_000

                    # Skip unreasonably small values (likely segment data or prior year)
                    # For Target (100B+ revenue company), debt values < 100M are likely not consolidated totals
                    if value_in_millions < 100:
                        continue

                    return value_in_millions
                except (ValueError, TypeError):
                    # This tag has invalid numeric format, try next tag
                    continue

            # If we got here, no valid numeric values found in any tag
            # Fall through to METHOD 2 (legacy XML format)

        # METHOD 2: Legacy raw XML format (FY2015-FY2018)
        # Example: <us-gaap:SalesRevenueNet contextRef="FD2015Q4YTD" decimals="-6">73785000000</us-gaap:SalesRevenueNet>
        # BeautifulSoup doesn't preserve XML namespaces, so we use regex on raw content

        if raw_content:
            import re

            # Build regex pattern to match the GAAP tag with contextRef
            # Look for annual period context (Q4YTD or FY)
            # Pattern: <us-gaap:TagName contextRef="...Q4YTD..." decimals="..." ...>VALUE</us-gaap:TagName>
            pattern = rf'<{re.escape(gaap_tag)}\s+[^>]*contextRef="[^"]*(?:Q4YTD|FY)[^"]*"[^>]*decimals="([^"]*)"[^>]*>([0-9]+)</\s*{re.escape(gaap_tag)}\s*>'

            matches = re.findall(pattern, raw_content)
            if matches:
                # Take the first match (usually the most recent period)
                decimals_str, value_str = matches[0]
                try:
                    value = float(value_str)
                    decimals = int(decimals_str)

                    # decimals="-6" means value is in dollars, rounded to nearest million
                    # We need to return in millions, so divide by 1,000,000
                    # decimals="-3" means value is in dollars, rounded to nearest thousand
                    # All values in the XML are in actual dollars, not pre-scaled
                    return value / 1_000_000
                except (ValueError, TypeError):
                    pass

        return None

    def _parse_period_to_fiscal(self, period: str) -> tuple:
        """
        Parse period string to fiscal year and quarter (Phase 3).

        Args:
            period: Period label like "FY2024", "Q1 2025"

        Returns:
            Tuple of (fiscal_year, fiscal_quarter)
            - fiscal_year: int (e.g., 2024)
            - fiscal_quarter: int or None (1-3 for Q1-Q3, None for annual)
        """
        # Match annual format: FY2024
        annual_match = re.match(r'FY(\d{4})', period)
        if annual_match:
            return int(annual_match.group(1)), None

        # Match quarterly format: Q1 2025
        quarterly_match = re.match(r'Q(\d)\s+(\d{4})', period)
        if quarterly_match:
            quarter = int(quarterly_match.group(1))
            year = int(quarterly_match.group(2))
            return year, quarter

        # Fallback - try to extract just the year
        year_match = re.search(r'(\d{4})', period)
        if year_match:
            return int(year_match.group(1)), None

        return None, None

    def _calculate_cashflow_metrics(self, vital_signs: Dict) -> Dict:
        """
        Calculate cash flow metrics (Phase 3 Enhancement).

        Metrics:
        - Free Cash Flow = Operating Cash Flow - CapEx (if available)
        - Operating Cash Flow Margin = Operating Cash Flow / Revenue

        Args:
            vital_signs: Dictionary containing cash flow and revenue data

        Returns:
            Dictionary with cash flow metrics
        """
        cashflow_metrics = {}

        operating_cf = vital_signs.get('operating_cash_flow_billion')
        investing_cf = vital_signs.get('investing_cash_flow_billion')
        financing_cf = vital_signs.get('financing_cash_flow_billion')
        net_sales = vital_signs.get('net_sales_billion')

        if operating_cf is not None:
            cashflow_metrics['operating_cash_flow_billion'] = operating_cf

            if net_sales and net_sales > 0:
                cf_margin = (operating_cf / net_sales) * 100
                cashflow_metrics['operating_cash_flow_margin_percent'] = round(cf_margin, 2)

        if investing_cf is not None:
            cashflow_metrics['investing_cash_flow_billion'] = investing_cf

        if financing_cf is not None:
            cashflow_metrics['financing_cash_flow_billion'] = financing_cf

        return cashflow_metrics

    def _calculate_inventory_metrics(self, vital_signs: Dict, period: str) -> Dict:
        """
        Calculate inventory efficiency metrics (Phase 2 Enhancement).

        Metrics:
        - Inventory Turnover Ratio = COGS / Average Inventory
        - Days Sales of Inventory (DSI) = 365 / Inventory Turnover

        Args:
            vital_signs: Dictionary containing cost_of_sales_billion and inventory_billion
            period: Period label for tracking

        Returns:
            Dictionary with inventory metrics
        """
        inventory_metrics = {}

        # Need COGS and Inventory
        cogs = vital_signs.get('cost_of_sales_billion')
        inventory = vital_signs.get('inventory_billion')

        if cogs and inventory:
            # For simplicity, use current inventory (not average)
            # To calculate true average, would need previous period's inventory
            inventory_turnover = cogs / inventory
            dsi = 365 / inventory_turnover

            inventory_metrics['inventory_turnover_ratio'] = round(inventory_turnover, 2)
            inventory_metrics['days_sales_of_inventory'] = round(dsi, 1)

        return inventory_metrics

    def _calculate_debt_metrics(self, vital_signs: Dict) -> Dict:
        """
        Calculate debt servicing metrics (Phase 2 Enhancement).

        Metrics:
        - Interest Coverage Ratio = Operating Income / Interest Expense
        - Total Debt = Long-term Debt + Short-term Debt

        Args:
            vital_signs: Dictionary containing operating_income, interest_expense, and debt values

        Returns:
            Dictionary with debt metrics
        """
        debt_metrics = {}

        operating_income = vital_signs.get('operating_income_billion')
        interest_expense = vital_signs.get('interest_expense_billion')
        long_term_debt = vital_signs.get('long_term_debt_billion')
        short_term_debt = vital_signs.get('short_term_debt_billion', 0)

        if operating_income and interest_expense and interest_expense > 0:
            # Calculate interest coverage ratio
            interest_coverage = operating_income / interest_expense
            debt_metrics['interest_coverage_ratio'] = round(interest_coverage, 2)

            # Interest expense is in millions, operating income is in billions
            # Both should be in same units for ratio
            debt_metrics['interest_expense_million'] = round(interest_expense * 1000, 0)
            debt_metrics['operating_income_million'] = round(operating_income * 1000, 0)

            # Flag if below 2.0x (warning threshold)
            if interest_coverage < 2.0:
                debt_metrics['interest_coverage_warning'] = f"Low coverage: {interest_coverage:.2f}x"

        if long_term_debt is not None:
            total_debt = long_term_debt + short_term_debt
            debt_metrics['total_debt_billion'] = round(total_debt, 2)
        else:
            total_debt = None

        # Pillar 2: Capital Structure & Solvency ratios
        stockholders_equity = vital_signs.get('stockholders_equity_billion')
        total_assets = vital_signs.get('total_assets_billion')
        ebitda = vital_signs.get('ebitda_billion')  # Phase 7 metric
        net_income = vital_signs.get('net_income_billion')  # Phase 3 metric

        total_debt_billion = debt_metrics.get('total_debt_billion')

        if total_debt_billion and stockholders_equity:
            # 1. Debt-to-Equity Ratio = Total Debt / Stockholders' Equity
            debt_to_equity = total_debt_billion / stockholders_equity
            debt_metrics['debt_to_equity_ratio'] = round(debt_to_equity, 2)

            # Retail benchmark: <1.0 is conservative, 1.0-2.0 is moderate, >2.0 is aggressive
            if debt_to_equity < 1.0:
                debt_metrics['leverage_profile'] = 'conservative'
            elif debt_to_equity <= 2.0:
                debt_metrics['leverage_profile'] = 'moderate'
            else:
                debt_metrics['leverage_profile'] = 'aggressive'

        if total_debt_billion and total_assets:
            # 2. Debt-to-Assets Ratio = Total Debt / Total Assets
            debt_to_assets = total_debt_billion / total_assets
            debt_metrics['debt_to_assets_ratio'] = round(debt_to_assets, 2)

        if stockholders_equity and total_assets:
            # 3. Equity Ratio = Stockholders' Equity / Total Assets
            equity_ratio = stockholders_equity / total_assets
            debt_metrics['equity_ratio'] = round(equity_ratio, 2)

        if total_debt_billion and ebitda:
            # 4. Debt-to-EBITDA Ratio = Total Debt / EBITDA
            # Measures how many years of EBITDA needed to pay off debt
            # Benchmark: <3.0 is healthy, 3.0-5.0 is moderate, >5.0 is risky
            debt_to_ebitda = total_debt_billion / ebitda
            debt_metrics['debt_to_ebitda_ratio'] = round(debt_to_ebitda, 2)

            if debt_to_ebitda < 3.0:
                debt_metrics['debt_to_ebitda_health'] = 'healthy'
            elif debt_to_ebitda <= 5.0:
                debt_metrics['debt_to_ebitda_health'] = 'moderate'
            else:
                debt_metrics['debt_to_ebitda_health'] = 'risky'

        # Pillar 2: Return on Equity and Assets
        if net_income and stockholders_equity:
            # 5. ROE = (Net Income / Stockholders' Equity) × 100%
            roe = (net_income / stockholders_equity) * 100
            debt_metrics['return_on_equity_percent'] = round(roe, 2)

        if net_income and total_assets:
            # 6. ROA = (Net Income / Total Assets) × 100%
            roa = (net_income / total_assets) * 100
            debt_metrics['return_on_assets_percent'] = round(roa, 2)

        return debt_metrics

    def _calculate_liquidity_metrics(self, vital_signs: Dict, period: str) -> Dict:
        """
        Calculate short-term liquidity ratios and working capital (Pillar 2).

        Metrics:
        - Current Ratio = Current Assets / Current Liabilities
          Target: >1.5 (retail industry benchmark)
        - Quick Ratio = (Cash + Receivables) / Current Liabilities
          Target: >1.0 (acid test of immediate liquidity)
        - Working Capital = Current Assets - Current Liabilities
          Positive indicates ability to cover short-term obligations

        Args:
            vital_signs: Dict containing current_assets, current_liabilities,
                         cash_and_equivalents, current_receivables
            period: Period label (e.g., "Q1 2025")

        Returns:
            Dict with liquidity_metrics or empty dict if data unavailable
        """
        liquidity_metrics = {}

        # Extract required data (values already in billions from vital_signs)
        current_assets = vital_signs.get('current_assets_billion')
        current_liabilities = vital_signs.get('current_liabilities_billion')
        cash = vital_signs.get('cash_and_equivalents_billion')
        receivables = vital_signs.get('current_receivables_billion', 0)  # May not exist

        if not current_assets or not current_liabilities:
            return {}  # Insufficient data

        # 1. Current Ratio = Current Assets / Current Liabilities
        current_ratio = current_assets / current_liabilities
        liquidity_metrics['current_ratio'] = round(current_ratio, 2)

        # Health flag (retail benchmark: >1.5 is healthy)
        if current_ratio >= 1.5:
            liquidity_metrics['current_ratio_health'] = 'healthy'
        elif current_ratio >= 1.0:
            liquidity_metrics['current_ratio_health'] = 'adequate'
        else:
            liquidity_metrics['current_ratio_health'] = 'warning'

        # 2. Quick Ratio (Acid Test) = (Cash + Receivables) / Current Liabilities
        if cash is not None:
            quick_assets = cash + receivables
            quick_ratio = quick_assets / current_liabilities
            liquidity_metrics['quick_ratio'] = round(quick_ratio, 2)

            # Health flag (benchmark: >1.0 is healthy)
            if quick_ratio >= 1.0:
                liquidity_metrics['quick_ratio_health'] = 'healthy'
            elif quick_ratio >= 0.8:
                liquidity_metrics['quick_ratio_health'] = 'adequate'
            else:
                liquidity_metrics['quick_ratio_health'] = 'warning'

        # 3. Working Capital = Current Assets - Current Liabilities (in billions)
        working_capital = current_assets - current_liabilities
        liquidity_metrics['working_capital_billion'] = round(working_capital, 2)

        # Trend flag (positive is healthy)
        liquidity_metrics['working_capital_trend'] = 'positive' if working_capital > 0 else 'negative'

        return liquidity_metrics

    def _extract_quarter_number(self, period: str) -> Optional[str]:
        """
        Extract quarter number from period label (Phase 2 Enhancement).

        Args:
            period: Period label like "Q1 2025", "Q2 2024"

        Returns:
            Quarter number ("Q1", "Q2", "Q3") or None
        """
        match = re.match(r'(Q\d)', period)
        return match.group(1) if match else None

    def _compare_year_over_year(self, current_vital_signs: Dict,
                                quarter_num: str, current_period: str) -> Dict:
        """
        Compare current quarter to same quarter from previous year (Phase 2 Enhancement).

        Args:
            current_vital_signs: Current quarter vital signs
            quarter_num: Quarter number ("Q1", "Q2", "Q3")
            current_period: Current period label

        Returns:
            Dictionary with YoY comparison metrics
        """
        comparison = {}

        # Find previous year's same quarter
        if quarter_num not in self.quarterly_history:
            return comparison

        # Get the most recent previous entry (year ago)
        previous_quarters = self.quarterly_history[quarter_num]
        if not previous_quarters:
            return comparison

        prior_year = previous_quarters[-1]  # Most recent Q1/Q2/Q3 from history
        prior_vital = prior_year['vital_signs']

        # Compare operating margin YoY
        if 'operating_margin_percent' in current_vital_signs and 'operating_margin_percent' in prior_vital:
            current_margin = current_vital_signs['operating_margin_percent']
            prior_margin = prior_vital['operating_margin_percent']
            diff = current_margin - prior_margin

            comparison['operating_margin_yoy_change'] = round(diff, 2)
            comparison['operating_margin_yoy_trend'] = "improving" if diff > 0 else "declining"
            comparison['comparison_period'] = prior_year['period']

        # Compare net sales YoY
        if 'net_sales_billion' in current_vital_signs and 'net_sales_billion' in prior_vital:
            current_sales = current_vital_signs['net_sales_billion']
            prior_sales = prior_vital['net_sales_billion']
            growth = ((current_sales - prior_sales) / prior_sales) * 100

            comparison['net_sales_yoy_growth_percent'] = round(growth, 2)

        # Compare inventory YoY
        if 'inventory_billion' in current_vital_signs and 'inventory_billion' in prior_vital:
            current_inv = current_vital_signs['inventory_billion']
            prior_inv = prior_vital['inventory_billion']
            inv_growth = ((current_inv - prior_inv) / prior_inv) * 100

            comparison['inventory_yoy_growth_percent'] = round(inv_growth, 2)

            # Flag if inventory growing faster than sales
            if 'net_sales_yoy_growth_percent' in comparison:
                if inv_growth > comparison['net_sales_yoy_growth_percent'] + 5:
                    comparison['inventory_buildup_warning'] = \
                        f"Inventory growing {inv_growth:.1f}% vs sales {comparison['net_sales_yoy_growth_percent']:.1f}%"

        return comparison

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

    def _extract_risk_flags(self, soup: BeautifulSoup, period: str) -> List[str]:
        """
        Phase 2: Monitor for markdown and shrink mentions in quarterly filings.
        Also populate risk heatmap for trend analysis.

        Args:
            soup: BeautifulSoup parsed HTML
            period: Period label for tracking in heatmap

        Returns:
            List of risk flag strings
        """
        flags = []

        # Find MD&A section
        mda_section = self._find_mda_section(soup, is_annual=False)

        if mda_section:
            text = mda_section.get_text()

            # Check for shrink mentions (with count for heatmap)
            shrink_pattern = r"shrink|inventory\s+shortage|theft"
            shrink_matches = re.findall(shrink_pattern, text, re.IGNORECASE)
            if shrink_matches:
                self.risk_heatmap['shrink'].append((period, len(shrink_matches)))

                # Try to extract basis point impact
                bp_pattern = r"(\d+)\s*basis\s+points?"
                match = re.search(bp_pattern, text, re.IGNORECASE)
                if match:
                    flags.append(f"Shrink reduced gross margin by {match.group(1)} basis points")
                else:
                    flags.append("Shrink/theft mentioned in MD&A")

            # Check for markdown/clearance mentions (with count for heatmap)
            markdown_pattern = r"markdown|clearance|promotional|discount"
            markdown_matches = re.findall(markdown_pattern, text, re.IGNORECASE)
            if markdown_matches:
                self.risk_heatmap['markdown'].append((period, len(markdown_matches)))
                flags.append("Increased markdown/promotional activity noted")

            # Check for margin pressure (with count for heatmap)
            margin_pattern = r"margin\s+pressure|margin\s+decline|margin\s+compression"
            margin_matches = re.findall(margin_pattern, text, re.IGNORECASE)
            if margin_matches:
                self.risk_heatmap['margin_pressure'].append((period, len(margin_matches)))
                flags.append("Margin pressure mentioned")

        return flags

    def get_risk_heatmap_summary(self) -> Dict:
        """
        Generate summary of risk mentions across all periods (Phase 2 Enhancement).

        Returns:
            Dictionary with risk heatmap summary statistics
        """
        summary = {}

        for risk_type, mentions in self.risk_heatmap.items():
            if mentions:
                total_mentions = sum(count for _, count in mentions)
                periods_affected = len(mentions)
                avg_mentions = total_mentions / periods_affected if periods_affected > 0 else 0

                summary[risk_type] = {
                    'total_mentions': total_mentions,
                    'periods_affected': periods_affected,
                    'avg_mentions_per_period': round(avg_mentions, 1),
                    'trend': 'increasing' if mentions[-1][1] > mentions[0][1] else 'stable/decreasing',
                    'details': mentions
                }

        return summary

    def extract_executive_insights(self) -> Dict:
        """
        Extract key insights for executive summary (Phase 4).

        Identifies:
        - Inflection points (major quarterly changes)
        - Top trends (strongest/weakest metrics)
        - Critical warnings (debt, inventory, margin risks)
        """
        insights = {
            'inflection_points': [],
            'top_trends': {},
            'critical_warnings': []
        }

        # 1. Identify inflection points (>50bp margin change QoQ)
        prev_margin = None
        for filing in self.results:
            if filing['filing_type'] == '10-Q':
                current_margin = filing['vital_signs'].get('operating_margin_percent')
                if current_margin and prev_margin:
                    delta = current_margin - prev_margin
                    if abs(delta) >= 0.5:  # 50 basis points
                        insights['inflection_points'].append({
                            'period': filing['period'],
                            'metric': 'Operating Margin',
                            'change_bp': round(delta * 100, 0),
                            'direction': 'improvement' if delta > 0 else 'deterioration'
                        })
                prev_margin = current_margin

        # 2. Identify top YoY trends
        yoy_changes = []
        for filing in self.results:
            if filing['filing_type'] == '10-Q':
                vs_year_ago = filing['vital_signs'].get('vs_year_ago', {})
                if vs_year_ago:
                    margin_yoy = vs_year_ago.get('operating_margin_yoy_change')
                    sales_yoy = vs_year_ago.get('net_sales_yoy_growth_percent')

                    if margin_yoy is not None:
                        yoy_changes.append({
                            'period': filing['period'],
                            'metric': 'Operating Margin',
                            'yoy_change': margin_yoy
                        })

                    if sales_yoy is not None:
                        yoy_changes.append({
                            'period': filing['period'],
                            'metric': 'Net Sales',
                            'yoy_change': sales_yoy
                        })

        # Get strongest/weakest
        if yoy_changes:
            yoy_changes_sorted = sorted(yoy_changes, key=lambda x: x['yoy_change'])
            insights['top_trends']['weakest'] = yoy_changes_sorted[0]
            insights['top_trends']['strongest'] = yoy_changes_sorted[-1]

        # 3. Critical warnings
        for filing in self.results:
            period = filing['period']

            # Debt coverage warning
            debt_metrics = filing.get('debt_metrics', {})
            coverage = debt_metrics.get('interest_coverage_ratio')
            if coverage and coverage < 2.0:
                insights['critical_warnings'].append({
                    'period': period,
                    'type': 'Debt Coverage',
                    'severity': 'Critical',
                    'message': f"Interest coverage at {coverage:.2f}x (below 2.0x threshold)"
                })

            # Inventory buildup warning
            vs_year_ago = filing['vital_signs'].get('vs_year_ago', {})
            inv_warning = vs_year_ago.get('inventory_buildup_warning')
            if inv_warning:
                insights['critical_warnings'].append({
                    'period': period,
                    'type': 'Inventory Risk',
                    'severity': 'High',
                    'message': inv_warning
                })

        return insights

    def export_executive_insights(self, output_path: str):
        """Export executive insights to JSON (Phase 4)."""
        insights = self.extract_executive_insights()

        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2)

        print(f"✅ Executive insights exported to: {output_path}")

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

        # Phase 2: Display inventory metrics
        inv_metrics = result.get('inventory_metrics', {})
        if inv_metrics:
            print("\n📦 Inventory Efficiency:")
            if 'inventory_turnover_ratio' in inv_metrics:
                print(f"   Turnover Ratio: {inv_metrics['inventory_turnover_ratio']:.2f}x")
            if 'days_sales_of_inventory' in inv_metrics:
                print(f"   Days Sales of Inventory: {inv_metrics['days_sales_of_inventory']:.1f} days")

        # Phase 2: Display debt metrics
        debt_metrics = result.get('debt_metrics', {})
        if debt_metrics:
            print("\n💳 Debt Metrics:")
            if 'total_debt_billion' in debt_metrics:
                print(f"   Total Debt: ${debt_metrics['total_debt_billion']:.2f}B")
            if 'interest_coverage_ratio' in debt_metrics:
                coverage = debt_metrics['interest_coverage_ratio']
                warning = " ⚠️" if coverage < 2.0 else ""
                print(f"   Interest Coverage: {coverage:.2f}x{warning}")
            if 'interest_coverage_warning' in debt_metrics:
                print(f"   {debt_metrics['interest_coverage_warning']}")

        if 'vs_baseline' in vital:
            print("\n📊 vs Baseline:")
            for key, value in vital['vs_baseline'].items():
                print(f"   {key}: {value}")

        # Phase 2: Display year-over-year comparison
        if 'vs_year_ago' in vital:
            yoy = vital['vs_year_ago']
            if yoy:  # Only print if there's data
                print("\n📅 Year-over-Year:")
                for key, value in yoy.items():
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
        """Export all results to JSON file including risk heatmap (Phase 2)."""
        output_data = {
            'filings': self.results,
            'risk_heatmap': self.get_risk_heatmap_summary()
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✅ Results exported to: {output_path}")

    def export_timeseries_json(self, output_path: str):
        """
        Export time-series friendly JSON format (Phase 3).

        Creates a flat structure optimized for Plotly visualization with parallel
        arrays for each metric category.
        """
        timeseries_data = {
            'metadata': {
                'company': 'Target Corporation',
                'ticker': 'TGT',
                'cik': '0000027419',
                'total_periods': len(self.results)
            },
            'periods': [],
            'metrics': {
                'revenue': {
                    'net_sales_billion': [],
                    'yoy_growth_percent': []
                },
                'margins': {
                    'gross_margin_percent': [],
                    'operating_margin_percent': [],
                    'net_profit_margin_percent': [],
                    'operating_margin_yoy_change': []
                },
                'inventory': {
                    'inventory_billion': [],
                    'inventory_turnover_ratio': [],
                    'days_sales_of_inventory': [],
                    'inventory_yoy_growth_percent': []
                },
                'debt': {
                    'total_debt_billion': [],
                    'interest_coverage_ratio': [],
                    # Pillar 2: Solvency ratios
                    'debt_to_equity_ratio': [],
                    'leverage_profile': [],
                    'debt_to_assets_ratio': [],
                    'equity_ratio': [],
                    'debt_to_ebitda_ratio': [],
                    'debt_to_ebitda_health': [],
                    'return_on_equity_percent': [],
                    'return_on_assets_percent': []
                },
                'liquidity': {
                    'current_ratio': [],
                    'current_ratio_health': [],
                    'quick_ratio': [],
                    'quick_ratio_health': [],
                    'working_capital_billion': [],
                    'working_capital_trend': [],
                    'current_assets_billion': [],
                    'current_liabilities_billion': []
                },
                'comparable_sales': {
                    'total_change_percent': [],
                    'digital_change_percent': []
                },
                'cash_flows': {
                    'operating_cash_flow_billion': [],
                    'investing_cash_flow_billion': [],
                    'financing_cash_flow_billion': [],
                    'operating_cash_flow_margin_percent': [],
                    'net_income_billion': []  # For earnings quality analysis
                },
                'operating_expenses': {
                    'cost_of_sales_billion': [],
                    'cogs_percent_of_revenue': [],
                    'sga_expense_billion': [],
                    'sga_percent_of_revenue': [],
                    'other_operating_expenses_billion': [],
                    'other_expenses_percent_of_revenue': [],
                    'depreciation_amortization_billion': [],  # Phase 7
                    'ebitda_billion': [],  # Phase 7
                    'ebitda_margin_percent': []  # Phase 7
                }
            },
            'comparisons': {
                'revenue_vs_inventory': [],
                'margin_waterfall': []
            },
            'risk_heatmap': self.get_risk_heatmap_summary()
        }

        # Populate arrays in chronological order
        for filing in self.results:
            # Period metadata
            period_entry = {
                'period': filing['period'],
                'fiscal_year': filing.get('fiscal_year'),
                'fiscal_quarter': filing.get('fiscal_quarter'),
                'filing_type': filing['filing_type']
            }
            timeseries_data['periods'].append(period_entry)

            vital = filing['vital_signs']
            inv_metrics = filing.get('inventory_metrics', {})
            debt_metrics = filing.get('debt_metrics', {})
            liquidity_metrics = filing.get('liquidity_metrics', {})
            comp_sales = filing.get('comparable_sales', {})
            cashflow_metrics = filing.get('cashflow_metrics', {})

            # Revenue metrics
            timeseries_data['metrics']['revenue']['net_sales_billion'].append(
                vital.get('net_sales_billion')
            )
            yoy = vital.get('vs_year_ago', {})
            timeseries_data['metrics']['revenue']['yoy_growth_percent'].append(
                yoy.get('net_sales_yoy_growth_percent')
            )

            # Margin metrics
            timeseries_data['metrics']['margins']['gross_margin_percent'].append(
                vital.get('gross_margin_percent')
            )
            timeseries_data['metrics']['margins']['operating_margin_percent'].append(
                vital.get('operating_margin_percent')
            )
            timeseries_data['metrics']['margins']['net_profit_margin_percent'].append(
                vital.get('net_profit_margin_percent')
            )
            timeseries_data['metrics']['margins']['operating_margin_yoy_change'].append(
                yoy.get('operating_margin_yoy_change')
            )

            # Inventory metrics
            timeseries_data['metrics']['inventory']['inventory_billion'].append(
                vital.get('inventory_billion')
            )
            timeseries_data['metrics']['inventory']['inventory_turnover_ratio'].append(
                inv_metrics.get('inventory_turnover_ratio')
            )
            timeseries_data['metrics']['inventory']['days_sales_of_inventory'].append(
                inv_metrics.get('days_sales_of_inventory')
            )
            timeseries_data['metrics']['inventory']['inventory_yoy_growth_percent'].append(
                yoy.get('inventory_yoy_growth_percent')
            )

            # Debt metrics
            timeseries_data['metrics']['debt']['total_debt_billion'].append(
                debt_metrics.get('total_debt_billion')
            )
            timeseries_data['metrics']['debt']['interest_coverage_ratio'].append(
                debt_metrics.get('interest_coverage_ratio')
            )

            # Pillar 2: Solvency ratios
            timeseries_data['metrics']['debt']['debt_to_equity_ratio'].append(
                debt_metrics.get('debt_to_equity_ratio')
            )
            timeseries_data['metrics']['debt']['leverage_profile'].append(
                debt_metrics.get('leverage_profile')
            )
            timeseries_data['metrics']['debt']['debt_to_assets_ratio'].append(
                debt_metrics.get('debt_to_assets_ratio')
            )
            timeseries_data['metrics']['debt']['equity_ratio'].append(
                debt_metrics.get('equity_ratio')
            )
            timeseries_data['metrics']['debt']['debt_to_ebitda_ratio'].append(
                debt_metrics.get('debt_to_ebitda_ratio')
            )
            timeseries_data['metrics']['debt']['debt_to_ebitda_health'].append(
                debt_metrics.get('debt_to_ebitda_health')
            )
            timeseries_data['metrics']['debt']['return_on_equity_percent'].append(
                debt_metrics.get('return_on_equity_percent')
            )
            timeseries_data['metrics']['debt']['return_on_assets_percent'].append(
                debt_metrics.get('return_on_assets_percent')
            )

            # Pillar 2: Liquidity metrics
            timeseries_data['metrics']['liquidity']['current_ratio'].append(
                liquidity_metrics.get('current_ratio')
            )
            timeseries_data['metrics']['liquidity']['current_ratio_health'].append(
                liquidity_metrics.get('current_ratio_health')
            )
            timeseries_data['metrics']['liquidity']['quick_ratio'].append(
                liquidity_metrics.get('quick_ratio')
            )
            timeseries_data['metrics']['liquidity']['quick_ratio_health'].append(
                liquidity_metrics.get('quick_ratio_health')
            )
            timeseries_data['metrics']['liquidity']['working_capital_billion'].append(
                liquidity_metrics.get('working_capital_billion')
            )
            timeseries_data['metrics']['liquidity']['working_capital_trend'].append(
                liquidity_metrics.get('working_capital_trend')
            )
            timeseries_data['metrics']['liquidity']['current_assets_billion'].append(
                vital.get('current_assets_billion')
            )
            timeseries_data['metrics']['liquidity']['current_liabilities_billion'].append(
                vital.get('current_liabilities_billion')
            )

            # Comparable sales
            timeseries_data['metrics']['comparable_sales']['total_change_percent'].append(
                comp_sales.get('total_change_percent')
            )
            timeseries_data['metrics']['comparable_sales']['digital_change_percent'].append(
                comp_sales.get('digital_change_percent')
            )

            # Cash flows (Phase 3)
            timeseries_data['metrics']['cash_flows']['operating_cash_flow_billion'].append(
                cashflow_metrics.get('operating_cash_flow_billion')
            )
            timeseries_data['metrics']['cash_flows']['investing_cash_flow_billion'].append(
                cashflow_metrics.get('investing_cash_flow_billion')
            )
            timeseries_data['metrics']['cash_flows']['financing_cash_flow_billion'].append(
                cashflow_metrics.get('financing_cash_flow_billion')
            )
            timeseries_data['metrics']['cash_flows']['operating_cash_flow_margin_percent'].append(
                cashflow_metrics.get('operating_cash_flow_margin_percent')
            )
            timeseries_data['metrics']['cash_flows']['net_income_billion'].append(
                vital.get('net_income_billion')
            )

            # Operating expenses (Phase 6)
            timeseries_data['metrics']['operating_expenses']['cost_of_sales_billion'].append(
                vital.get('cost_of_sales_billion')
            )
            timeseries_data['metrics']['operating_expenses']['sga_expense_billion'].append(
                vital.get('sga_expense_billion')
            )
            timeseries_data['metrics']['operating_expenses']['sga_percent_of_revenue'].append(
                vital.get('sga_percent_of_revenue')
            )
            timeseries_data['metrics']['operating_expenses']['other_operating_expenses_billion'].append(
                vital.get('other_operating_expenses_billion')
            )

            # Calculate COGS and Other percentages
            if vital.get('cost_of_sales_billion') and vital.get('net_sales_billion'):
                cogs_pct = (vital['cost_of_sales_billion'] / vital['net_sales_billion']) * 100
                timeseries_data['metrics']['operating_expenses']['cogs_percent_of_revenue'].append(round(cogs_pct, 2))
            else:
                timeseries_data['metrics']['operating_expenses']['cogs_percent_of_revenue'].append(None)

            if vital.get('other_operating_expenses_billion') and vital.get('net_sales_billion'):
                other_pct = (vital['other_operating_expenses_billion'] / vital['net_sales_billion']) * 100
                timeseries_data['metrics']['operating_expenses']['other_expenses_percent_of_revenue'].append(round(other_pct, 2))
            else:
                timeseries_data['metrics']['operating_expenses']['other_expenses_percent_of_revenue'].append(None)

            # Phase 7: EBITDA metrics
            timeseries_data['metrics']['operating_expenses']['depreciation_amortization_billion'].append(
                vital.get('depreciation_amortization_billion')
            )
            timeseries_data['metrics']['operating_expenses']['ebitda_billion'].append(
                vital.get('ebitda_billion')
            )
            timeseries_data['metrics']['operating_expenses']['ebitda_margin_percent'].append(
                vital.get('ebitda_margin_percent')
            )

            # Comparisons
            net_sales = vital.get('net_sales_billion')
            inventory = vital.get('inventory_billion')
            if net_sales and inventory:
                timeseries_data['comparisons']['revenue_vs_inventory'].append({
                    'period': filing['period'],
                    'revenue': net_sales,
                    'inventory': inventory,
                    'inventory_to_revenue_ratio': round(inventory / net_sales, 3)
                })

            operating_margin = vital.get('operating_margin_percent')
            if operating_margin:
                timeseries_data['comparisons']['margin_waterfall'].append({
                    'period': filing['period'],
                    'operating_margin': operating_margin
                })

        with open(output_path, 'w') as f:
            json.dump(timeseries_data, f, indent=2)

        print(f"✅ Time-series data exported to: {output_path}")

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
    analyzer.export_timeseries_json("output/target_timeseries.json")
    analyzer.export_summary_report("output/target_summary.txt")
    analyzer.export_executive_insights("output/executive_insights.json")

    print("\n✅ Analysis complete!")
    print(f"   Total filings analyzed: {len(results)}")
    print(f"   Output files:")
    print(f"     - target_analysis.json (detailed format)")
    print(f"     - target_timeseries.json (time-series format for Plotly)")
    print(f"     - target_summary.txt (human-readable report)")
    print(f"     - executive_insights.json (key insights for reports)")


if __name__ == "__main__":
    main()
