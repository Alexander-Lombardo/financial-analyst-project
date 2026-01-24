# Target Corporation Financial Analyzer

Automated SEC filing analysis tool that extracts financial metrics from 10-K and 10-Q XBRL filings and generates comprehensive reports.

## Overview

This analyzer implements a **three-phase approach** to financial analysis:

### Phase 1: The Baseline (10-K Analysis)
Extracts "Vital Signs" from the annual 10-K report:
- **Net Sales** (Target's renamed "Total Revenue")
- **Gross Margin %** = (Net Sales - Cost of Sales) / Net Sales
- **Operating Margin %** = Operating Income / Net Sales ⭐ **Key Metric**
- **Comparable Sales** breakdown:
  - Total Comp Sales %
  - Store-Originated Comp Sales %
  - Digitally-Originated Comp Sales %
- **Inventory Level** (total $ at period end)

Also extracts:
- CEO's Top 3 Strategic Priorities
- Top 2 Risk Factors from Item 1A

### Phase 2: Enhanced Analytics (10-Q Quarterly Analysis)
Comprehensive trend analysis with multiple comparison methods:

**Year-over-Year Comparisons:**
- Compares Q1 2025 vs Q1 2024, Q2 2025 vs Q2 2024, etc.
- Tracks operating margin YoY changes
- Identifies sales growth vs inventory growth mismatches
- Flags inventory buildup warnings (inventory growing >5% faster than sales)

**Inventory Efficiency Metrics:**
- **Inventory Turnover Ratio** = COGS / Inventory
- **Days Sales of Inventory (DSI)** = 365 / Inventory Turnover
- Tracks how quickly Target is moving inventory

**Debt Health Monitoring:**
- **Interest Coverage Ratio** = Operating Income / Interest Expense
- **Total Debt** tracking (long-term + short-term)
- Flags coverage ratios below 2.0x (warning threshold)

**Risk Heatmap Tracking:**
- Counts mentions of "shrink", "theft", "markdown" across all periods
- Identifies trend direction (increasing/stable/decreasing)
- Provides average mentions per period for risk assessment

### Phase 3: JSON Restructuring & Visualization (Complete)

**Dual Export Approach:**
- Detailed JSON format (backward compatible)
- Time-series JSON format (optimized for Plotly charting)

**New Features:**
- **Temporal Keys**: `fiscal_year` and `fiscal_quarter` in all filing objects
- **Cash Flow Analysis**: Operating, Investing, and Financing cash flows extracted
- **Interactive Visualizations**: 5 Plotly charts with hover tooltips

**Cash Flow Metrics:**
```json
{
  "cashflow_metrics": {
    "operating_cash_flow_billion": 10.525,
    "investing_cash_flow_billion": 2.591,
    "financing_cash_flow_billion": 2.0,
    "operating_cash_flow_margin_percent": 11.39
  }
}
```

**Time-Series Format Example:**
```json
{
  "metadata": {
    "company": "Target Corporation",
    "ticker": "TGT",
    "total_periods": 17
  },
  "periods": [
    {
      "period": "Q1 2025",
      "fiscal_year": 2025,
      "fiscal_quarter": 1,
      "filing_type": "10-Q"
    }
  ],
  "metrics": {
    "revenue": {
      "net_sales_billion": [92.4, 104.611, ...],
      "yoy_growth_percent": [null, null, ...]
    },
    "cash_flows": {
      "operating_cash_flow_billion": [10.525, 8.625, ...],
      "investing_cash_flow_billion": [2.591, 3.154, ...],
      "financing_cash_flow_billion": [2.0, 8.071, ...]
    }
  }
}
```

**7 Interactive Charts:**
1. Revenue vs Inventory Growth (dual-axis line, **15 quarters Q1 2022-Q3 2025 including calculated Q4**)
2. Revenue Growth Year-over-Year (dual-axis: revenue bars + YoY growth % line, **15 quarters with Q4**)
3. **Margin Analysis** (3-line chart: Gross, Operating, Net Profit margins, **15 quarters Q1 2022-Q3 2025**)
4. Operating Margin Waterfall (quarterly trend)
5. Inventory Efficiency (turnover + DSI)
6. Debt Health (coverage ratio + total debt)
7. Statement of Cash Flows (3 lines: operating, investing, financing)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd financial-analyst-project

# Install dependencies
pip install -r requirements.txt

# Configure SEC credentials
cp .env.example .env
# Edit .env with your name and email (required by SEC)
```

**Dependencies:**
- `beautifulsoup4` - HTML/XBRL parsing
- `lxml` - XML processing
- `sec-edgar-downloader` - Automated SEC filing downloads
- `python-dotenv` - Environment variable management
- `plotly` - Interactive visualizations (Phase 3)
- `pandas` (optional) - Future data analysis
- `numpy` (optional) - Future calculations

## Usage

### Quick Start

```bash
# Run the analyzer (automatically downloads SEC filings)
python financial_analyzer.py

# Generate interactive visualizations
python visualize_data.py

# Generate investment thesis (Phase 4)
python thesis_generator.py

# Create PowerPoint presentation (Phase 4)
python create_presentation.py
```

The analyzer will automatically:
1. **Download** 5 years of 10-K reports and 12 quarters of 10-Q reports from SEC EDGAR
2. **Extract** financial metrics from each filing using XBRL parsing
3. **Analyze** trends and compare against baseline
4. **Export** results to:
   - `output/target_analysis.json` (detailed format)
   - `output/target_timeseries.json` (time-series format)
   - `output/target_summary.txt` (human-readable report)
   - `output/executive_insights.json` (key insights for reports - Phase 4)

The visualization script will generate:
- 10 interactive HTML charts in the `output/` directory (7 from Phase 3 + 3 from Phase 4)
- Charts include hover tooltips, zoom, and pan features
- Open any `.html` file in your browser to view

The thesis generator (Phase 4) will produce:
- Auto-generated investment thesis with Buy/Hold/Sell recommendation
- Risk factor analysis and opportunity identification
- Exported to `output/investment_thesis.json`

The presentation generator (Phase 4) will create:
- Professional PowerPoint with 11 slides including Phase 4 enhancements
- Investment thesis, margin bridge, and risk heatmap slides
- Links to all 10 interactive charts

### SEC Credentials Setup

The SEC requires all automated downloads to include contact information in the User-Agent header. This is part of their [fair access policy](https://www.sec.gov/os/webmaster-faq#code-support).

**No account needed!** Just provide your name and email:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your information:
   ```
   SEC_USER_NAME="Your Name"
   SEC_USER_EMAIL="your.email@example.com"
   ```

3. The `.env` file is git-ignored for security.

### Data Structure (Automated)

After the first run, SEC filings are organized automatically:

```
financial-analyst-project/
├── data/
│   └── Target 10Q/
│       └── sec-edgar-filings/          # Auto-downloaded (git-ignored)
│           └── TGT/
│               ├── 10-K/
│               │   ├── 0000027419-25-000018/
│               │   │   └── primary-document.html
│               │   └── ... (5 years)
│               └── 10-Q/
│                   ├── 0000027419-25-000101/
│                   │   └── primary-document.html
│                   └── ... (12 quarters)
├── output/
│   ├── target_analysis.json            # Detailed format
│   ├── target_timeseries.json          # Time-series format (Phase 3)
│   ├── target_summary.txt              # Human-readable report
│   ├── chart_revenue_vs_inventory.html # Interactive charts (Phase 3)
│   ├── chart_revenue_growth_yoy.html   # Revenue Growth YoY (Phase 3)
│   ├── chart_operating_margin_waterfall.html
│   ├── chart_inventory_efficiency.html
│   ├── chart_debt_health.html
│   └── chart_cash_flows.html
├── financial_analyzer.py               # Main analyzer
├── visualize_data.py                   # Plotly visualizations (Phase 3)
├── sec_data_fetcher.py                 # SEC EDGAR downloader
└── .env                                # Your credentials (git-ignored)
```

### Output Files

**1. `target_analysis.json`** (Detailed Format)
- Complete structured data for all periods
- Includes fiscal_year and fiscal_quarter fields
- Cash flow metrics (operating, investing, financing)
- Backward compatible with Phase 2
- Machine-readable format

**2. `target_timeseries.json`** (Time-Series Format - Phase 3)
- Flat array structure optimized for Plotly
- Parallel arrays indexed by period
- 6 metric categories: revenue, margins, inventory, debt, comparable_sales, cash_flows
- Ideal for charting and data visualization
- 65% smaller file size

**3. `executive_insights.json`** (Phase 4)
- Inflection points (>50bp margin changes)
- Top YoY trends (strongest/weakest metrics)
- Critical warnings (debt coverage, inventory risks)
- Auto-generated insights for reports

**4. `investment_thesis.json`** (Phase 4)
- Auto-generated Buy/Hold/Sell recommendation
- Risk factor analysis (severity, trend, evidence)
- Opportunity identification (digital growth, margin recovery)
- Current state analysis with 3-year comparisons

**5. Interactive Charts** (Phases 3 & 4)
- 9 HTML files with embedded Plotly visualizations
- Phase 3: Revenue vs Inventory, Revenue Growth YoY, Operating Margin, Inventory Efficiency, Debt Health, Cash Flows
- Phase 4: Margin Bridge (waterfall), Risk Trends, Risk Heatmap Grid
- Fully interactive: hover tooltips, zoom, pan
- No external dependencies - open directly in browser
- Professional presentation quality

**6. PowerPoint Presentation** (Phase 4)
- `Target_Financial_Analysis.pptx` - Enhanced 11-slide deck
- Investment Thesis slide with color-coded recommendation
- Margin Bridge Analysis slide with FY2022 → Q3 2025 summary
- Risk Heatmap slide with shrink/markdown statistics
- Links to all 9 interactive charts

## Understanding the Analysis

### Key Metrics Explained

**Operating Margin %** ⭐ **Most Important**
- Formula: Operating Income / Net Sales
- Best indicator of operational efficiency
- Target's core profitability metric
- Compare quarter-over-quarter to detect trends

**Gross Margin %**
- Formula: (Net Sales - Cost of Sales) / Net Sales
- Measures pricing power and product mix
- Declining gross margin = potential markdowns or shrink

**Comparable Sales**
- Same-store sales growth (excludes new stores)
- **Store-Originated**: Physical retail health
- **Digitally-Originated**: E-commerce health (includes in-store pickup)
- Split shows channel shift dynamics

**Inventory Level**
- Total inventory value at period end
- Compare to sales to calculate inventory turnover
- Rising inventory + falling sales = clearance risk

**Inventory Turnover Ratio** (Phase 2)
- Formula: COGS / Inventory
- Measures how many times inventory is sold and replaced
- Higher is better (faster inventory movement)
- Target's typical range: 5-6x annually, ~1.2-1.5x quarterly

**Days Sales of Inventory (DSI)** (Phase 2)
- Formula: 365 / Inventory Turnover Ratio
- Average number of days to sell inventory
- Lower is better (faster turnover)
- Target's typical range: 60-70 days annually, ~240-300 days quarterly

**Interest Coverage Ratio** (Phase 2)
- Formula: Operating Income / Interest Expense
- Measures ability to pay interest on debt
- Healthy range: Above 2.5x
- Warning threshold: Below 2.0x
- Critical: Below 1.5x

### Risk Flags

The analyzer automatically flags:

1. **Markdown Pressure**: Gross margin decline > 0.5%
2. **Shrink/Theft**: Mentions in MD&A with basis point impact
3. **Margin Compression**: Operating margin decline vs. baseline

## Customization

### Modifying Extraction Logic

Edit `financial_analyzer.py` to customize:

**Add new GAAP mappings:**
```python
# In the GAAP_MAPPINGS dictionary
GAAP_MAPPINGS = {
    # Add new taxonomy mappings
    'us-gaap:ResearchAndDevelopmentExpense': 'rd_expense',
    'us-gaap:CapitalExpenditures': 'capex',
    # ... existing mappings
}
```

**Modify calculation logic:**
```python
def calculate_vital_signs(self, data: Dict) -> Dict:
    # Add custom calculations
    vital_signs['free_cash_flow'] = (
        data.get('operating_cash_flow', 0) -
        data.get('capex', 0)
    )
    return vital_signs
```

## Troubleshooting

### Missing Data

**Problem**: Some metrics return `None` or missing values

**Cause**: XBRL tags may use different taxonomy names or be structured differently

**Solution**:
1. Open the .htm file in browser
2. Inspect the element to find the actual `<ix:nonFraction>` tag
3. Check the `name` attribute (e.g., `us-gaap:Revenues`)
4. Add the mapping to `GAAP_MAPPINGS` dictionary in [financial_analyzer.py](financial_analyzer.py)

### Incorrect Values

**Problem**: Numbers seem wrong or scaled incorrectly

**Cause**: XBRL values may be in different units (millions vs billions)

**Solution**: Check the `scale` and `unitRef` attributes in the XBRL tags:
```python
# Look for scale attribute: scale="-6" means millions
<ix:nonFraction name="us-gaap:Revenues"
                contextRef="..."
                unitRef="usd"
                decimals="-6"
                scale="6">106580000000</ix:nonFraction>
```

## Processing Order

Files are processed in this **specific order** for accurate trend analysis:

1. **2024 10-K** → Sets baseline `operating_margin_percent`
2. **Q1 2025 10-Q** → Compare Q1 Operating Margin vs Baseline
3. **Q2 2025 10-Q** → Compare Q2 Operating Margin vs Q1
4. **Q3 2025 10-Q** → Compare Q3 Operating Margin vs Q2

This creates a chronological trend line.

### Q4 Data Calculation

Q4 quarterly data is **calculated from 10-K annual reports** since Target only files 10-Q for Q1-Q3:

- **Q4 Revenue** = Annual Revenue (10-K) - (Q1 + Q2 + Q3 Revenue from 10-Q)
- **Q4 Inventory** = Year-end inventory balance from 10-K (point-in-time metric)

This approach:
- Provides complete quarterly coverage (15 quarters: Q1 2022 - Q3 2025)
- Excludes fiscal year totals from charts to prevent distortion
- Reveals seasonal patterns (Q4 typically 20-35% higher due to holidays)

## Additional Tools

### Presentation Generation

Generate presentation materials from analysis results:

```bash
# Create Google Slides compatible HTML/JSON/Markdown
python create_google_slides.py
```

Outputs to `output/`:
- `Target_Financial_Analysis.html` - HTML presentation (print to PDF for Google Slides import)
- `target_presentation_data.json` - Structured presentation data
- `Target_Financial_Analysis.md` - Markdown format

### PowerPoint Generation (Alternative)

```bash
python create_presentation.py
```

Generates `output/Target_Financial_Analysis.pptx` with charts and data tables.

## Roadmap

### ✅ Phase 1: Automated Data Acquisition (Complete)
- Automated SEC EDGAR filing downloads
- 5 years of 10-K annual reports
- 12 quarters of 10-Q quarterly reports
- Environment-based credential management

### ✅ Phase 2: Enhanced Analytics (Complete)
- ✅ Year-over-year comparisons (Q1 2025 vs Q1 2024, etc.)
- ✅ Inventory turnover ratio and Days Sales of Inventory (DSI)
- ✅ Interest coverage ratio and total debt tracking
- ✅ Risk heatmap with trend analysis (shrink, markdown, margin pressure)
- ✅ Inventory buildup warnings (inventory growth vs sales growth)
- ✅ Automated XBRL extraction using GAAP taxonomy mappings

### ✅ Phase 3: JSON Restructuring & Visualization (Complete)
- ✅ Dual export approach (detailed + time-series formats)
- ✅ Temporal keys (fiscal_year, fiscal_quarter) in all filings
- ✅ Cash flow statement analysis (operating, investing, financing)
- ✅ Operating cash flow margin calculation
- ✅ Time-series friendly flat array structure
- ✅ 6 interactive Plotly charts (HTML format)
- ✅ Backward compatibility maintained
- ✅ 100% requirement coverage (43/43 requirements met)

### ✅ Phase 4: Professional Reports (Complete)
- ✅ Margin bridge analysis (waterfall chart FY2022 → Q3 2025)
- ✅ Investment thesis generation (auto-generated Buy/Hold/Sell recommendation)
- ✅ Executive insights extraction (inflection points, top trends, warnings)
- ✅ Risk heatmap visualizations (2 interactive charts)
- ✅ Enhanced PowerPoint with Phase 4 slides
- ✅ 9 total Plotly charts (6 from Phase 3 + 3 from Phase 4)

### Future Considerations
- Balance sheet ratio calculations (Current Ratio, Quick Ratio)
- Segment-level analysis (if disclosed)
- Real-time dashboard (Plotly Dash)
- Excel export with embedded charts
- API endpoints for data access

## Technical Notes

### XBRL Parsing Strategy

SEC filings use **Inline XBRL** (iXBRL) format where:
- Financial data is embedded in HTML with special tags
- Tags like `<ix:nonNumeric>` and `<ix:nonFraction>` contain values
- BeautifulSoup parses HTML structure
- Regex extracts numeric values from text

**Current Implementation:**
- Uses `sec-edgar-downloader` for automated filing retrieval
- BeautifulSoup parses iXBRL HTML structure
- Regex extracts numeric values and contextual text
- GAAP taxonomy mappings for metric extraction

### Why This Approach?

**Pros:**
- Automated filing downloads (no manual work)
- Simple, maintainable codebase
- Works with standard SEC EDGAR structure
- Easy to debug and customize
- Fast execution
- Environment-based configuration

**Cons:**
- Fragile to HTML structure changes
- Requires manual pattern updates for new metrics
- May miss some edge cases
- Dependent on SEC EDGAR API availability

**Trade-offs:** This approach prioritizes simplicity and automation over robustness. For production use requiring high reliability, consider dedicated XBRL parsing libraries like `python-xbrl`.

## Example Output

```json
{
  "period": "Q3 2025",
  "filing_type": "10-Q",
  "vital_signs": {
    "net_sales_billion": 25.27,
    "cost_of_sales_billion": 18.137,
    "operating_income_billion": 0.948,
    "inventory_billion": 14.896,
    "gross_margin_percent": 28.23,
    "operating_margin_percent": 3.75,
    "vs_baseline": {
      "operating_margin_change": -1.47,
      "operating_margin_trend": "declining",
      "gross_margin_change": 0.02
    },
    "vs_year_ago": {
      "operating_margin_yoy_change": -0.88,
      "operating_margin_yoy_trend": "declining",
      "comparison_period": "Q3 2024",
      "net_sales_yoy_growth_percent": 0.17,
      "inventory_yoy_growth_percent": -1.77
    }
  },
  "comparable_sales": {
    "total_change_percent": 2.7,
    "digital_change_percent": 2.4
  },
  "inventory_metrics": {
    "inventory_turnover_ratio": 1.22,
    "days_sales_of_inventory": 299.8
  },
  "debt_metrics": {},
  "risk_flags": [
    "Shrink/theft mentioned in MD&A",
    "Increased markdown/promotional activity noted"
  ]
}
```

**Plus top-level risk heatmap:**
```json
{
  "risk_heatmap": {
    "shrink": {
      "total_mentions": 22,
      "periods_affected": 8,
      "avg_mentions_per_period": 2.8,
      "trend": "increasing"
    },
    "markdown": {
      "total_mentions": 89,
      "periods_affected": 12,
      "avg_mentions_per_period": 7.4,
      "trend": "stable/decreasing"
    }
  }
}
```

The analyzer outputs structured JSON for all periods (FY2020-FY2024 annual, Q1 2022-Q3 2025 quarterly) showing:
- Operating margin decline of 88 basis points YoY in Q3 2025
- Inventory turnover of 1.22x (slower than typical 1.3-1.5x range)
- Days Sales of Inventory at 299.8 days (high, indicating slower inventory movement)
- Risk heatmap shows increasing shrink mentions trend (2.8 mentions/period average)

## License

This is a personal financial analysis tool. Use at your own discretion.

## Disclaimer

This tool is for educational and analytical purposes. Always verify extracted data against official SEC filings. Not financial advice.
