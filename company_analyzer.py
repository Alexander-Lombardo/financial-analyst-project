"""
Company Analyzer Orchestration Module
======================================
Coordinates CIK lookup, fiscal year detection, filing download,
and financial analysis for any company.

Usage:
    from company_analyzer import analyze_company, get_company_info

    # Check if company data exists
    info = get_company_info("AAPL")

    # Run full analysis (downloads if needed)
    result = analyze_company("AAPL", force_refresh=False)
"""

import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime


# Cache for SEC company tickers data
_SEC_TICKERS_CACHE = None
_SEC_TICKERS_CACHE_FILE = Path("data/sec_company_tickers.json")

# Known fiscal year end months for common tickers (optional override)
# If not in this dict, defaults to December (12)
KNOWN_FISCAL_YEAR_ENDS = {
    'TGT': 1,   # January FY end
    'WMT': 1,   # January FY end
    'COST': 8,  # August FY end
    'KR': 1,    # January FY end
    'AAPL': 9,  # September FY end
    'MSFT': 6,  # June FY end
    'HD': 1,    # January FY end
    'LOW': 1,   # January FY end
    'DG': 1,    # January FY end
    'DLTR': 1,  # January FY end
    'WBA': 8,   # August FY end
}


def fetch_sec_company_tickers() -> dict:
    """
    Fetch company tickers from SEC EDGAR API.
    URL: https://www.sec.gov/files/company_tickers.json

    Returns dict mapping ticker -> {cik, name}
    Caches to file for 24 hours.
    """
    global _SEC_TICKERS_CACHE

    # Check memory cache
    if _SEC_TICKERS_CACHE:
        return _SEC_TICKERS_CACHE

    # Check file cache (if less than 24 hours old)
    if _SEC_TICKERS_CACHE_FILE.exists():
        try:
            mtime = datetime.fromtimestamp(_SEC_TICKERS_CACHE_FILE.stat().st_mtime)
            if (datetime.now() - mtime).total_seconds() < 86400:
                with open(_SEC_TICKERS_CACHE_FILE, 'r') as f:
                    _SEC_TICKERS_CACHE = json.load(f)
                    return _SEC_TICKERS_CACHE
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read SEC tickers cache: {e}")

    # Fetch from SEC
    # SEC requires a User-Agent with company name and email
    # See: https://www.sec.gov/os/accessing-edgar-data
    print("📡 Fetching company list from SEC EDGAR...")
    url = "https://www.sec.gov/files/company_tickers.json"

    # Try to get email from environment, fallback to generic
    user_email = os.environ.get("SEC_USER_EMAIL", "user@example.com")
    user_name = os.environ.get("SEC_USER_NAME", "CompanyAnalyzer")

    headers = {
        "User-Agent": f"{user_name} {user_email}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Transform to ticker -> info mapping
        raw_data = response.json()
        ticker_map = {}
        for entry in raw_data.values():
            ticker = entry['ticker'].upper()
            ticker_map[ticker] = {
                'cik': str(entry['cik_str']).zfill(10),
                'name': entry['title']
            }

        # Cache to file
        _SEC_TICKERS_CACHE_FILE.parent.mkdir(exist_ok=True)
        with open(_SEC_TICKERS_CACHE_FILE, 'w') as f:
            json.dump(ticker_map, f)

        _SEC_TICKERS_CACHE = ticker_map
        print(f"   ✅ Loaded {len(ticker_map)} companies from SEC")
        return ticker_map

    except requests.RequestException as e:
        print(f"❌ SEC API request failed: {e}")
        # Try to use stale cache as fallback
        if _SEC_TICKERS_CACHE_FILE.exists():
            print("   Using stale cache as fallback...")
            try:
                with open(_SEC_TICKERS_CACHE_FILE, 'r') as f:
                    _SEC_TICKERS_CACHE = json.load(f)
                    return _SEC_TICKERS_CACHE
            except (IOError, json.JSONDecodeError):
                pass
        raise


def get_company_info(ticker: str) -> Optional[Dict]:
    """
    Look up company information for ANY ticker using SEC EDGAR API.

    Args:
        ticker: Stock ticker symbol (e.g., "TGT", "AAPL", "F", "NFLX")

    Returns:
        Dictionary with company info or None if not found:
        {
            'ticker': 'AAPL',
            'cik': '0000320193',
            'name': 'Apple Inc.',
            'fiscal_year_end_month': 9
        }
    """
    ticker = ticker.upper().strip()

    if not ticker:
        return None

    try:
        # Fetch from SEC API (uses cache if available)
        tickers = fetch_sec_company_tickers()

        if ticker in tickers:
            info = tickers[ticker]
            # Use known fiscal year end if available, otherwise default to December
            fy_month = KNOWN_FISCAL_YEAR_ENDS.get(ticker, 12)

            return {
                'ticker': ticker,
                'cik': info['cik'],
                'name': info['name'],
                'fiscal_year_end_month': fy_month
            }
    except Exception as e:
        print(f"SEC lookup failed: {e}")

    return None


def lookup_cik_from_sec(ticker: str) -> Optional[str]:
    """
    Look up CIK from SEC EDGAR API.

    Args:
        ticker: Stock ticker symbol

    Returns:
        CIK string or None if not found
    """
    info = get_company_info(ticker)
    return info['cik'] if info else None


def has_cached_data(ticker: str) -> bool:
    """
    Check if analyzed data exists for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        True if timeseries JSON exists and is recent
    """
    ticker = ticker.upper().strip()
    timeseries_path = Path(f"output/{ticker.lower()}_timeseries.json")

    # Fallback for legacy Target file naming
    if ticker == "TGT" and not timeseries_path.exists():
        legacy_path = Path("output/target_timeseries.json")
        if legacy_path.exists():
            timeseries_path = legacy_path

    if not timeseries_path.exists():
        return False

    # Check if file is recent (less than 24 hours old)
    mtime = datetime.fromtimestamp(timeseries_path.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600

    return age_hours < 24


def get_cached_data(ticker: str) -> Optional[Dict]:
    """
    Load cached analysis data for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Timeseries data dictionary or None if not cached
    """
    ticker = ticker.upper().strip()
    timeseries_path = Path(f"output/{ticker.lower()}_timeseries.json")

    # Fallback for legacy Target file naming
    if ticker == "TGT" and not timeseries_path.exists():
        legacy_path = Path("output/target_timeseries.json")
        if legacy_path.exists():
            timeseries_path = legacy_path

    if not timeseries_path.exists():
        return None

    try:
        with open(timeseries_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def analyze_company(ticker: str, force_refresh: bool = False,
                    num_10k: int = 10, num_10q: int = 12) -> Dict:
    """
    Analyze any company's SEC filings.

    This is the main orchestration function that:
    1. Looks up company CIK
    2. Checks for cached data
    3. Downloads SEC filings if needed
    4. Runs financial analysis
    5. Returns path to output files

    Args:
        ticker: Stock ticker symbol (e.g., "TGT", "AAPL", "WMT")
        force_refresh: If True, re-download and re-analyze even if cached
        num_10k: Number of 10-K annual reports to download (default: 10)
        num_10q: Number of 10-Q quarterly reports to download (default: 12)

    Returns:
        Dictionary with analysis results:
        {
            'success': True/False,
            'ticker': 'TGT',
            'company_name': 'Target Corporation',
            'timeseries_path': 'output/tgt_timeseries.json',
            'analysis_path': 'output/tgt_analysis.json',
            'num_filings': 22,
            'error': None or error message
        }

    Raises:
        ValueError: If ticker is unknown and CIK cannot be determined
    """
    from dotenv import load_dotenv
    from financial_analyzer import CompanyFinancialAnalyzer

    load_dotenv()

    ticker = ticker.upper().strip()
    result = {
        'success': False,
        'ticker': ticker,
        'company_name': None,
        'timeseries_path': None,
        'analysis_path': None,
        'num_filings': 0,
        'error': None
    }

    # Step 1: Look up company info
    company_info = get_company_info(ticker)
    if not company_info:
        result['error'] = f"Unknown ticker: {ticker}. CIK lookup not implemented."
        print(f"❌ Error: {result['error']}")
        return result

    cik = company_info['cik']
    company_name = company_info['name']
    fy_month = company_info['fiscal_year_end_month']

    result['company_name'] = company_name

    print(f"\n📊 Analyzing: {company_name} ({ticker})")
    print(f"   CIK: {cik}")
    print(f"   Fiscal Year End: Month {fy_month}")

    # Step 2: Check for cached data
    if not force_refresh and has_cached_data(ticker):
        print(f"   ✅ Using cached data (less than 24 hours old)")
        cached = get_cached_data(ticker)
        if cached:
            result['success'] = True
            result['timeseries_path'] = f"output/{ticker.lower()}_timeseries.json"
            result['analysis_path'] = f"output/{ticker.lower()}_analysis.json"
            result['num_filings'] = cached.get('metadata', {}).get('total_periods', 0)
            return result

    # Step 3: Check for SEC credentials
    user_name = os.getenv("SEC_USER_NAME")
    user_email = os.getenv("SEC_USER_EMAIL")

    if not user_name or not user_email:
        result['error'] = "SEC credentials not configured. Set SEC_USER_NAME and SEC_USER_EMAIL in .env"
        print(f"❌ Error: {result['error']}")
        return result

    # Step 4: Initialize analyzer and download filings
    print(f"\n📥 Downloading SEC filings...")
    try:
        analyzer = CompanyFinancialAnalyzer(
            ticker=ticker,
            cik=cik,
            company_name=company_name,
            fiscal_year_end_month=fy_month,
            auto_download=True,
            user_name=user_name,
            user_email=user_email
        )

        # Download filings
        analyzer.download_required_filings(num_10k=num_10k, num_10q=num_10q)

        # Step 5: Analyze all filings
        print(f"\n📊 Analyzing filings...")
        results = analyzer.analyze_all_filings()

        # Step 6: Export results
        print(f"\n📤 Exporting results...")

        # Ensure output directory exists
        Path("output").mkdir(exist_ok=True)

        analyzer.export_json()  # output/{ticker}_analysis.json
        analyzer.export_timeseries_json()  # output/{ticker}_timeseries.json
        analyzer.export_summary_report()  # output/{ticker}_summary.txt
        analyzer.export_executive_insights()  # output/{ticker}_executive_insights.json

        result['success'] = True
        result['timeseries_path'] = f"output/{ticker.lower()}_timeseries.json"
        result['analysis_path'] = f"output/{ticker.lower()}_analysis.json"
        result['num_filings'] = len(results)

        print(f"\n✅ Analysis complete for {company_name}")
        print(f"   Filings analyzed: {len(results)}")
        print(f"   Output: output/{ticker.lower()}_*.json")

    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

    return result


def list_available_companies() -> Dict[str, Dict]:
    """
    List companies with known fiscal year ends and cached data status.

    Note: ANY publicly traded company can be analyzed via SEC lookup.
    This list shows companies with known fiscal year configurations.

    Returns:
        Dictionary of ticker -> info for companies with known FY ends
    """
    companies = {}

    # First, add companies with cached data
    output_dir = Path("output")
    if output_dir.exists():
        for json_file in output_dir.glob("*_timeseries.json"):
            ticker = json_file.stem.replace("_timeseries", "").upper()
            if ticker == "TARGET":
                ticker = "TGT"
            info = get_company_info(ticker)
            if info:
                companies[ticker] = {
                    'ticker': ticker,
                    'cik': info['cik'],
                    'name': info['name'],
                    'fiscal_year_end_month': info['fiscal_year_end_month'],
                    'has_cached_data': True
                }

    # Then add known FY companies that don't have cached data yet
    try:
        tickers = fetch_sec_company_tickers()
        for ticker, fy_month in KNOWN_FISCAL_YEAR_ENDS.items():
            if ticker not in companies and ticker in tickers:
                info = tickers[ticker]
                companies[ticker] = {
                    'ticker': ticker,
                    'cik': info['cik'],
                    'name': info['name'],
                    'fiscal_year_end_month': fy_month,
                    'has_cached_data': has_cached_data(ticker)
                }
    except Exception:
        pass  # SEC API may fail, that's okay

    return companies


if __name__ == "__main__":
    import sys

    # Example usage
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
        force = "--force" in sys.argv

        result = analyze_company(ticker, force_refresh=force)

        if result['success']:
            print(f"\n✅ Success! Data saved to:")
            print(f"   {result['timeseries_path']}")
            print(f"   {result['analysis_path']}")
        else:
            print(f"\n❌ Failed: {result['error']}")
    else:
        print("Usage: python company_analyzer.py <TICKER> [--force]")
        print("\nAvailable companies:")
        for ticker, info in list_available_companies().items():
            cached = "✓" if info['has_cached_data'] else " "
            print(f"  [{cached}] {ticker}: {info['name']}")
