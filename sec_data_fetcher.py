"""
SEC EDGAR Data Fetcher Module

Handles automated downloading of SEC filings using the sec-edgar-downloader library.
Provides a clean interface for fetching Target Corporation 10-K and 10-Q filings.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sec_edgar_downloader import Downloader


def period_sort_key(item) -> Tuple[int, int]:
    """
    Return a sort key for period labels that orders chronologically.

    Accepts:
      - a tuple (period_label, _) — as produced by get_filing_list
      - a bare period_label string
      - a dict with 'period' / 'fiscal_year' / 'fiscal_quarter' keys

    Within a fiscal year, quarters come before the annual (10-K) because the
    10-K period-of-report is dated in the fiscal-year-END month, after all 10-Qs.
    """
    if isinstance(item, tuple):
        period = item[0]
    elif isinstance(item, dict):
        period = item.get('period', '')
    else:
        period = str(item)

    if period.startswith("FY"):
        try:
            year = int(period[2:].split()[0])
        except (ValueError, IndexError):
            return (0, 0)
        return (year, 4)  # 10-K closes the fiscal year, after Q3
    if period.startswith("Q"):
        try:
            quarter = int(period[1])
            year = int(period.split()[1])
        except (ValueError, IndexError):
            return (0, 0)
        return (year, quarter)
    return (0, 0)


class SECDataFetcher:
    """
    Wrapper class for sec-edgar-downloader with filing organization capabilities.
    """

    def __init__(self, company_name: str, email: str, download_dir: str,
                 fiscal_calendar=None):
        """
        Initialize the SEC EDGAR downloader.

        Args:
            company_name: Your company/organization name (for User-Agent)
            email: Your contact email (for User-Agent, required by SEC)
            download_dir: Base directory for downloaded filings
            fiscal_calendar: Optional FiscalCalendar from config_loader. If
                supplied, filings are labeled using the company's actual fiscal
                calendar. If None, falls back to retail-calendar heuristics.
        """
        self.company_name = company_name
        self.email = email
        self.download_dir = Path(download_dir)
        self.fiscal_calendar = fiscal_calendar

        # Initialize downloader with proper User-Agent
        self.downloader = Downloader(company_name, email, str(self.download_dir))

        # Track downloaded filing metadata
        self.filing_metadata: Dict[str, List[Dict]] = {
            "10-K": [],
            "10-Q": []
        }

    def download_filings(
        self,
        ticker: str,
        cik: str,
        num_10k: int = 5,
        num_10q: int = 12
    ) -> Dict[str, List[Dict]]:
        """
        Download specified number of 10-K and 10-Q filings.

        Args:
            ticker: Stock ticker symbol (e.g., "TGT")
            cik: Central Index Key (e.g., "0000027419")
            num_10k: Number of recent 10-K filings to download
            num_10q: Number of recent 10-Q filings to download

        Returns:
            Dictionary with filing metadata:
            {
                "10-K": [{file_path, period, filing_date}, ...],
                "10-Q": [{file_path, period, filing_date}, ...]
            }
        """
        print(f"📥 Downloading {num_10k} 10-Ks and {num_10q} 10-Qs for {ticker}...")

        try:
            # Download 10-K filings (download_details=True gets the individual .htm files)
            self.downloader.get("10-K", ticker, limit=num_10k, download_details=True)
            self.filing_metadata["10-K"] = self._discover_filings(ticker, "10-K")

            # Download 10-Q filings (download_details=True gets the individual .htm files)
            self.downloader.get("10-Q", ticker, limit=num_10q, download_details=True)
            self.filing_metadata["10-Q"] = self._discover_filings(ticker, "10-Q")

            print(f"✅ Download complete:")
            print(f"   10-Ks: {len(self.filing_metadata['10-K'])} filings")
            print(f"   10-Qs: {len(self.filing_metadata['10-Q'])} filings")

            return self.filing_metadata

        except Exception as e:
            print(f"❌ Download failed: {e}")
            raise

    def _discover_filings(self, ticker: str, filing_type: str) -> List[Dict]:
        """
        Discover downloaded filing files and extract metadata.

        Args:
            ticker: Stock ticker symbol
            filing_type: "10-K" or "10-Q"

        Returns:
            List of filing metadata dictionaries
        """
        filings = []
        filing_dir = self.download_dir / "sec-edgar-filings" / ticker / filing_type

        if not filing_dir.exists():
            return filings

        # Iterate through filing subdirectories
        for filing_subdir in sorted(filing_dir.iterdir(), reverse=True):
            if not filing_subdir.is_dir():
                continue

            # Find the primary XBRL file
            htm_file = self._find_xbrl_file(filing_subdir)

            if htm_file:
                # Extract period info from file (check title tag for period end date)
                period_info = self._extract_period_from_file(htm_file, filing_type)

                # Get relative path from base data directory
                relative_path = htm_file.relative_to(self.download_dir)

                filings.append({
                    "file_path": str(relative_path),
                    "absolute_path": str(htm_file),
                    "period": period_info,
                    "filing_type": filing_type,
                    "accession": filing_subdir.name
                })

        return filings

    def _find_xbrl_file(self, filing_dir: Path) -> Optional[Path]:
        """
        Find the primary XBRL HTML file in a filing directory.

        The sec-edgar-downloader downloads multiple files per filing.
        We need to identify the main XBRL file.

        Args:
            filing_dir: Path to filing subdirectory

        Returns:
            Path to XBRL file, or None if not found
        """
        # Priority 1: Look for primary-document.html (from download_details=True)
        primary_doc = filing_dir / "primary-document.html"
        if primary_doc.exists():
            return primary_doc

        # Priority 2: Look for .htm files matching pattern: [ticker]-YYYYMMDD.htm
        for file in filing_dir.glob("*.htm"):
            if re.match(r"[a-z]+-\d{8}\.htm", file.name):
                return file

        # Priority 3: Return first .html or .htm file
        html_files = list(filing_dir.glob("*.html")) + list(filing_dir.glob("*.htm"))
        return html_files[0] if html_files else None

    def _label_period(self, year: int, month: int, filing_type: str) -> str:
        """
        Label a (year, month) period-end date using the configured fiscal
        calendar. Falls back to retail-calendar heuristics if no calendar is set.
        """
        if self.fiscal_calendar is not None:
            fc = self.fiscal_calendar
            if filing_type == "10-K":
                # 10-Ks always represent the annual period. Target's fiscal year
                # closes Jan 31 but the period-of-report can be Feb 1, so the
                # calendar month may differ by ±1 from year_end_month.
                if month == fc.year_end_month:
                    fy, _ = fc.quarter_for_period_end(year, month)
                else:
                    # Normalize: use the configured year_end_month for label mapping
                    fy, _ = fc.quarter_for_period_end(year, fc.year_end_month)
                    # If the calendar month is in the month BEFORE year_end_month
                    # (e.g., Jan 31 close for Feb config), the fiscal year is the
                    # one ENDING in this calendar year, which the helper above
                    # handles via the year_end_month normalization.
                    if fc.convention == "starts_in" and month < fc.year_end_month:
                        # Already handled by using year_end_month as-is
                        pass
                return f"FY{fy}"
            fy, q = fc.quarter_for_period_end(year, month)
            if q is None:
                return f"FY{fy}"
            return f"Q{q} {fy}"

        # Retail calendar fallback (legacy behavior)
        if filing_type == "10-K":
            fiscal_year = year - 1 if month <= 3 else year
            return f"FY{fiscal_year}"
        if month in [4, 5, 6]:
            return f"Q1 {year}"
        if month in [7, 8, 9]:
            return f"Q2 {year}"
        if month in [10, 11, 12]:
            return f"Q3 {year}"
        return f"Period {year}-{month:02d}"

    def _extract_period_from_file(self, filepath: Path, filing_type: str) -> str:
        """Extract period label from XBRL file's title tag."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(5000)

            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                date_match = re.search(r'(\d{8})', title_match.group(1))
                if date_match:
                    date_str = date_match.group(1)
                    return self._label_period(int(date_str[0:4]), int(date_str[4:6]), filing_type)
        except Exception:
            pass

        # Fallback 1: try filename
        period_from_filename = self._extract_period_from_filename(filepath.name, filing_type)
        if period_from_filename != "Unknown Period":
            return period_from_filename

        # Fallback 2: full-submission.txt
        return self._extract_period_from_submission(filepath.parent, filing_type)

    def _extract_period_from_filename(self, filename: str, filing_type: str = None) -> str:
        """Extract period label from filename like `tgt-20250201.htm`."""
        match = re.search(r"-(\d{4})(\d{2})(\d{2})\.htm", filename)
        if not match:
            return "Unknown Period"
        return self._label_period(int(match.group(1)), int(match.group(2)), filing_type or "10-Q")

    def _extract_period_from_submission(self, filing_dir: Path, filing_type: str) -> str:
        """Extract period label from `full-submission.txt` metadata."""
        submission_file = filing_dir / "full-submission.txt"
        if not submission_file.exists():
            return "Unknown Period"

        try:
            with open(submission_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)

            period_match = re.search(r'CONFORMED PERIOD OF REPORT:\s+(\d{8})', content)
            if period_match:
                date_str = period_match.group(1)
                return self._label_period(int(date_str[0:4]), int(date_str[4:6]), filing_type)
        except Exception:
            pass

        return "Unknown Period"

    def get_filing_list(self) -> List[Tuple[str, str]]:
        """
        Get filing list in format compatible with TargetFinancialAnalyzer.

        Returns:
            List of tuples: [(period_label, relative_file_path), ...]
            Sorted chronologically (oldest first)
        """
        all_filings = []

        # Combine 10-Ks and 10-Qs
        for filing_type in ["10-K", "10-Q"]:
            for filing in self.filing_metadata.get(filing_type, []):
                all_filings.append((
                    filing["period"],
                    filing["file_path"]
                ))

        all_filings.sort(key=period_sort_key)

        return all_filings

    def get_filing_count(self) -> Dict[str, int]:
        """
        Get count of downloaded filings by type.

        Returns:
            Dictionary: {"10-K": count, "10-Q": count}
        """
        return {
            "10-K": len(self.filing_metadata.get("10-K", [])),
            "10-Q": len(self.filing_metadata.get("10-Q", []))
        }


# Example usage for testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get credentials from environment
    user_name = os.getenv("SEC_USER_NAME", "Test")
    user_email = os.getenv("SEC_USER_EMAIL", "test@example.com")

    # Initialize fetcher
    fetcher = SECDataFetcher(user_name, user_email, "data/Target 10Q")

    # Download filings
    print("Testing SEC EDGAR downloader...")
    metadata = fetcher.download_filings("TGT", "0000027419", num_10k=2, num_10q=3)

    # Display results
    print("\nFiling List (for analyzer):")
    for period, filepath in fetcher.get_filing_list():
        print(f"  {period}: {filepath}")

    print("\nDownload complete!")
