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

## Project Structure

```
financial-analyst-project/
├── financial_analyzer.py       # Main analyzer (core logic)
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
│   ├── target_analysis.json    # Structured analysis output
│   └── target_summary.txt      # Human-readable summary
└── docs/
    └── extended-financial-data-spec.md  # Original specification
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

**GAAP Mappings Used** (as of Phase 2):
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
    'us-gaap:DebtCurrent': 'short_term_debt'
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

### Phase 3: JSON Restructuring (Planned)
- Time-series friendly format
- Pre-calculated period-over-period deltas
- Normalized metric names for charting

### Phase 4: Professional Reports (Planned)
- Margin bridge analysis (waterfall charts)
- Investment thesis generation
- Executive summary with key insights

## Testing & Verification

### Quick Test
```bash
python financial_analyzer.py
# Check console output for new metrics
```

### Comprehensive Verification
Run the test suite from the plan file:
```bash
# Test 1: JSON structure
python3 -c "import json; ..."

# Test 2-5: See docs/phase-2-plan.md
```

**Expected results**:
- 17 total filings (5 10-Ks + 12 10-Qs)
- FY2024 net_sales_billion ~106.6B
- All filings have inventory_metrics
- 6+ filings have vs_year_ago comparisons
- Risk heatmap shows shrink trend increasing

## Environment Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure SEC credentials
cp .env.example .env
# Edit .env with your name and email

# 3. Run analyzer
python financial_analyzer.py
```

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
