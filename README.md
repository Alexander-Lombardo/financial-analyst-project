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

### Phase 2: Trend Analysis (10-Q Quarterly Analysis)
Compares each quarter against the baseline:
- **Operating Income Trend**: Growth vs. same quarter prior year
- **Markdown Watch**: Gross margin decline = potential inventory clearance
- **Theft/Shrink Monitor**: Scans MD&A for "shrink" mentions and basis point impact

### Phase 3: Data Structure (JSON Output)
Outputs structured JSON for each period, ready for graphing and visualization:

```json
{
  "period": "Q1 2025",
  "filing_type": "10-Q",
  "vital_signs": {
    "net_sales_billion": 24.5,
    "gross_margin_percent": 26.3,
    "operating_income_billion": 1.2,
    "operating_margin_percent": 4.9,
    "inventory_billion": 13.1,
    "vs_baseline": {
      "operating_margin_change": -0.3,
      "operating_margin_trend": "declining",
      "gross_margin_change": -0.5,
      "markdown_flag": "Potential inventory clearance/discounting"
    }
  },
  "comparable_sales": {
    "total_change_percent": 0.5,
    "store_change_percent": -1.2,
    "digital_change_percent": 8.4
  },
  "risk_flags": [
    "Shrink reduced gross margin by 50 basis points",
    "Increased markdown/promotional activity noted"
  ]
}
```

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
- `pandas` (optional) - Future data analysis
- `numpy` (optional) - Future calculations

## Usage

### Quick Start

```bash
# Run the analyzer (automatically downloads SEC filings)
python financial_analyzer.py
```

The script will automatically:
1. **Download** 5 years of 10-K reports and 12 quarters of 10-Q reports from SEC EDGAR
2. **Extract** financial metrics from each filing using XBRL parsing
3. **Analyze** trends and compare against baseline
4. **Export** results to `output/target_analysis.json` and `output/target_summary.txt`

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
│   ├── target_analysis.json            # Structured data
│   └── target_summary.txt              # Human-readable report
├── financial_analyzer.py               # Main analyzer
├── sec_data_fetcher.py                 # SEC EDGAR downloader
└── .env                                # Your credentials (git-ignored)
```

### Output Files

**1. `target_analysis.json`**
- Complete structured data for all periods
- Ready for import into visualization tools
- Machine-readable format
- Includes vital signs, comparable sales, and trend analysis

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

### 🚧 Phase 2: Enhanced Analytics (Planned)
- Year-over-year comparisons
- Inventory turnover ratio
- Interest coverage ratio
- Advanced trend detection

### 📋 Phase 3: JSON Restructuring (Planned)
- Time-series friendly data format
- Period-over-period deltas
- Normalized metric names
- API-ready structure

### 📊 Phase 4: Professional Reports (Planned)
- Margin bridge analysis
- Risk heatmaps
- Investment thesis generation
- Executive summary

### Future Considerations
- Cash flow statement analysis
- Balance sheet ratio calculations (Current Ratio, Quick Ratio)
- Segment-level analysis (if disclosed)
- Visualization dashboard (Plotly/Dash)
- Excel export with charts

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
    "operating_income_billion": 0.95,
    "gross_margin_percent": 28.23,
    "operating_margin_percent": 3.75,
    "inventory_billion": 14.9,
    "vs_baseline": {
      "operating_margin_change": -1.47,
      "operating_margin_trend": "declining",
      "gross_margin_change": 0.02
    }
  },
  "comparable_sales": {
    "total_change_percent": 0.3,
    "store_change_percent": -2.4,
    "digital_change_percent": 10.8
  },
  "debt_metrics": {
    "total_debt_billion": 15.49,
    "interest_expense_million": 123,
    "interest_coverage_ratio": 7.72,
    "vs_baseline": {
      "debt_change_percent": 7.51,
      "interest_coverage_change": -1.98
    }
  }
}
```

The analyzer outputs structured JSON for all periods (FY2024, Q1-Q3 2025) showing:
- Operating margin decline of 147 basis points in Q3 2025
- Inventory buildup of 16.9% above baseline
- Interest coverage deterioration from 9.7x to 1.5x (critical weakness)

## License

This is a personal financial analysis tool. Use at your own discretion.

## Disclaimer

This tool is for educational and analytical purposes. Always verify extracted data against official SEC filings. Not financial advice.
