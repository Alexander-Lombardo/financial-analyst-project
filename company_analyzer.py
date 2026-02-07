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
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime


# Known company CIKs for common tickers
KNOWN_CIKS = {
    'TGT': ('0000027419', 'Target Corporation', 1),      # January FY end
    'WMT': ('0000104169', 'Walmart Inc.', 1),             # January FY end
    'COST': ('0000909832', 'Costco Wholesale Corporation', 8),  # August FY end
    'AMZN': ('0001018724', 'Amazon.com, Inc.', 12),       # December FY end
    'KR': ('0000056873', 'The Kroger Co.', 1),            # January FY end
    'AAPL': ('0000320193', 'Apple Inc.', 9),              # September FY end
    'MSFT': ('0000789019', 'Microsoft Corporation', 6),   # June FY end
    'HD': ('0000354950', 'The Home Depot, Inc.', 1),      # January FY end
    'LOW': ('0000060667', "Lowe's Companies, Inc.", 1),   # January FY end
    'DG': ('0000029534', 'Dollar General Corporation', 1),  # January FY end
    'DLTR': ('0000935703', 'Dollar Tree, Inc.', 1),       # January FY end
    'CVS': ('0000064803', 'CVS Health Corporation', 12),  # December FY end
    'WBA': ('0001618921', 'Walgreens Boots Alliance, Inc.', 8),  # August FY end
}


def get_company_info(ticker: str) -> Optional[Dict]:
    """
    Look up company information for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "TGT", "AAPL")

    Returns:
        Dictionary with company info or None if unknown:
        {
            'ticker': 'AAPL',
            'cik': '0000320193',
            'name': 'Apple Inc.',
            'fiscal_year_end_month': 9
        }
    """
    ticker = ticker.upper().strip()

    if ticker in KNOWN_CIKS:
        cik, name, fy_month = KNOWN_CIKS[ticker]
        return {
            'ticker': ticker,
            'cik': cik,
            'name': name,
            'fiscal_year_end_month': fy_month
        }

    # Try SEC EDGAR company search (could implement API call here)
    # For now, return None for unknown tickers
    return None


def lookup_cik_from_sec(ticker: str) -> Optional[str]:
    """
    Look up CIK from SEC EDGAR API.

    Note: This is a placeholder - implement actual SEC API call if needed.

    Args:
        ticker: Stock ticker symbol

    Returns:
        CIK string or None if not found
    """
    # SEC provides a company tickers JSON file:
    # https://www.sec.gov/files/company_tickers.json
    # Could fetch and cache this for lookups
    return None


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
    List all companies with known CIKs and cached data status.

    Returns:
        Dictionary of ticker -> info for all known companies
    """
    companies = {}

    for ticker, (cik, name, fy_month) in KNOWN_CIKS.items():
        companies[ticker] = {
            'ticker': ticker,
            'cik': cik,
            'name': name,
            'fiscal_year_end_month': fy_month,
            'has_cached_data': has_cached_data(ticker)
        }

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
