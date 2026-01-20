
---

# Technical Specification: Professional Grade Financial Data Expansion

## 1. Project Objective

Upgrade the current `TargetFinancialAnalyzer` from a manual, single-year analysis to a professional-grade automated platform capable of 5-year annual (10-K) and 3-year quarterly (10-Q) trend analysis using direct SEC EDGAR integration.

## 2. Data Retrieval Specifications

* **Target Entity:** Target Corporation (CIK: `0000027419`).
* **Data Source:** Direct SEC EDGAR REST API (`https://data.sec.gov/submissions/CIK0000027419.json`).
* **Required Depth:**
* **10-K (Annual):** Last 5 fiscal years (FY2020–FY2024).
* **10-Q (Quarterly):** Last 12 quarters (8 quarters minimum for YoY comparisons).


* **Authentication/Fair Access:**
* Implement a professional `User-Agent` header in all requests: `[Your Name] [Your Email]`.
* Adhere to the SEC limit of 10 requests per second.



## 3. Implementation Steps for Claude Code

### Phase 1: Automated Data Acquisition

**Task:** Replace the manual file list in `financial_analyzer.py` with an automated downloader.

* **Library Recommendation:** Use `sec-edgar-downloader` or `python-edgar`.
* **Direction:** "Update `financial_analyzer.py` to use the `sec-edgar-downloader` library. Create a method `download_filings()` that retrieves the last five 10-Ks and twelve 10-Qs for CIK `0000027419`. Save these to the `data/` directory."

### Phase 2: Enhanced Analytical Logic

**Task:** Update the `TargetFinancialAnalyzer` class to process multi-year data.

* **Year-Over-Year (YoY) Comparisons:** Modify `analyze_10q` to compare the current quarter results against the *same* quarter from the previous year, rather than just the annual baseline.
* **Inventory Efficiency:** Add logic to calculate **Inventory Turnover Ratio** (`COGS / Average Inventory`) and **Days Sales of Inventory (DSI)** to track the clearance risk identified in Q3 2025.
* **Risk Trend Tracking:** Update `_extract_risk_flags` to create a "Risk Heatmap" data structure that counts mentions of "shrink," "theft," and "markdown" across all 5 years of 10-Ks.

### Phase 3: Visual Data Structuring

**Task:** Prepare the JSON output for professional visual modeling.

* **Direction:** "Refactor `export_json` to output a time-series friendly format. Ensure each entry includes a `fiscal_year` and `fiscal_quarter` key to allow for easy charting of 'Revenue vs. Inventory Growth' and 'Operating Margin Waterfall' steps."

## 4. Professional Report Structure (Output Requirements)

The final generated report must follow this professional hierarchy:

1. **Investment Thesis:** High-level "Bottom Line" (e.g., Target's margin recovery vs. inventory risk).
2. **Revenue & Channel Mix:** Breakdown of Store vs. Digital performance over 3 years.
3. **The "Margin Bridge":** Analysis of how Shrink and Markdowns have impacted the Operating Margin since FY2022.
4. **Solvency & Liquidity:** Debt maturity ladder and Interest Coverage trend (1.5x warning).
5. **Appendix:** Historical Data Tables (5-year view).

---

## Directions for Claude to Start

**Copy and paste the following into your Claude Code terminal:**

> "I need to upgrade this project to a professional standard. Please read the `financial_analyzer.py` file and the specifications in the provided markdown.
> 1. First, install `sec-edgar-downloader` and update the code to automatically fetch 5 years of 10-Ks and 12 quarters of 10-Qs for Target (CIK: 0000027419).
> 2. Update the analysis logic to perform Year-over-Year (YoY) comparisons for margins and sales.
> 3. Add 'Inventory Turnover' and 'Interest Coverage' to the vital signs extraction.
> 4. Finally, refactor the JSON output so it is ready for time-series visualization."
> 
>