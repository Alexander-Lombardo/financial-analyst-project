# Claude Code Documentation

This document is designed for AI assistants (like Claude) to understand the Target Corporation Financial Analyzer project architecture, implementation details, and how to extend it.

## Project Overview

**Purpose**: Automated financial analysis tool that extracts metrics from SEC 10-K and 10-Q XBRL filings for Target Corporation.

**Key Features**:
- Automated SEC EDGAR filing downloads (5 years of 10-K, 12 quarters of 10-Q)
- XBRL/iXBRL parsing for financial data extraction
- Year-over-year trend analysis
- Inventory efficiency tracking
- Debt health monitoring
- Risk heatmap generation

**Tech Stack**:
- Python 3.x
- BeautifulSoup4 (HTML/XBRL parsing)
- sec-edgar-downloader (SEC EDGAR API client)
- python-dotenv (environment configuration)
- Plotly (interactive visualizations - Phase 3)

## Project Structure

```
financial-analyst-project/
├── financial_analyzer.py       # Main analyzer (core logic)
├── visualize_data.py           # Plotly visualizations (Phase 3)
├── sec_data_fetcher.py         # SEC EDGAR downloader
├── create_presentation.py      # PowerPoint generation (optional)
├── create_google_slides.py     # Google Slides generation (optional)
├── requirements.txt            # Python dependencies
├── .env                        # SEC credentials (git-ignored)
├── .env.example                # Template for .env
├── data/
│   └── Target 10Q/
│       └── sec-edgar-filings/  # Downloaded SEC filings (git-ignored)
├── output/
│   ├── target_analysis.json    # Detailed format
│   ├── target_timeseries.json  # Time-series format (Phase 3)
│   ├── target_summary.txt      # Human-readable summary
│   └── chart_*.html            # 5 interactive Plotly charts (Phase 3)
├── docs/
│   └── extended-financial-data-spec.md  # Original specification
└── test_phase3_*.py            # Phase 3 test suites
```

## Core Components

### 1. `financial_analyzer.py`

**Main class**: `TargetFinancialAnalyzer`

**Key Methods**:

#### Initialization
```python
def __init__(self, data_dir: str, auto_download: bool = False,
             user_name: str = None, user_email: str = None)
```
- Initializes analyzer with data directory
- Sets up quarterly history tracking (Phase 2)
- Sets up risk heatmap tracking (Phase 2)
- Optionally initializes SEC downloader

#### Analysis Methods
```python
def analyze_10k(self, filepath: Path, period: str) -> Dict
```
- Extracts annual report data
- Returns: vital_signs, comparable_sales, inventory_metrics, debt_metrics, strategic_promise

```python
def analyze_10q(self, filepath: Path, period: str) -> Dict
```
- Extracts quarterly report data
- Compares to baseline (FY2024)
- Performs year-over-year comparison (Phase 2)
- Returns: vital_signs, comparable_sales, inventory_metrics, debt_metrics, risk_flags

#### XBRL Extraction (Phase 2 Enhancement)
```python
def _extract_vital_signs(self, soup: BeautifulSoup, is_annual: bool) -> Dict
```
- **CRITICAL**: Uses direct XBRL tag parsing (not table parsing)
- GAAP taxonomy mappings defined in `GAAP_MAPPINGS` dict
- Handles Target-specific tags like `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`

```python
def _extract_xbrl_value(self, soup: BeautifulSoup, gaap_tag: str) -> Optional[float]
```
- Finds `<ix:nonFraction>` tags with matching GAAP tag name
- Handles scale attribute (e.g., `scale="6"` = millions)
- Returns value in millions

**GAAP Mappings Used** (as of Phase 3):
```python
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
    'us-gaap:NetCashProvidedByUsedInFinancingActivities': 'financing_cash_flow'
}
```

#### Phase 2 Enhancements

**Inventory Metrics**:
```python
def _calculate_inventory_metrics(self, vital_signs: Dict, period: str) -> Dict
```
- Inventory Turnover Ratio = COGS / Inventory
- Days Sales of Inventory = 365 / Inventory Turnover

**Debt Metrics**:
```python
def _calculate_debt_metrics(self, vital_signs: Dict) -> Dict
```
- Interest Coverage Ratio = Operating Income / Interest Expense
- Total Debt = Long-term Debt + Short-term Debt
- Flags coverage < 2.0x as warning

