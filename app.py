"""
SEC Filing Browser - Flask web application for browsing SEC filings.
Provides a web interface to search companies, view filing lists, and read individual filings.
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import requests

from cik_resolver import CIKResolver, search_companies, get_company_filings
from sec_data_fetcher import SECDataFetcher
from filing_parser import FilingParser

app = Flask(__name__)

# Initialize filing parser
filing_parser = FilingParser()

# Initialize components
cik_resolver = CIKResolver()
sec_fetcher = SECDataFetcher()


@app.route("/")
def index():
    """Home page with company search."""
    return render_template("index.html")


@app.route("/company/<ticker>")
def company(ticker: str):
    """Display all available filings for a company."""
    ticker = ticker.upper()

    # Get filter parameters
    form_filter = request.args.get("form", "").upper()
    year_filter = request.args.get("year", "")

    try:
        # Get company info and filings from SEC
        company_info = cik_resolver.get_company_info(ticker)
        if not company_info:
            return render_template(
                "error.html",
                error=f"Company not found: {ticker}",
                message="Please check the ticker symbol and try again."
            ), 404

        # Get all filings
        filings_data = cik_resolver.get_company_filings(ticker=ticker)

        # Apply filters
        filings = filings_data.get("filings", [])

        if form_filter:
            filings = [f for f in filings if f["form"] == form_filter]

        if year_filter:
            filings = [f for f in filings if f["filingDate"].startswith(year_filter)]

        # Get unique form types and years for filter dropdowns
        all_filings = filings_data.get("filings", [])
        form_types = sorted(set(f["form"] for f in all_filings))
        years = sorted(set(f["filingDate"][:4] for f in all_filings if f["filingDate"]), reverse=True)

        return render_template(
            "company.html",
            company=company_info,
            filings=filings,
            form_types=form_types,
            years=years,
            current_form=form_filter,
            current_year=year_filter,
            cik=company_info["cik"]
        )

    except Exception as e:
        return render_template(
            "error.html",
            error="Error fetching company data",
            message=str(e)
        ), 500


@app.route("/view/<ticker>/<accession>")
def view_filing(ticker: str, accession: str):
    """View a specific filing."""
    ticker = ticker.upper()
    view_mode = request.args.get("view", "focused")  # default to focused

    try:
        company_info = cik_resolver.get_company_info(ticker)
        if not company_info:
            return render_template(
                "error.html",
                error=f"Company not found: {ticker}"
            ), 404

        cik = company_info["cik"]

        # Get filing details
        filings_data = cik_resolver.get_company_filings(ticker=ticker)
        filing_info = None

        for f in filings_data.get("filings", []):
            if f["accessionNumber"] == accession:
                filing_info = f
                break

        if not filing_info:
            return render_template(
                "error.html",
                error=f"Filing not found: {accession}"
            ), 404

        # Construct the filing URL
        filing_url = cik_resolver.get_filing_url(
            cik,
            accession,
            filing_info.get("primaryDocument")
        )

        # Also get the index URL for the filing
        index_url = cik_resolver.get_filing_url(cik, accession)

        # Determine filing year for view mode decision
        filing_year = int(filing_info["filingDate"][:4]) if filing_info.get("filingDate") else 0

        # For filings after 2009 and focused view mode, parse and show focused view
        if filing_year > 2009 and view_mode == "focused":
            # Fetch the filing content
            headers = {
                "User-Agent": f"{sec_fetcher.company_name} {sec_fetcher.email}"
            }
            try:
                response = requests.get(filing_url, headers=headers, timeout=30)
                response.raise_for_status()
                html_content = response.text

                # Parse the filing
                parsed_data = filing_parser.parse_filing(
                    html_content,
                    filing_info.get("form", "10-K")
                )

                return render_template(
                    "filing_focused.html",
                    company=company_info,
                    filing=filing_info,
                    filing_url=filing_url,
                    index_url=index_url,
                    parsed_data=parsed_data
                )
            except requests.RequestException:
                # Fall back to full view if parsing fails
                pass

        # Default: full iframe view (for pre-2010 filings or explicit full view)
        return render_template(
            "filing.html",
            company=company_info,
            filing=filing_info,
            filing_url=filing_url,
            index_url=index_url
        )

    except Exception as e:
        return render_template(
            "error.html",
            error="Error loading filing",
            message=str(e)
        ), 500


@app.route("/api/search")
def api_search():
    """API endpoint for company search autocomplete."""
    query = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)

    if len(query) < 1:
        return jsonify([])

    results = search_companies(query, limit=limit)
    return jsonify(results)


@app.route("/api/company/<ticker>")
def api_company(ticker: str):
    """API endpoint to get company info and filings."""
    ticker = ticker.upper()
    form_types = request.args.get("forms", "").upper().split(",")
    form_types = [f.strip() for f in form_types if f.strip()]

    try:
        filings_data = get_company_filings(
            ticker=ticker,
            filing_types=form_types if form_types else None
        )
        return jsonify(filings_data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<ticker>")
def api_download(ticker: str):
    """API endpoint to trigger download of filings for a company."""
    ticker = ticker.upper()
    years = min(int(request.args.get("years", 20)), 25)
    forms = request.args.get("forms", "10-K,10-Q").upper().split(",")
    forms = [f.strip() for f in forms if f.strip()]

    try:
        results = sec_fetcher.download_filings(
            ticker=ticker,
            years=years,
            filing_types=forms
        )
        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/proxy/<ticker>/<accession>")
def proxy_filing(ticker: str, accession: str):
    """
    Proxy a filing from SEC to avoid CORS issues.
    This fetches the filing content and serves it locally.
    """
    ticker = ticker.upper()

    try:
        company_info = cik_resolver.get_company_info(ticker)
        if not company_info:
            return "Company not found", 404

        cik = company_info["cik"]

        # Get filing details
        filings_data = cik_resolver.get_company_filings(ticker=ticker)
        filing_info = None

        for f in filings_data.get("filings", []):
            if f["accessionNumber"] == accession:
                filing_info = f
                break

        if not filing_info:
            return "Filing not found", 404

        # Construct the filing URL
        filing_url = cik_resolver.get_filing_url(
            cik,
            accession,
            filing_info.get("primaryDocument")
        )

        # Fetch from SEC
        headers = {
            "User-Agent": f"{sec_fetcher.company_name} {sec_fetcher.email}"
        }
        response = requests.get(filing_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Determine content type
        content_type = response.headers.get("Content-Type", "text/html")

        return Response(
            response.content,
            content_type=content_type
        )

    except requests.RequestException as e:
        return f"Error fetching filing: {e}", 500
    except Exception as e:
        return f"Error: {e}", 500


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template(
        "error.html",
        error="Page Not Found",
        message="The requested page could not be found."
    ), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template(
        "error.html",
        error="Server Error",
        message="An internal error occurred. Please try again."
    ), 500


if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    print(f"Starting SEC Filing Browser on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
