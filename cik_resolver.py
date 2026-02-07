"""
CIK Resolver - Resolves company tickers to SEC CIK numbers.
Uses SEC's public APIs for ticker/CIK mapping and filing history.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class CIKResolver:
    """Resolves company tickers to SEC CIK numbers and fetches filing metadata."""

    # SEC API endpoints
    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

    # Cache settings
    CACHE_DIR = Path(".sec_cache")
    CACHE_EXPIRY_HOURS = 24

    def __init__(self, user_agent: str = None):
        """
        Initialize CIK resolver.

        Args:
            user_agent: User-Agent string for SEC requests (required by SEC).
                       Format: "Company Name contact@email.com"
        """
        self.user_agent = user_agent or os.getenv(
            "SEC_USER_AGENT",
            "SEC Filing Browser contact@example.com"
        )
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
        self._ticker_cache: Dict[str, Tuple[str, str]] = {}  # ticker -> (cik, name)
        self._last_request_time = 0

        # Ensure cache directory exists
        self.CACHE_DIR.mkdir(exist_ok=True)

    def _rate_limit(self):
        """Enforce SEC rate limit of 10 requests/second."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.1:  # 100ms between requests
            time.sleep(0.1 - elapsed)
        self._last_request_time = time.time()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.CACHE_DIR / f"{safe_key}.json"

    def _get_cached(self, key: str) -> Optional[dict]:
        """Get cached data if not expired."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            cached_time = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
            if datetime.now() - cached_time < timedelta(hours=self.CACHE_EXPIRY_HOURS):
                return data.get("data")
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _set_cache(self, key: str, data: dict):
        """Cache data with timestamp."""
        cache_path = self._get_cache_path(key)
        cache_data = {
            "_cached_at": datetime.now().isoformat(),
            "data": data
        }
        cache_path.write_text(json.dumps(cache_data))

    def _load_ticker_map(self) -> Dict[str, Tuple[str, str]]:
        """Load ticker to CIK mapping from SEC."""
        if self._ticker_cache:
            return self._ticker_cache

        # Check cache first
        cached = self._get_cached("company_tickers")
        if cached:
            self._ticker_cache = {
                k: tuple(v) for k, v in cached.items()
            }
            return self._ticker_cache

        # Fetch from SEC
        self._rate_limit()
        response = requests.get(self.TICKERS_URL, headers=self.headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Build ticker -> (cik, name) mapping
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", "")).zfill(10)
            name = entry.get("title", "")
            if ticker:
                self._ticker_cache[ticker] = (cik, name)

        # Cache the mapping
        self._set_cache("company_tickers", {
            k: list(v) for k, v in self._ticker_cache.items()
        })

        return self._ticker_cache

    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Get SEC CIK number for a ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")

        Returns:
            10-digit CIK string or None if not found
        """
        ticker_map = self._load_ticker_map()
        result = ticker_map.get(ticker.upper())
        return result[0] if result else None

    def get_company_name(self, ticker: str) -> Optional[str]:
        """
        Get official company name for a ticker symbol.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company name or None if not found
        """
        ticker_map = self._load_ticker_map()
        result = ticker_map.get(ticker.upper())
        return result[1] if result else None

    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """
        Get both CIK and company name for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with 'cik', 'name', 'ticker' or None if not found
        """
        ticker_map = self._load_ticker_map()
        result = ticker_map.get(ticker.upper())
        if result:
            return {
                "cik": result[0],
                "name": result[1],
                "ticker": ticker.upper()
            }
        return None

    # Minimum date for XBRL-era filings
    XBRL_START_DATE = "2009-01-01"

    def _fetch_additional_filings(self, filename: str) -> Optional[Dict]:
        """
        Fetch additional filings from a supplementary SEC submissions file.

        Args:
            filename: Name of the additional filings file (e.g., "CIK0000320193-submissions-001.json")

        Returns:
            Dict with filings data or None if fetch fails
        """
        cache_key = f"additional_{filename}"
        cached = self._get_cached(cache_key)

        if cached:
            return cached

        try:
            self._rate_limit()
            url = f"https://data.sec.gov/submissions/{filename}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except requests.RequestException:
            return None

    def _process_filings_data(
        self,
        filings_data: Dict,
        filing_types: List[str] = None,
        min_date: str = None
    ) -> List[Dict]:
        """
        Process filings data into a list of filing dicts.

        Args:
            filings_data: Dict with form, accessionNumber, filingDate, etc. arrays
            filing_types: Optional list of form types to filter
            min_date: Optional minimum filing date (YYYY-MM-DD format)

        Returns:
            List of filing dicts
        """
        filings = []

        forms = filings_data.get("form", [])
        accessions = filings_data.get("accessionNumber", [])
        filing_dates = filings_data.get("filingDate", [])
        primary_docs = filings_data.get("primaryDocument", [])
        descriptions = filings_data.get("primaryDocDescription", [])

        for i in range(len(forms)):
            form_type = forms[i] if i < len(forms) else ""
            filing_date = filing_dates[i] if i < len(filing_dates) else ""

            # Filter by filing type if specified
            if filing_types and form_type not in filing_types:
                continue

            # Filter by minimum date (XBRL era)
            if min_date and filing_date < min_date:
                continue

            filing = {
                "form": form_type,
                "accessionNumber": accessions[i] if i < len(accessions) else "",
                "filingDate": filing_date,
                "primaryDocument": primary_docs[i] if i < len(primary_docs) else "",
                "description": descriptions[i] if i < len(descriptions) else "",
            }
            filings.append(filing)

        return filings

    def get_company_filings(
        self,
        ticker: str = None,
        cik: str = None,
        filing_types: List[str] = None
    ) -> Dict:
        """
        Fetch all available filings for a company from SEC submissions API.
        Includes filings from 2009 onwards (XBRL era) by fetching additional
        historical filing files.

        Args:
            ticker: Stock ticker symbol (resolved to CIK if cik not provided)
            cik: SEC CIK number (10 digits, zero-padded)
            filing_types: Optional list of form types to filter (e.g., ["10-K", "10-Q"])

        Returns:
            Dict with company info and filing list
        """
        if not cik and not ticker:
            raise ValueError("Either ticker or cik must be provided")

        if not cik:
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                raise ValueError(f"Could not find CIK for ticker: {ticker}")

        # Ensure CIK is properly formatted (10 digits)
        cik = cik.lstrip("0").zfill(10)

        # Check cache
        cache_key = f"submissions_{cik}"
        cached = self._get_cached(cache_key)

        if not cached:
            # Fetch from SEC
            self._rate_limit()
            url = self.SUBMISSIONS_URL.format(cik=cik)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            cached = response.json()
            self._set_cache(cache_key, cached)

        # Extract company info
        result = {
            "cik": cik,
            "name": cached.get("name", ""),
            "ticker": ticker.upper() if ticker else "",
            "sic": cached.get("sic", ""),
            "sicDescription": cached.get("sicDescription", ""),
            "filings": []
        }

        filings_data = cached.get("filings", {})

        # Process recent filings
        recent = filings_data.get("recent", {})
        if recent:
            result["filings"].extend(
                self._process_filings_data(recent, filing_types, self.XBRL_START_DATE)
            )

        # Fetch and merge older filings from additional files
        additional_files = filings_data.get("files", [])
        for file_info in additional_files:
            filename = file_info.get("name")
            if not filename:
                continue

            # Check if this file contains filings from 2009+
            # filingTo is the most recent date in the file
            filing_to = file_info.get("filingTo", "")
            if filing_to and filing_to < self.XBRL_START_DATE:
                # Skip files that only contain pre-2009 filings
                continue

            additional_data = self._fetch_additional_filings(filename)
            if additional_data:
                result["filings"].extend(
                    self._process_filings_data(additional_data, filing_types, self.XBRL_START_DATE)
                )

        return result

    def search_companies(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for companies by ticker or name (fuzzy matching).

        Args:
            query: Search string (ticker or partial company name)
            limit: Maximum number of results

        Returns:
            List of matching companies with ticker, cik, and name
        """
        query = query.upper().strip()
        if not query:
            return []

        ticker_map = self._load_ticker_map()
        results = []

        # First, exact ticker match
        if query in ticker_map:
            cik, name = ticker_map[query]
            results.append({
                "ticker": query,
                "cik": cik,
                "name": name,
                "match_type": "exact_ticker"
            })

        # Then, ticker prefix matches
        for ticker, (cik, name) in ticker_map.items():
            if ticker.startswith(query) and ticker != query:
                results.append({
                    "ticker": ticker,
                    "cik": cik,
                    "name": name,
                    "match_type": "ticker_prefix"
                })
                if len(results) >= limit:
                    break

        # Finally, name contains matches (case-insensitive)
        if len(results) < limit:
            for ticker, (cik, name) in ticker_map.items():
                if query in name.upper() and not any(r["ticker"] == ticker for r in results):
                    results.append({
                        "ticker": ticker,
                        "cik": cik,
                        "name": name,
                        "match_type": "name_contains"
                    })
                    if len(results) >= limit:
                        break

        return results[:limit]

    def get_filing_url(self, cik: str, accession_number: str, primary_doc: str = None) -> str:
        """
        Construct SEC EDGAR URL for a filing.

        Args:
            cik: SEC CIK number
            accession_number: Filing accession number (e.g., "0001193125-24-012345")
            primary_doc: Primary document filename (optional)

        Returns:
            URL to the filing on SEC EDGAR
        """
        cik = cik.lstrip("0")
        accession_clean = accession_number.replace("-", "")

        if primary_doc:
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}"
        else:
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/"


# Module-level convenience functions
_resolver = None

def get_resolver() -> CIKResolver:
    """Get or create the global CIK resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = CIKResolver()
    return _resolver

def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """Get SEC CIK for a ticker symbol."""
    return get_resolver().get_cik_from_ticker(ticker)

def get_company_name(ticker: str) -> Optional[str]:
    """Get company name for a ticker symbol."""
    return get_resolver().get_company_name(ticker)

def get_company_filings(ticker: str = None, cik: str = None, filing_types: List[str] = None) -> Dict:
    """Get all filings for a company."""
    return get_resolver().get_company_filings(ticker, cik, filing_types)

def search_companies(query: str, limit: int = 10) -> List[Dict]:
    """Search for companies by ticker or name."""
    return get_resolver().search_companies(query, limit)


if __name__ == "__main__":
    # Test the resolver
    import sys

    resolver = CIKResolver()

    # Test with a few tickers
    test_tickers = ["AAPL", "MSFT", "WMT", "AMZN", "TGT"]

    print("Testing CIK Resolution:")
    print("-" * 60)

    for ticker in test_tickers:
        info = resolver.get_company_info(ticker)
        if info:
            print(f"{ticker}: CIK={info['cik']}, Name={info['name']}")
        else:
            print(f"{ticker}: Not found")

    print("\nTesting Company Search:")
    print("-" * 60)

    search_results = resolver.search_companies("APP", limit=5)
    for r in search_results:
        print(f"  {r['ticker']}: {r['name']} (CIK: {r['cik']})")

    print("\nTesting Filings Fetch:")
    print("-" * 60)

    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = "AAPL"

    filings = resolver.get_company_filings(ticker=ticker, filing_types=["10-K", "10-Q"])
    print(f"\n{filings['name']} ({ticker}) - CIK: {filings['cik']}")
    print(f"Found {len(filings['filings'])} 10-K/10-Q filings")
    print("\nRecent filings:")
    for f in filings['filings'][:10]:
        print(f"  {f['filingDate']} - {f['form']}: {f['description']}")
