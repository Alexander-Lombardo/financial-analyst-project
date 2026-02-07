# Claude Code Documentation

This document is designed for AI assistants (like Claude) to understand the Target Corporation Financial Analyzer project architecture, implementation details, and how to extend it.

## Project Overview

**Purpose**: Automated financial analysis tool that extracts metrics from SEC 10-K and 10-Q XBRL filings for Target Corporation.

**Key Features**:
- Automated SEC EDGAR filing downloads (10 years of 10-K, 12 quarters of 10-Q)
- XBRL/iXBRL parsing for financial data extraction
- Year-over-year trend analysis
- Inventory efficiency tracking
- Debt health monitoring
- Risk heatmap generation
- 24 interactive Plotly charts

**Tech Stack**:
- Python 3.x
- BeautifulSoup4 (HTML/XBRL parsing)
- sec-edgar-downloader (SEC EDGAR API client)
- python-dotenv (environment configuration)
- Plotly (interactive visualizations)
- yfinance (market data for Pillar 5)

## Project Structure

```
financial-analyst-project/
├── financial_analyzer.py       # Main analyzer (core logic)
├── visualize_data.py           # Plotly visualizations (24 charts)
├── sec_data_fetcher.py         # SEC EDGAR downloader
├── market_data_fetcher.py      # Yahoo Finance market data
├── peer_ccc_analyzer.py        # Peer company CCC extraction
├── thesis_generator.py         # Investment thesis auto-generation
├── create_presentation.py      # PowerPoint generation
├── cik_resolver.py             # Company CIK lookup and filing retrieval
├── app.py                      # SEC Filing Browser Flask app
├── filing_parser.py            # Financial statement parser
├── dupont_validation.py        # DuPont analysis validation tool
├── requirements.txt            # Python dependencies
├── .env                        # SEC credentials (git-ignored)
├── templates/                  # Flask HTML templates
│   ├── base.html
│   ├── index.html
│   ├── company.html
│   ├── filing_focused.html
│   └── error.html
├── static/css/                 # CSS styles
├── data/
│   ├── Target 10Q/sec-edgar-filings/  # Downloaded SEC filings (git-ignored)
│   ├── peer_filings/                  # Peer company SEC filings (git-ignored)
│   └── peer_comparison_data.json      # Peer CCC data
├── output/
│   ├── target_analysis.json           # Detailed format
│   ├── target_timeseries.json         # Time-series format
│   ├── target_summary.txt             # Human-readable summary
│   ├── chart_*.html                   # 24 interactive Plotly charts
│   ├── Target_Financial_Analysis.pptx # PowerPoint presentation
│   ├── dupont_validation.md           # DuPont analysis validation document
│   └── dupont_validation.html         # DuPont validation interactive report
└── test_*.py                          # Test suites
```

## Core Components

### 1. `financial_analyzer.py`

**Main class**: `TargetFinancialAnalyzer`

**Key Methods**:
- `__init__()` - Initializes analyzer, sets up quarterly history and risk heatmap tracking
- `analyze_10k()` - Extracts annual report data (vital_signs, inventory_metrics, debt_metrics)
- `analyze_10q()` - Extracts quarterly data with YoY comparison and risk flags
- `_extract_vital_signs()` - **CRITICAL**: Uses direct XBRL tag parsing (not table parsing)
- `_extract_xbrl_value()` - Dual-format support for modern iXBRL and legacy raw XML
- `_calculate_inventory_metrics()` - Inventory Turnover Ratio, Days Sales of Inventory
- `_calculate_debt_metrics()` - Interest Coverage, D/E, D/A, ROE, ROA, D/EBITDA
- `_calculate_liquidity_metrics()` - Current Ratio, Quick Ratio, Working Capital
- `_calculate_cashflow_metrics()` - FCF, FCF Margin, cash flow components
- `_compare_year_over_year()` - Q1 2025 vs Q1 2024, etc.
- `_extract_risk_flags()` - Tracks shrink, theft, markdown, margin_pressure mentions
- `export_timeseries_json()` - Time-series optimized JSON for Plotly

