# Target Financial Analyzer

Automated financial analysis tool that extracts metrics from Target Corporation's SEC 10-K and 10-Q filings and generates:
- 24 interactive Plotly charts
- Professional PowerPoint presentation

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/target-financial-analyzer.git
cd target-financial-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure SEC credentials
cp .env.example .env
# Edit .env with your name and email

# 4. Run the analysis
python run_analysis.py

# 5. View results
open output/Target_Financial_Analysis.pptx
```

## Features

- **10 years of annual data** - 10-K filings from FY2015 to FY2024
- **12 quarters of quarterly data** - 10-Q filings for recent quarters
- **XBRL parsing** - Accurate extraction directly from SEC XBRL tags
- **24 interactive charts** - Comprehensive financial visualizations
- **37-slide PowerPoint** - Professional presentation with pillar summaries

## 5 Pillars of Analysis

| Pillar | Focus | Charts |
|--------|-------|--------|
| 1. Growth & Revenue | Is the business growing? | 4 |
| 2. Profitability & Margins | How efficiently is profit generated? | 6 |
| 3. Liquidity & Solvency | Can the company pay its bills? | 5 |
| 4. Operational Efficiency | How well are assets utilized? | 4 |
| 5. Valuation & Risk | Is the stock fairly priced? | 5 |

## Output Files

| File | Description |
|------|-------------|
| `output/Target_Financial_Analysis.pptx` | 37-slide PowerPoint presentation |
| `output/chart_*.html` | 24 interactive Plotly charts |
| `output/target_timeseries.json` | Time-series data for charts |
| `output/target_analysis.json` | Detailed analysis data |

### Presentation Structure

- 3 introduction slides (Title, Executive Summary, Investment Thesis)
- 5 pillar section dividers
- 24 chart slides across 5 pillars
- 5 pillar summary slides with key findings

## Charts Generated

### Pillar 1: Growth & Revenue
1. Revenue & Net Income (10-Year Annual)
2. Revenue Growth YoY
3. Revenue vs Inventory Growth
4. Revenue & Net Income (Quarterly)

### Pillar 2: Profitability & Margins
5. Margin Analysis (Gross/Operating/Net)
6. Margin Bridge Waterfall
7. Operating Expense Breakdown
8. EBITDA Bridge
9. Operating Margin Waterfall
10. Earnings Quality

### Pillar 3: Liquidity & Solvency
11. Current Ratio Gauge
12. Capital Structure
13. Debt-to-EBITDA Trend
14. Debt Health (Interest Coverage)
15. Statement of Cash Flows

### Pillar 4: Operational Efficiency
16. DuPont Analysis
17. Inventory Efficiency
18. Cash Conversion Cycle
19. OCF vs CapEx

### Pillar 5: Valuation & Risk
20. Valuation vs Growth Scatter
21. Historical P/E Band
22. Cash Flow Sankey
23. Risk Trends
24. Risk Heatmap

## Requirements

- Python 3.8+
- SEC EDGAR API credentials (free registration)
- Internet connection for SEC filing downloads

### SEC Credentials

The SEC requires identification for API access. Create a `.env` file:

```
SEC_USER_NAME=Your Name
SEC_USER_EMAIL=your.email@example.com
```

This is used in the User-Agent header as required by SEC EDGAR.

## Project Structure

```
target-financial-analyzer/
├── run_analysis.py           # Main entry point
├── financial_analyzer.py     # Core XBRL parsing & analysis
├── sec_data_fetcher.py       # SEC EDGAR downloader
├── visualize_data.py         # Chart generation (24 Plotly charts)
├── create_presentation.py    # PowerPoint generation
├── market_data_fetcher.py    # Yahoo Finance integration
├── xbrl_parser.py            # XBRL tag extraction utilities
├── requirements.txt          # Python dependencies
├── .env.example              # SEC credentials template
└── data/
    └── Target 10Q/           # Downloaded SEC filings
```

## Key Metrics Extracted

| Category | Metrics |
|----------|---------|
| Revenue | Net Sales, Revenue Growth YoY |
| Profitability | Gross Margin, Operating Margin, Net Margin |
| Efficiency | Inventory Turnover, Days Sales of Inventory |
| Debt | Interest Coverage, Debt-to-Equity, Debt-to-EBITDA |
| Liquidity | Current Ratio, Quick Ratio |
| Cash Flow | Free Cash Flow, FCF Margin |
| Valuation | P/E Ratio, P/S Ratio |

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Financial data sourced from SEC EDGAR
- Market data from Yahoo Finance
- Built with Plotly, python-pptx, and BeautifulSoup4