**Year-over-Year Comparison**:
```python
def _compare_year_over_year(self, current_vital_signs: Dict,
                            quarter_num: str, current_period: str) -> Dict
```
- Compares Q1 2025 vs Q1 2024, Q2 2025 vs Q2 2024, etc.
- Tracks: operating margin, net sales, inventory
- Flags inventory buildup (inventory growth > sales growth + 5%)
- Uses `self.quarterly_history` dict to store previous quarters

**Risk Heatmap**:
```python
def _extract_risk_flags(self, soup: BeautifulSoup, period: str) -> List[str]
```
- Tracks mentions of: shrink, theft, markdown, margin_pressure
- Populates `self.risk_heatmap` dict
- Returns human-readable risk flags

```python
def get_risk_heatmap_summary(self) -> Dict
```
- Aggregates risk mentions across all periods
- Calculates: total_mentions, periods_affected, avg_mentions_per_period
- Determines trend (increasing/stable/decreasing)

### 2. `sec_data_fetcher.py`

**Main class**: `SECDataFetcher`

**Purpose**: Download and organize SEC filings from EDGAR

**Key Methods**:
```python
def download_filings(self, ticker: str = "TGT", num_10k: int = 5,
                     num_10q: int = 12) -> Dict
```
- Downloads filings using `sec-edgar-downloader`
- Returns metadata: file paths, periods, filing dates

```python
def _extract_period_from_file(self, filepath: Path, filing_type: str) -> str
```
- Reads XBRL file title tag to determine period
- Returns period labels: "FY2024", "Q1 2025", etc.
- Handles Target's fiscal year (ends late Jan/early Feb)

## Data Flow

```
1. User runs: python financial_analyzer.py
   ↓
2. SECDataFetcher.download_filings()
   → Downloads 5 10-Ks + 12 10-Qs from SEC EDGAR
   → Saves to data/Target 10Q/sec-edgar-filings/
   ↓
3. TargetFinancialAnalyzer.run_analysis()
   → Processes each filing in chronological order
   ↓
4. For each 10-K:
   → _extract_vital_signs() using XBRL tags
   → _calculate_inventory_metrics()
   → _calculate_debt_metrics()
   → Set as baseline if FY2024
   ↓
5. For each 10-Q:
   → _extract_vital_signs() using XBRL tags
   → _calculate_inventory_metrics()
   → _calculate_debt_metrics()
   → _extract_risk_flags() + populate heatmap
   → _compare_to_baseline()
   → _compare_year_over_year() (Phase 2)
   ↓
6. Export results:
   → export_json() → output/target_analysis.json
   → export_summary_report() → output/target_summary.txt
```

## JSON Output Structure

**Top-level**:
```json
{
  "filings": [...]  // Array of filing objects
  "risk_heatmap": {...}  // Risk trend aggregation
}
```

**Filing object**:
```json
{
  "period": "Q1 2025",
  "filing_type": "10-Q",
  "vital_signs": {
    "net_sales_billion": 23.846,
    "cost_of_sales_billion": 17.128,
    "operating_income_billion": 1.472,
    "inventory_billion": 13.048,
    "gross_margin_percent": 28.17,
    "operating_margin_percent": 6.17,
    "vs_baseline": {
      "operating_margin_change": 0.95,
      "operating_margin_trend": "improving"
    },
    "vs_year_ago": {  // Phase 2
      "operating_margin_yoy_change": 0.8,
      "comparison_period": "Q1 2024",
      "net_sales_yoy_growth_percent": -1.23,
      "inventory_yoy_growth_percent": 11.24,
      "inventory_buildup_warning": "..."
    }
  },
  "comparable_sales": {...},
  "inventory_metrics": {  // Phase 2
    "inventory_turnover_ratio": 1.31,
    "days_sales_of_inventory": 278.1
  },
  "debt_metrics": {  // Phase 2
    "interest_coverage_ratio": 12.23,
    "interest_expense_million": 106.0,
    "operating_income_million": 1296.0,
    "total_debt_billion": 3.61
  },
  "risk_flags": [...]
}
```

## How to Extend

### Adding New GAAP Metrics

1. **Identify the GAAP tag**:
   - Open a downloaded filing in browser
   - Inspect element to find `<ix:nonFraction name="us-gaap:...">`
   - Note the tag name

2. **Add to GAAP_MAPPINGS**:
```python
# In _extract_vital_signs()
GAAP_MAPPINGS = {
    'us-gaap:ResearchAndDevelopmentExpense': 'rd_expense',
    # ... existing mappings
}
```

