"""
SEC EDGAR Data Fetcher Module

Handles automated downloading of SEC filings using the sec-edgar-downloader library.
Provides a clean interface for fetching Target Corporation 10-K and 10-Q filings.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sec_edgar_downloader import Downloader


class SECDataFetcher:
    """
    Wrapper class for sec-edgar-downloader with filing organization capabilities.
    """

    def __init__(self, company_name: str, email: str, download_dir: str):
        """
        Initialize the SEC EDGAR downloader.

        Args:
            company_name: Your company/organization name (for User-Agent)
            email: Your contact email (for User-Agent, required by SEC)
            download_dir: Base directory for downloaded filings
        """
        self.company_name = company_name
        self.email = email
        self.download_dir = Path(download_dir)

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

    def _extract_period_from_file(self, filepath: Path, filing_type: str) -> str:
        """
        Extract period label from XBRL file by reading title tag.

        Args:
            filepath: Path to XBRL file
            filing_type: "10-K" or "10-Q"

        Returns:
            Period label string (e.g., "FY2024", "Q1 2025")
        """
        try:
            # Read first 5000 bytes to find title tag
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(5000)

            # Look for title tag with pattern like: <title>tgt-20250201</title>
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                title = title_match.group(1)
                # Extract date from title if present
                date_match = re.search(r'(\d{8})', title)
                if date_match:
                    date_str = date_match.group(1)
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])

                    # Target's fiscal year ends in late January/early February
                    if filing_type == "10-K":
                        fiscal_year = year - 1  # FY2024 ends in Feb 2025
                        return f"FY{fiscal_year}"
                    else:  # 10-Q
                        # Map months to quarters (with some flexibility for filing dates)
                        if month in [4, 5, 6]:
                            return f"Q1 {year}"
                        elif month in [7, 8, 9]:
                            return f"Q2 {year}"
                        elif month in [10, 11, 12]:
                            return f"Q3 {year}"
                        else:
                            # Month 1-3 might be Q4 from previous year
                            return f"Period {year}-{month:02d}"

        except Exception:
            pass

        # Fallback: try filename
        return self._extract_period_from_filename(filepath.name)

    def _extract_period_from_filename(self, filename: str) -> str:
        """
        Extract period label from XBRL filename.

        Examples:
            tgt-20250201.htm → "FY2024" (Feb 1, 2025 end date = FY2024)
            tgt-20250503.htm → "Q1 2025"
            tgt-20250802.htm → "Q2 2025"

        Args:
            filename: XBRL filename (e.g., "tgt-20250201.htm")

        Returns:
            Period label string
        """
        # Extract date from filename (format: tgt-YYYYMMDD.htm)
        match = re.search(r"-(\d{4})(\d{2})(\d{2})\.htm", filename)
        if not match:
            return "Unknown Period"

        year = int(match.group(1))
        month = int(match.group(2))

        # Target's fiscal year ends in late January/early February
        # FY2024 ends Feb 1, 2025
        if month in [1, 2]:
            # This is a fiscal year-end
            fiscal_year = year - 1
            return f"FY{fiscal_year}"
        elif month in [5]:
            return f"Q1 {year}"
        elif month in [8]:
            return f"Q2 {year}"
        elif month in [11]:
            return f"Q3 {year}"
        else:
            return f"Period {year}-{month:02d}"

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

        # Sort by period (rough chronological sort)
        # FY filings first, then Q1, Q2, Q3 in order
        def sort_key(item):
            period = item[0]
            if period.startswith("FY"):
                year = int(period[2:])
                return (year, 0)  # FY comes first
            elif period.startswith("Q"):
                quarter = int(period[1])
                year = int(period.split()[1])
                return (year, quarter)
            else:
                return (0, 0)  # Unknown periods go first

        all_filings.sort(key=sort_key)

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