**GAAP Mappings** (key tags extracted):
| Category | GAAP Tags |
|----------|-----------|
| Revenue | `RevenueFromContractWithCustomerExcludingAssessedTax`, `Revenues`, `SalesRevenueNet` |
| Cost | `CostOfGoodsAndServicesSold`, `SellingGeneralAndAdministrativeExpense` |
| Income | `OperatingIncomeLoss`, `IncomeLossFromContinuingOperationsBeforeInterestExpenseInterestIncomeIncomeTaxesExtraordinaryItemsNoncontrollingInterestsNet` (legacy EBIT), `NetIncomeLoss` |
| Interest | `InterestExpense`, `InterestExpenseNonoperating` |
| Debt | `LongTermDebt`, `LongTermDebtAndCapitalLeaseObligations` (consolidated), `ShortTermBorrowings` |
| Cash Flow | `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment` |
| Balance Sheet | `AssetsCurrent`, `LiabilitiesCurrent`, `StockholdersEquity`, `Assets` |
| D&A | `DepreciationDepletionAndAmortization`, `Depreciation` |

### 2. `sec_data_fetcher.py`

**Main class**: `SECDataFetcher`

**Key Methods**:
- `download_filings()` - Downloads 10 10-Ks + 12 10-Qs from SEC EDGAR
- `_extract_period_from_file()` - Reads XBRL title tag, returns "FY2024", "Q1 2025", etc.
- `_extract_period_from_submission()` - Fallback for older filings using full-submission.txt

### 3. `visualize_data.py`