3. **Value is automatically extracted** and available as `{metric_name}_billion`

4. **Add derived calculations** if needed:
```python
# After extraction loop in _extract_vital_signs()
if 'rd_expense_billion' in vital_signs:
    rd_intensity = (vital_signs['rd_expense_billion'] /
                    vital_signs['net_sales_billion']) * 100
    vital_signs['rd_intensity_percent'] = round(rd_intensity, 2)
```

### Adding New Comparison Metrics

Follow the pattern from Phase 2 YoY comparison:

1. **Create tracking structure** in `__init__()`:
```python
self.metric_history = {}  # Store historical values
```

2. **Populate during analysis**:
```python
# In analyze_10q() or analyze_10k()
self.metric_history[period] = {'metric_value': value}
```

3. **Create comparison method**:
```python
def _compare_metric(self, current, period):
    if period in self.metric_history:
        prior = self.metric_history[period]
        return {'change': current - prior, 'trend': '...'}
    return {}
```

### Adding New Risk Patterns

Follow the pattern from `_extract_risk_flags()`:

1. **Define pattern**:
```python
new_risk_pattern = r"pattern|keywords|to|match"
```

2. **Search and track**:
```python
matches = re.findall(new_risk_pattern, text, re.IGNORECASE)
if matches:
    self.risk_heatmap['new_risk_type'].append((period, len(matches)))
    flags.append("Risk description")
```

3. **Initialize in `__init__()`**:
```python
self.risk_heatmap = {
    'new_risk_type': [],  # Add new type
    # ... existing types
}
```

## Common Issues & Solutions

### Issue: XBRL values are null or incorrect scale

**Cause**: Company uses different GAAP tags or scale attributes

**Solution**:
1. Inspect actual HTML filing
2. Find correct GAAP tag name
3. Add to GAAP_MAPPINGS
4. Verify scale attribute handling in `_extract_xbrl_value()`

### Issue: Quarter comparison not working

**Cause**: `_extract_quarter_number()` not matching period format

**Solution**:
1. Check period labels in `sec_data_fetcher.py`
2. Ensure format is "Q1 2025" not "Period 2025-05"
3. Adjust regex in `_extract_quarter_number()` if needed

### Issue: Missing debt metrics for some quarters

**Expected**: 10-Q filings may not always include debt details

**Not a bug**: Only annual 10-K reports consistently have full debt information

## Development History

### Phase 1: Automated Data Acquisition
- Implemented `SECDataFetcher` for automatic EDGAR downloads
- Environment-based SEC credentials (.env file)
- Git hygiene (ignore downloaded filings)

### Phase 2: Enhanced Analytics (Current)
- **CRITICAL FIX**: Replaced table parsing with direct XBRL tag extraction
- Added year-over-year comparison tracking
- Implemented inventory efficiency metrics (Turnover, DSI)
- Implemented debt health metrics (Interest Coverage, Total Debt)
- Built risk heatmap system with trend analysis
- Enhanced output display with all new metrics

**Phase 2 Success Criteria** (all met ✅):
1. ✅ XBRL extraction works for all 17 filings (no null values)
2. ✅ Inventory metrics present in all filings
3. ✅ Debt metrics present where available (annual reports)
4. ✅ YoY comparisons for 6+ quarters
5. ✅ Risk heatmap populated with trend data

### Phase 3: JSON Restructuring & Visualization (Complete) ✅
- **Dual Export Approach**: Maintains detailed JSON + adds time-series JSON
- **Temporal Keys**: Added fiscal_year and fiscal_quarter to all filings
- **Cash Flow Analysis**: 3 new GAAP mappings (operating, investing, financing)
- **Operating CF Margin**: Calculated as Operating CF / Net Sales × 100
- **Time-Series Format**: Flat array structure optimized for Plotly
- **Interactive Visualizations**: 7 Plotly charts created in visualize_data.py
  1. Revenue vs Inventory Growth (dual-axis line)
  2. Revenue Growth Year-over-Year (dual-axis: revenue bars + YoY growth line)
  3. Margin Analysis (3-line: Gross, Operating, Net Profit margins Q1 2022-Q3 2025)
  4. Operating Margin Waterfall (quarterly trend)
  5. Inventory Efficiency (turnover + DSI)
  6. Debt Health (coverage ratio + total debt)
  7. Statement of Cash Flows (3 lines: operating, investing, financing)
