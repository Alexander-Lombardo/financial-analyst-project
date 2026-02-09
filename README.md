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
├── options_builder/          # Options pricing engine
│   ├── __init__.py
│   ├── constants.py          # Global pricing constants
│   ├── pricing.py            # Black-Scholes-Merton model
│   ├── greeks.py             # Option Greeks (delta, gamma, theta, vega)
│   └── monte_carlo.py        # Monte Carlo simulation (GBM paths, exotic options)
├── tests/                    # Test suite
│   ├── test_pricing.py       # Pricing function tests
│   ├── test_greeks.py        # Greeks function tests
│   └── test_monte_carlo.py   # Monte Carlo simulation tests
├── scripts/                  # Utility scripts
│   └── validate_with_market.py  # Market data validation
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

## Options Pricing Engine

The `options_builder` module provides European option pricing using the Black-Scholes-Merton model.

### Usage

```python
from options_builder import black_scholes

# Price a European option
call, put = black_scholes(
    S=100,      # Current stock price
    K=100,      # Strike price
    T=1,        # Time to maturity (years)
    r=0.05,     # Risk-free rate (annualized)
    sigma=0.2   # Volatility (annualized)
)

print(f"Call: ${call:.2f}, Put: ${put:.2f}")
# Output: Call: $10.45, Put: $5.57
```

### Formula

The Black-Scholes-Merton model calculates option prices as:

- **Call** = S·N(d₁) - K·e^(-rT)·N(d₂)
- **Put** = K·e^(-rT)·N(-d₂) - S·N(-d₁)

Where:
- d₁ = (ln(S/K) + (r + σ²/2)T) / (σ√T)
- d₂ = d₁ - σ√T
- N() = cumulative normal distribution

### Greeks

Calculate option sensitivities using analytical derivatives of Black-Scholes:

```python
from options_builder import delta, gamma, theta, vega, greeks
import numpy as np

# Single option
call_delta, put_delta = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
g = gamma(S=100, K=100, T=1, r=0.05, sigma=0.2)
call_theta, put_theta = theta(S=100, K=100, T=1, r=0.05, sigma=0.2)
v = vega(S=100, K=100, T=1, r=0.05, sigma=0.2)

# Vectorized for option chains
strikes = np.array([90, 95, 100, 105, 110])
call_deltas, put_deltas = delta(S=100, K=strikes, T=1, r=0.05, sigma=0.2)

# All Greeks at once
all_greeks = greeks(S=100, K=100, T=1, r=0.05, sigma=0.2)
```

| Greek | Description | Call | Put |
|-------|-------------|------|-----|
| **Delta (Δ)** | Price sensitivity to stock | N(d₁) | N(d₁) - 1 |
| **Gamma (Γ)** | Delta sensitivity to stock | N'(d₁) / (Sσ√T) | Same |
| **Theta (Θ)** | Price sensitivity to time | -SN'(d₁)σ/(2√T) - rKe^(-rT)N(d₂) | -SN'(d₁)σ/(2√T) + rKe^(-rT)N(-d₂) |
| **Vega (ν)** | Price sensitivity to volatility | SN'(d₁)√T | Same |

### Monte Carlo Simulation

Price options using Monte Carlo simulation with Geometric Brownian Motion (GBM). Supports European, Asian, and barrier options.

```python
from options_builder import (
    generate_paths,
    mc_european,
    mc_asian_call,
    mc_barrier_call,
    compare_mc_to_bsm,
)

# Generate GBM price paths
paths = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                       num_paths=10000, num_steps=252, seed=42)

# Price European options with standard error
result = mc_european(S=100, K=100, T=1, r=0.05, sigma=0.2,
                     num_paths=100000, seed=42)
print(f"Call: ${result['call']:.2f} ± ${result['call_std_error']:.4f}")
# Output: Call: $10.47 ± $0.0339

# Compare MC to analytical Black-Scholes
comparison = compare_mc_to_bsm(S=100, K=100, T=1, r=0.05, sigma=0.2,
                               num_paths_list=[1000, 10000, 100000], seed=42)
print(f"BSM Call: ${comparison['bsm_call']:.4f}")
for mc in comparison['mc_results']:
    print(f"{mc['num_paths']:>7,} paths: ${mc['mc_call']:.4f} (error: {mc['call_error']:+.4f})")

# Asian option (average price)
asian = mc_asian_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                      average_type='arithmetic', num_paths=50000, seed=42)
print(f"Asian Call: ${asian['price']:.2f}")

# Barrier option (knock-out)
barrier = mc_barrier_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                          barrier=120, barrier_type='up-and-out',
                          num_paths=50000, seed=42)
print(f"Up-and-Out Call: ${barrier['price']:.2f}")
```

| Function | Description |
|----------|-------------|
| `generate_paths()` | Simulate GBM asset paths with antithetic variates |
| `mc_european()` | European call/put with price and standard error |
| `mc_european_call()` | European call price only |
| `mc_european_put()` | European put price only |
| `compare_mc_to_bsm()` | Validate MC against analytical Black-Scholes |
| `mc_asian_call()` | Asian option (arithmetic or geometric average) |
| `mc_barrier_call()` | Barrier option (up/down, knock-in/out) |

**Key Features:**
- Exact GBM solution (not Euler discretization): S(t+dt) = S(t) × exp((r - σ²/2)dt + σ√dt × Z)
- Antithetic variates for variance reduction
- Convergence rate: O(1/√n)
- Reproducible results with optional seed

### Market Validation

Validate the pricing engine against live market data using the validation script:

```bash
# Validate SPY options (default)
PYTHONPATH=/Users/alex python3 scripts/validate_with_market.py

# Multiple tickers
PYTHONPATH=/Users/alex python3 scripts/validate_with_market.py --tickers AAPL MSFT SPY

# Specific option type with minimum days to expiration
PYTHONPATH=/Users/alex python3 scripts/validate_with_market.py --tickers SPY --type call --min-dte 7
```

**Sample Output:**
```
============================================================
Options Pricing Engine - Market Validation
============================================================

Ticker: SPY
Type: call
Underlying: $690.62
Strike: $691.00
Expiration: 2026-02-17 (T=0.025 years)
Risk-free rate: 3.59%
Implied Volatility: 14.8%

Market Prices:
  Bid: $6.16
  Ask: $6.20
  Mid: $6.18

Theoretical Prices:
  Black-Scholes: $6.50
  Monte Carlo:   $6.51 +/- $0.03

Result: PASS - BSM price within bid/ask spread
        MC price within 3 std errors of BSM (models agree)
============================================================
```

**Validation Criteria:**
- BSM price falls within market bid/ask spread (PASS/FAIL)
- MC price within 3 standard errors of BSM (confirms model consistency)
- Reports tolerance when outside spread but within 5% of mid

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Financial data sourced from SEC EDGAR
- Market data from Yahoo Finance
- Built with Plotly, python-pptx, and BeautifulSoup4