Creates 24 interactive Plotly charts. See [Chart Catalog](#chart-catalog) below.

### 4. `market_data_fetcher.py`

**Main class**: `MarketDataFetcher` (Yahoo Finance integration)

**Key Methods**:
- `get_current_prices()`, `get_historical_prices()` - Fetch stock prices
- `get_valuation_metrics()` - P/E, P/S, EV/EBITDA, dividend yield
- `get_historical_pe_for_quarters()` - Calculate Target historical P/E from SEC data
- Caching: 1 hour for prices, 24 hours for history

### 5. `peer_ccc_analyzer.py`

**Main class**: `PeerCCCAnalyzer` (Peer company Cash Conversion Cycle extraction)

**Purpose**: Downloads and analyzes peer company 10-K filings to extract CCC components (DSI, DSO, DPO) for competitive benchmarking against Target.

**Supported Peers**: Walmart (WMT), Amazon (AMZN), Costco (COST), Kroger (KR)

**Key Methods**:
- `analyze_peer()` - Download and extract multi-year CCC data for a peer
- `_extract_ccc_from_filing()` - Extract CCC components from single 10-K
- `_extract_xbrl_value()` - Reuses Target's dual-format XBRL extraction
- `_extract_inventory_from_table()` - Fallback for companies without XBRL inventory tags
- `_calculate_dsi()`, `_calculate_dso()`, `_calculate_dpo()` - CCC component formulas

**GAAP Tag Priority**:
- Revenue: Check `RevenueFromContractWithCustomerExcludingAssessedTax` first (ASC 606)
- COGS: Check `CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization` first (Kroger-specific)
- Inventory: Fallback chain includes `FIFOInventoryAmount`, `InventoryLIFO`

**Output**: `data/peer_comparison_data.json` with multi-year CCC data per company

### 6. SEC Filing Browser (`app.py` + `filing_parser.py`)

**Purpose**: Flask web application for browsing and viewing SEC filings with parsed financial statements.

**Main Components**:
- `app.py` - Flask routes for company search, filing list, and filing views
- `filing_parser.py` - Extracts and formats financial statements from SEC HTML

**Key Features**:
- Company search by ticker or name
- Filing list with form type and year filtering
- Focused view with tabbed financial statements
- Full filing view with original SEC content

**Financial Statement Parsing** (`FilingParser` class):

| Statement | Source Pattern | Output |
|-----------|---------------|--------|
| Income Statement | "Consolidated Statements of Operations/Income" | Revenue, expenses, net income |
| Balance Sheet | "Consolidated Balance Sheets" | Assets, liabilities, equity |
| Cash Flow | "Consolidated Statements of Cash Flows" | Operating/investing/financing |
| Shareholders' Equity | "Stockholders'/Shareholders' Equity/Investment" | Equity component changes |
| Retained Earnings | Extracted from equity statement | Beginning/ending balance, dividends |

**Retained Earnings Extraction** (handles both filing formats):
- **10-K (Annual)**: Extracts row-based "Retained Earnings:" section with beginning balance, net income, dividends, ending balance
- **10-Q (Quarterly)**: Extracts retained earnings from columnar equity statement using positional logic (4th numeric column is typically Retained Earnings)
- **Multi-row headers**: Checks first 3 rows of tables for header patterns to handle complex table structures
- **Company variations**: Supports both "Shareholders' Equity" (Home Depot) and "Shareholders' Investment" (Target) terminology

**Table Formatting**:
- `_build_clean_financial_table()` - Handles colspan misalignment in SEC HTML
- Extracts labels and numeric values intelligently
- Removes empty columns for readability

**Running the Browser**:
```bash
export PORT=5003  # Optional, defaults to 5000
python3 app.py
# Open http://localhost:5003
```

**URL Examples**:
- Search: `http://localhost:5003/search?q=apple`
- Company filings: `http://localhost:5003/company/HD`
- View filing: `http://localhost:5003/view/HD/0000354950-25-000085`

### 7. DuPont Validation Tool (`dupont_validation.py`)

**Purpose**: Validates DuPont analysis calculations with detailed side-by-side comparison and trend visualization.

**Key Features**:
- Uses average assets methodology for accurate ROA/ROE calculations
- Generates validation document with step-by-step calculations
- Creates 5-year trend chart comparing DuPont components

**Outputs**:
- `output/dupont_validation.md` - Detailed validation with formulas and values
- `output/dupont_validation.html` - Interactive validation report
- `output/chart_dupont_annual_trend.html` - 5-year trend line chart

**DuPont Components**:
- **Net Profit Margin**: Net Income / Revenue
- **Asset Turnover**: Revenue / Average Total Assets
- **Equity Multiplier**: Average Total Assets / Average Shareholders' Equity
- **ROE**: Net Profit Margin × Asset Turnover × Equity Multiplier

**Running**:
```bash
python3 dupont_validation.py
```

## Data Flow

```
1. python financial_analyzer.py
   ↓
2. SECDataFetcher downloads 10 10-Ks + 12 10-Qs → data/Target 10Q/sec-edgar-filings/
   ↓
3. TargetFinancialAnalyzer.run_analysis() processes each filing chronologically
   ↓
4. For each filing: _extract_vital_signs() → _calculate_*_metrics() → compare/flags
   ↓
5. Export: target_analysis.json, target_timeseries.json, target_summary.txt
   ↓
6. python visualize_data.py → 24 interactive HTML charts
```

## JSON Output Structure

**target_analysis.json** (top-level):
```json
{
  "filings": [...],
  "risk_heatmap": {...}
}
```

**Filing object**:
```json
{
  "period": "Q1 2025",
  "filing_type": "10-Q",
  "vital_signs": {
    "net_sales_billion": 23.846,
    "operating_margin_percent": 6.17,
    "vs_baseline": {...},
    "vs_year_ago": {...}
  },
  "inventory_metrics": {"inventory_turnover_ratio": 1.31, "days_sales_of_inventory": 278.1},
  "debt_metrics": {"interest_coverage_ratio": 12.23, "total_debt_billion": 3.61},
  "liquidity_metrics": {"current_ratio": 0.94, "quick_ratio": 0.18},
  "cashflow_metrics": {"free_cash_flow_billion": 2.84, "fcf_margin_percent": 8.5},
  "risk_flags": [...]
}
```

## How to Extend

### Adding New GAAP Metrics

1. Find the GAAP tag in a downloaded filing (inspect `<ix:nonFraction name="us-gaap:...">`)
2. Add to `GAAP_MAPPINGS` dict in `_extract_vital_signs()`
3. Value auto-extracted as `{metric_name}_billion`
4. Add derived calculations if needed

### Adding New Comparison Metrics

1. Create tracking dict in `__init__()`: `self.metric_history = {}`
2. Populate during analysis: `self.metric_history[period] = {...}`
3. Create comparison method using stored history

### Adding New Risk Patterns

1. Define regex pattern
2. Search in `_extract_risk_flags()` and populate `self.risk_heatmap`

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| XBRL values null | Different GAAP tags or legacy XML format | Add tag variants to GAAP_MAPPINGS; ensure `full-submission.txt` read |
| Older filings (FY2015-2018) NULL | Legacy raw XML without `<ix:nonfraction>` | Dual-format `_extract_xbrl_value()` handles this automatically |
| Quarter comparison fails | Period format mismatch | Check `sec_data_fetcher.py` returns "Q1 2025" format |
| Missing debt metrics | Normal for 10-Q | Only 10-K has full debt info |
| Debt shows partial value (e.g., $1B vs $14B) | Dimensional context extracted instead of consolidated | Use `LongTermDebtAndCapitalLeaseObligations` tag; filter for contexts without `_Axis_` |
| Legacy operating income NULL | FY2015-2017 use different GAAP tag | Add `IncomeLossFromContinuingOperations...` as fallback for EBIT |
| Peer inventory NULL | Company uses non-standard XBRL tag | `_extract_inventory_from_table()` fallback parses Balance Sheet HTML |
| Peer CCC abnormal (>200 days) | Wrong GAAP tag extracted (segment vs consolidated) | Check tag priority order; ASC 606 revenue tag first |
| Retained Earnings shows N/A | Equity statement uses different terminology | EQUITY_PATTERNS supports both "equity" and "investment" |
| Retained Earnings column misaligned | $ symbols and empty cells break column indexing | Uses positional extraction (4th numeric column) instead of column index |

## Development History

| Phase/Pillar | Status | Key Deliverable |
|--------------|--------|-----------------|
| Phase 1 | ✅ | SEC EDGAR auto-download, .env credentials |
| Phase 2 | ✅ | XBRL extraction, YoY comparison, risk heatmap, inventory/debt metrics |
| Phase 3 | ✅ | Time-series JSON, 7 Plotly charts, cash flow metrics |
| Phase 4 | ✅ | Investment thesis, margin bridge, risk charts, earnings quality |
| Phase 5 | ✅ | 10-year historical data (dual XBRL format for FY2015-2018) |
| Phase 6 | ✅ | Expense breakdown chart (SG&A extraction) |
| Phase 7 | ✅ | EBITDA bridge waterfall (D&A extraction) |
| Pillar 2 | ✅ | Liquidity & solvency ratios (Current/Quick Ratio, D/E, ROE/ROA), 3 charts |
| Pillar 3 | ✅ | DuPont analysis, CCC peer comparison, 2 charts |
| Pillar 4 | ✅ | Cash flow dynamics (FCF, Sankey), 2 charts |
| Pillar 5 | ✅ | Valuation metrics (P/E bands, peer scatter), 2 charts |
| Peer CCC | ✅ | Automated peer company CCC extraction (WMT, AMZN, COST, KR) |
| SEC Browser | ✅ | Flask web app for browsing filings with parsed financial statements |
| Retained Earnings | ✅ | Enhanced extraction from equity statements (row-based + columnar formats) |
| DuPont Validation | ✅ | DuPont analysis validation tool with average assets methodology |

## Testing & Verification

```bash
# Run analyzer
python3 financial_analyzer.py

# Generate visualizations (24 charts)
python3 visualize_data.py

# Generate investment thesis
python3 thesis_generator.py

# Create PowerPoint
python3 create_presentation.py

# Run test suites
python3 test_phase3_comprehensive.py      # 43 RTM requirements
python3 test_expense_breakdown_chart.py   # Phase 6
python3 test_ebitda_bridge_chart.py       # Phase 7
python3 test_pillar2_liquidity_solvency.py # 25 tests
python3 test_pillar3_operational_efficiency.py # 10 tests
python3 test_pillar4_cash_flow_dynamics.py # 18 tests
python3 test_pillar5_valuation_sentiment.py # 16 tests
python3 test_kroger_extraction.py         # Peer CCC extraction test

# Run peer CCC analyzer
python3 peer_ccc_analyzer.py              # Extract CCC for all peers

# Run DuPont validation
python3 dupont_validation.py              # Generate DuPont validation reports

# Run SEC Filing Browser
export PORT=5003
python3 app.py                            # Browse filings at http://localhost:5003
```

## Environment Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Edit with your SEC name/email
python3 financial_analyzer.py
python3 visualize_data.py
open output/chart_cash_flows.html
```

## Q4 Data Calculation

Target files 10-Q for Q1-Q3 only. Q4 is calculated from 10-K annual reports:

**Income Statement Items** (cumulative):
- Q4 = Annual - (Q1 + Q2 + Q3)
- Applies to: Revenue, COGS, SG&A, Net Income, Operating Income, Cash Flows

**Balance Sheet Items** (point-in-time):
- Q4 = FY year-end value directly from 10-K
- Applies to: Inventory, Current Assets, Current Liabilities, Total Assets, Equity

**YTD to Standalone Conversion** (for cash flows in 10-Q):
- Q1 = Q1 YTD (as-is)
- Q2 = Q2 YTD - Q1 YTD
- Q3 = Q3 YTD - Q2 YTD
- Q4 = Annual - Q3 YTD

## Chart Catalog

All 24 interactive Plotly charts created by `visualize_data.py`:

| # | Chart Name | File | Type | Purpose |
|---|------------|------|------|---------|
| 1 | Revenue vs Inventory | chart_revenue_vs_inventory.html | Dual-axis line | Identify inventory buildup |
| 2 | Revenue Growth YoY | chart_revenue_yoy_growth.html | Bars + line | Revenue with YoY % |
| 3 | Margin Analysis | chart_margin_analysis.html | 3-line | Gross/Operating/Net margins |
| 4 | Operating Margin Waterfall | chart_operating_margin_waterfall.html | Waterfall | Quarterly margin changes |
| 5 | Inventory Efficiency | chart_inventory_efficiency.html | Dual-axis | Turnover + DSI |
| 6 | Debt Health | chart_debt_health.html | Dual-axis | Coverage ratio + debt (10-year: FY2015-FY2024) |
| 7 | Cash Flows | chart_cash_flows.html | 3-line | OCF/ICF/FCF |
| 8 | Margin Bridge | chart_margin_bridge.html | Waterfall | Margin evolution Q1 2022→Q3 2025 |
| 9 | Risk Trends | chart_risk_trends.html | Stacked area | Risk mentions over time |
| 10 | Risk Heatmap | chart_risk_heatmap.html | Heatmap | Risk intensity by period |
| 11 | Earnings Quality | chart_earnings_quality.html | Bars + line | Net Income vs OCF |
| 12 | Revenue/NI Long-term | chart_revenue_netincome_longterm.html | Dual-axis | Quarterly with calc Q4 |
| 13 | Revenue/NI Annual | chart_revenue_netincome_annual.html | Dual-axis | 10-year FY2015-FY2024 |
| 14 | Expense Breakdown | chart_expense_breakdown.html | 100% stacked bar | COGS/SG&A/Other/OI |
| 15 | EBITDA Bridge | chart_ebitda_bridge.html | Waterfall + dropdown | Revenue→EBITDA flow |
| 16 | Current Ratio Gauge | chart_current_ratio_gauge.html | Gauge + dropdown | Liquidity health |
| 17 | Capital Structure | chart_capital_structure_donut.html | Donut + dropdown | Debt vs Equity |
| 18 | Debt-to-EBITDA | chart_debt_to_ebitda_trend.html | Line + markers | Leverage trend |
| 19 | DuPont Analysis | chart_dupont_analysis.html | Grouped bar + dropdown | ROE decomposition |
| 20 | Cash Conversion Cycle | chart_cash_conversion_cycle.html | Grouped bar + dropdown | CCC peer comparison |
| 21 | OCF vs CapEx | chart_ocf_vs_capex.html | Bars + line | FCF visualization |
| 22 | Cash Flow Sankey | chart_cash_flow_sankey.html | Sankey + dropdown | Cash allocation |
| 23 | Valuation Scatter | chart_valuation_scatter.html | Scatter + dropdown | P/E vs Growth |
| 24 | P/E Band | chart_pe_band.html | Area | Historical valuation zones |

**Notes**:
- Charts with "dropdown" have quarter/period selectors
- All charts display 15 quarters (Q1 2022 - Q3 2025) with calculated Q4
- PowerPoint has static PNG images; click "📊 Click for interactive version" for full HTML

## Data Verification

To verify extracted metrics against official Target quarterly reports:

### Quick Verification Steps

1. **Load time-series data**:
   ```bash
   cat output/target_timeseries.json | python3 -m json.tool
   ```

2. **Compare key metrics** against official 10-Q/10-K:
   - Revenue: `net_sales_billion` (in billions)
   - Operating Income: `operating_income_billion`
   - Net Income: `net_income_billion`
   - Gross Margin: `gross_margin_percent`
   - Operating Margin: `operating_margin_percent`

3. **Verify balance sheet items**:
   - Inventory: `inventory_billion`
   - Current Assets: `current_assets_billion`
   - Total Debt: `total_debt_billion`

### Common Verification Discrepancies

| Metric | Potential Issue | Resolution |
|--------|-----------------|------------|
| Revenue off by ~$0.1B | Rounding in XBRL scale attribute | Check `scale="6"` vs `scale="9"` |
| Q4 values seem wrong | Q4 is calculated (Annual - Q1-Q3) | Verify Q1-Q3 values are correct first |
| Cash flow negative | YTD-to-standalone conversion | Check cumulative math |
| Debt mismatch | Dimensional vs consolidated context | Verify consolidated context used |

### Source Documents

Official filings available at:
- SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000027419
- Target Investor Relations: https://investors.target.com/quarterly-results

## Key Learnings

### XBRL Parsing
- **Always use direct tag extraction** over table parsing (tables vary, XBRL tags are standardized)
- Handle `scale` attribute: `scale="6"` = multiply by 10^6
- Company-specific tags exist (Target uses `RevenueFromContractWithCustomerExcludingAssessedTax`)
- Legacy filings (FY2015-2018) use raw XML format without `<ix:nonfraction>` wrapper
- **Consolidated vs Dimensional contexts**: Prefer contexts WITHOUT segment/dimension elements for totals; dimensional contexts (with `_Axis_` in ID) contain breakdowns, not consolidated values

### Data Quality
- Quarterly debt data is sparse (10-K has full info)
- Q4 Operating Cash Flow can be negative when calculated from annual - cumulative
- Risk mentions are noisy ("promotional" can be positive or negative)

### Performance
- Parsing 17 filings: ~30-60 seconds
- Most time in BeautifulSoup HTML parsing

## Contact & Support

- GitHub issues: https://github.com/anthropics/claude-code/issues
- Include `output/target_analysis.json` snippet when reporting data issues

## License

Personal financial analysis tool - use at your own discretion. Educational purposes only.