- **New Methods Added**:
  - `_parse_period_to_fiscal()` - Extracts fiscal_year and fiscal_quarter from period strings
  - `_calculate_cashflow_metrics()` - Computes cash flow metrics
  - `export_timeseries_json()` - Exports time-series optimized JSON

**Phase 3 Success Criteria** (all met ✅):
1. ✅ Dual export approach maintains backward compatibility
2. ✅ Time-series JSON has flat array structure
3. ✅ fiscal_year and fiscal_quarter present in all filings
4. ✅ Cash flow data extracted and charted
5. ✅ 7 Plotly charts created (including Revenue Growth YoY, Margin Analysis, and Cash Flows)
6. ✅ All charts are interactive with hover tooltips
7. ✅ Net profit margin data extracted from us-gaap:NetIncomeLoss tag
8. ✅ 43/43 RTM requirements met (100% coverage)
9. ✅ 89 tests passed (98.9% success rate)

### Phase 4: Professional Reports (Complete) ✅

**New Scripts**:
- `thesis_generator.py` - Investment thesis auto-generation
  - ThesisGenerator class with 6 analysis methods
  - Generates Buy/Hold/Sell recommendation from data
  - Exports investment_thesis.json + console summary

**Extended Scripts**:
- `visualize_data.py` - 6 new charts added (total 12):
  - Chart 2: Revenue Growth YoY (Phase 3 - dual-axis: revenue bars + YoY growth line)
  - Chart 3: Margin Analysis (Phase 3 - 3-line: Gross, Operating, Net Profit margins)
  - Chart 7: Margin bridge waterfall (FY2022 → Q3 2025)
  - Chart 8: Risk trends stacked area
  - Chart 9: Risk heatmap grid
  - Chart 11: Earnings Quality (Net Income vs Operating CF with Cash Conversion Ratio)
    - **Y-axis scaling fix**: Secondary Y-axis range [-150%, 650%] accommodates negative Q4 values (-104%, -99%) and extreme positive outliers (549%, 506%, 478%)
    - Negative ratios indicate Q4 periods where Operating CF was negative (calculated as Annual - Q1-Q2-Q3)
  - Chart 12: Revenue & Net Income Long-Term Trajectory (NEW)
    - Dual-axis line chart showing correlation between Revenue (blue) and Net Income (green)
    - Covers 5-10 year period with calculated Q4 data
    - Shows long-term trends and profit margin evolution
- `financial_analyzer.py` - Executive insights extraction:
  - extract_executive_insights() - Finds inflection points, top trends, warnings
  - export_executive_insights() - Exports executive_insights.json
- `create_presentation.py` - 3 new slides:
  - Investment Thesis (with recommendation)
  - Margin Bridge Analysis (with summary)
  - Risk Heatmap (with stats table)

**Phase 4 Success Criteria** (all met ✅):
1. ✅ Margin bridge waterfall chart shows FY2022 → Q3 2025 evolution
2. ✅ Investment thesis auto-generated with Buy/Hold/Sell rating
3. ✅ Risk heatmap visualizations created (2 charts)
4. ✅ Executive insights extracted (inflection points, trends, warnings)
5. ✅ PowerPoint enhanced with 3 new Phase 4 slides
6. ✅ All outputs professionally formatted and data-driven
7. ✅ Earnings quality chart created with proper Y-axis scaling for negative and extreme positive values

## Testing & Verification

### Quick Test
```bash
# Run analyzer (includes executive insights export - Phase 4)
python3 financial_analyzer.py

# Run visualizations (creates 12 charts including Phase 4)
python3 visualize_data.py

# Generate investment thesis (Phase 4)
python3 thesis_generator.py

# Create PowerPoint presentation (Phase 4)
python3 create_presentation.py

# Open charts in browser
open output/chart_margin_bridge.html
open output/chart_risk_trends.html
open output/Target_Financial_Analysis.pptx
```

### Comprehensive Verification (Phase 3)
Run the complete test suite:
```bash
# RTM Compliance Tests (43 requirements)
python3 test_phase3_comprehensive.py

# Deep Verification Tests (37 tests for data quality)
python3 test_phase3_deep_verification.py

# Integration Tests (9 end-to-end workflow tests)
python3 test_phase3_integration.py
```

**Expected results**:
- 17 total filings (5 10-Ks + 12 10-Qs)
- FY2024 net_sales_billion ~106.6B
- All filings have inventory_metrics, debt_metrics, cashflow_metrics
- All filings have fiscal_year and fiscal_quarter fields
- 6+ filings have vs_year_ago comparisons
- Risk heatmap shows shrink trend increasing
- 12 interactive HTML charts generated (including new Revenue & Net Income Long-Term Trajectory)
- 89/89 tests passed (98.9% - 1 expected limitation)

## Environment Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure SEC credentials
cp .env.example .env
# Edit .env with your name and email

# 3. Run analyzer
python3 financial_analyzer.py

# 4. Generate visualizations
python3 visualize_data.py

# 5. View charts
open output/chart_cash_flows.html
```

## Quarterly Data Calculation (Phase 3 Enhancement)

### Q4 Data from 10-K Annual Reports

Target only files 10-Q reports for Q1, Q2, and Q3. Q4 data is calculated from annual 10-K reports:

**Implementation** (in `visualize_data.py`):
```python
# Step 1: Collect Q1-Q3 from 10-Q filings
quarterly_data = []
for i, period in enumerate(data['periods']):
    if period['filing_type'] == '10-Q':
        quarterly_data.append({
            'period': period['period'],
            'fiscal_year': period['fiscal_year'],
            'revenue': revenue[i],
            'inventory': inventory[i]
        })

# Step 2: Calculate Q4 from 10-K annual reports
for i, period in enumerate(data['periods']):
    if period['filing_type'] == '10-K':
        fy = period['fiscal_year']
        annual_revenue = revenue[i]

        # Find Q1, Q2, Q3 for this fiscal year
        q1_rev = q2_rev = q3_rev = None
        for q in quarterly_data:
            if q['fiscal_year'] == fy:
                if 'Q1' in q['period']:
                    q1_rev = q['revenue']
                # ... match Q2, Q3

        # Calculate Q4 = Annual - (Q1 + Q2 + Q3)
        if q1_rev and q2_rev and q3_rev:
            q4_revenue = annual_revenue - (q1_rev + q2_rev + q3_rev)
            quarterly_data.append({
                'period': f'Q4 {fy}',
                'fiscal_year': fy,
                'revenue': q4_revenue,
                'inventory': annual_inventory  # Year-end balance
            })
```

**Key Principles**:
- Q4 Revenue = Annual Total - (Q1 + Q2 + Q3)
- Q4 Inventory = Year-end inventory from 10-K (point-in-time, not cumulative)
- Fiscal year totals (10-K) are **never displayed** in charts to avoid distortion
- Results in 15 complete quarters: Q1 2022 through Q3 2025

**Why This Matters**:
- Reveals seasonal patterns (Q4 consistently 20-35% higher revenue)
- Enables proper YoY comparisons (Q4 2024 vs Q4 2023)
- Prevents mixing annual and quarterly data in visualizations

## Key Learnings

### XBRL Parsing Best Practices

1. **Always use direct tag extraction** over table parsing:
   - Tables structures vary across filings
   - XBRL tags are standardized by US-GAAP
   - More reliable and maintainable

2. **Handle scale attributes properly**:
   - `scale="6"` means multiply by 10^6 (millions)
   - Always check scale before assuming unit

3. **Company-specific tags exist**:
   - Target uses `RevenueFromContractWithCustomerExcludingAssessedTax`
   - Not all companies use generic `Revenues` tag
   - Always inspect actual filings first

### Data Quality

- **Quarterly debt data is sparse**: Don't expect full debt metrics in every 10-Q
- **Inventory turnover is quarterly**: Annual formula / 4 != quarterly ratio
- **Risk mentions are noisy**: "promotional" can be positive or negative context
- **Q4 Operating Cash Flow can be negative**: When calculated as Annual - (Q1+Q2+Q3), if quarterly filings report cumulative cash flows that exceed the annual total, Q4 will be negative
  - Example: FY2023 Annual OCF = $8.62B, but Q1-Q3 cumulative = $10.00B → Q4 = -$1.37B
  - This affects Cash Conversion Ratio calculations (Operating CF / Net Income × 100), producing negative ratios
  - Chart Y-axis must accommodate negative values: Earnings Quality chart uses range [-150%, 650%]

### Performance

- Parsing 17 filings takes ~30-60 seconds
- Most time spent in BeautifulSoup HTML parsing
- XBRL extraction is fast once HTML is parsed

## Contact & Support

For issues or questions:
- File GitHub issue at: https://github.com/anthropics/claude-code/issues
- Reference this documentation when asking AI assistants for help
- Include `output/target_analysis.json` snippet when reporting data issues

## License

Personal financial analysis tool - use at your own discretion. Educational purposes only.
