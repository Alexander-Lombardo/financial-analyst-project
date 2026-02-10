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
│   ├── monte_carlo.py        # Monte Carlo simulation (GBM paths, exotic options)
│   ├── option.py             # Option class wrapper for strategy building
│   ├── iv_solver.py          # Newton-Raphson implied volatility solver
│   ├── payoffs.py            # Payoff functions for P&L diagrams
│   ├── data_connector.py     # Market data connector (yfinance)
│   ├── chain_analyzer.py     # Bridge: live data → IV/Greeks calculation
│   ├── data_manager.py       # Pandas-based option chain storage
│   ├── strategy.py           # Multi-leg option strategy classes
│   └── templates.py          # Strategy template factory functions
├── tests/                    # Test suite
│   ├── test_pricing.py       # Pricing function tests
│   ├── test_greeks.py        # Greeks function tests
│   ├── test_monte_carlo.py   # Monte Carlo simulation tests
│   ├── test_option_class.py  # Option class tests
│   ├── test_iv_solver.py     # IV solver tests
│   ├── test_payoffs.py       # Payoff function tests
│   ├── test_data_connector.py # Data connector tests
│   ├── test_chain_analyzer.py # Chain analyzer tests
│   ├── test_data_manager.py  # Data manager tests
│   ├── test_strategy.py      # Strategy classes tests
│   └── test_templates.py     # Strategy template tests
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

# All Greeks at once (returns flat dict)
all_greeks = greeks(S=100, K=100, T=1, r=0.05, sigma=0.2)
# Returns: {'call_delta': 0.637, 'put_delta': -0.363, 'gamma': 0.019,
#           'call_theta': -6.41, 'put_theta': -1.58, 'vega': 37.52}
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

### Option Class

The `Option` class provides an OOP wrapper for clean strategy building with automatic pricing and Greeks calculation:

```python
from options_builder import Option
import numpy as np

# Create an option (automatically calculates price and Greeks)
call = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
print(f"Price: ${call.price:.2f}")      # $10.45
print(f"Delta: {call.delta:.4f}")        # 0.6368
print(f"Gamma: {call.gamma:.4f}")        # 0.0188
print(f"Theta: {call.theta:.2f}")        # -6.41
print(f"Vega: {call.vega:.2f}")          # 37.52

# Short positions (position=-1)
short_put = Option(S=100, K=95, T=0.5, r=0.05, sigma=0.2,
                   option_type='put', position=-1)

# Position-adjusted Greeks (for portfolio management)
print(f"Net Delta: {short_put.net_delta:.4f}")  # Positive (short put)
print(f"Net Theta: {short_put.net_theta:.4f}")  # Positive (benefits from decay)

# Payoff and P&L at expiration
S_T = np.linspace(80, 120, 50)
payoffs = call.payoff_at(S_T)  # Position-adjusted payoff
pnl = call.pnl_at(S_T)         # Payoff minus premium paid
```

| Attribute | Description |
|-----------|-------------|
| `price` | Theoretical option price |
| `delta`, `gamma`, `theta`, `vega` | Option Greeks |
| `net_delta`, `net_gamma`, `net_theta`, `net_vega` | Position-adjusted Greeks |
| `payoff_at(S_T)` | Payoff at expiration given terminal price(s) |
| `pnl_at(S_T)` | P&L at expiration (payoff minus premium) |

### Data Connector

The `OptionsDataConnector` class fetches live market data from Yahoo Finance for pricing validation and analysis:

```python
from options_builder.data_connector import OptionsDataConnector, UnderlyingQuote, OptionQuote

# Initialize connector
connector = OptionsDataConnector()

# Get current stock price
quote = connector.get_underlying('AAPL')
print(f"{quote.ticker}: ${quote.price:.2f}")  # AAPL: $185.50

# Get available expiration dates
expirations = connector.get_expirations('AAPL')
print(expirations[:3])  # ['2026-02-14', '2026-02-21', '2026-02-28']

# Fetch option chain for a specific expiration
chain = connector.get_option_chain('AAPL', '2026-03-20')
for opt in chain[:2]:
    print(f"{opt.option_type.upper()} {opt.strike}: bid=${opt.bid}, ask=${opt.ask}, IV={opt.implied_volatility:.1%}")

# Filter by option type
calls_only = connector.get_option_chain('AAPL', '2026-03-20', option_type='call')

# Get current risk-free rate (13-week T-bill)
rate = connector.get_risk_free_rate()
print(f"Risk-free rate: {rate:.2%}")  # Risk-free rate: 4.25%
```

**Option Chain Grid (for multi-leg strategies):**

```python
from options_builder import OptionsDataConnector, OptionChainGrid

connector = OptionsDataConnector()
expirations = connector.get_expirations('SPY')

# Fetch grid with calls/puts side-by-side by strike
grid = connector.get_chain_grid('SPY', expirations[0])

# Display formatted table (10 strikes around ATM)
print(grid.display(num_strikes=10))
# Output:
# Option Chain: SPY | Exp: 2026-02-14 | Underlying: $693.95
# ------------------------------------------------------------------------------------------
#                  CALLS                   |  STRIKE  |                   PUTS
#       OI      Bid      Ask     Last |          | Last     Bid      Ask      OI
# ------------------------------------------------------------------------------------------
#     6858     2.50     2.55     2.70 | 693.00   | 1.14     1.10     1.15     9258
#     7299     2.00     2.05     2.00 | 694.00 * | 1.45     1.40     1.50     8873
# ...

# Access key data points
for row in grid.rows:
    print(f"Strike: {row.strike}")
    if row.call:
        print(f"  Call - Bid: {row.call.bid}, Ask: {row.call.ask}, Last: {row.call.last}, OI: {row.call.open_interest}")
    if row.put:
        print(f"  Put  - Bid: {row.put.bid}, Ask: {row.put.ask}, Last: {row.put.last}, OI: {row.put.open_interest}")

# Helper methods
atm = grid.atm_strike()           # Closest strike to underlying
strikes = grid.strikes()          # All strike prices
row = grid.get_strike(695.0)      # Get specific strike row
all_calls = grid.calls()          # All call legs
all_puts = grid.puts()            # All put legs
```

**Data Cleaning & Normalization:**

```python
from options_builder import OptionsDataConnector

connector = OptionsDataConnector()
expirations = connector.get_expirations('SPY')
grid = connector.get_chain_grid('SPY', expirations[0])

# Mid-price calculation
row = grid.get_strike(grid.atm_strike())
print(f"Call mid-price: ${row.call.mid_price:.2f}")
print(f"Call spread: ${row.call.spread:.2f} ({row.call.spread_pct:.1%})")

# Check liquidity
if row.call.is_liquid(max_spread_pct=0.50):
    print("Call is liquid (bid > 0 and spread < 50% of mid)")

# Time to maturity for pricing models
ttm = grid.time_to_maturity()  # From today
print(f"Time to maturity: {ttm:.4f} years ({ttm * 365:.0f} days)")

# Filter illiquid options (removes zero-bid and wide-spread options)
filtered = grid.filter_liquid(max_spread_pct=0.50)
print(f"Before: {len(grid)} rows, After: {len(filtered)} rows")
```

**Dataclasses:**

| Class | Fields |
|-------|--------|
| `UnderlyingQuote` | `ticker`, `price`, `timestamp` |
| `OptionQuote` | `ticker`, `option_type`, `strike`, `expiration`, `bid`, `ask`, `last`, `volume`, `open_interest`, `implied_volatility` |
| `OptionLeg` | `strike`, `last`, `bid`, `ask`, `open_interest`, `volume`, `implied_volatility` + properties below |
| `OptionChainRow` | `strike`, `call` (OptionLeg), `put` (OptionLeg) |
| `OptionChainGrid` | `ticker`, `expiration`, `underlying_price`, `rows` (list of OptionChainRow) |

**Methods:**

| Method | Description |
|--------|-------------|
| `get_underlying(ticker)` | Fetch current price for underlying asset |
| `get_expirations(ticker)` | Get available option expiration dates |
| `get_option_chain(ticker, expiration, option_type=None)` | Fetch option chain as list of OptionQuote |
| `get_chain_grid(ticker, expiration)` | Fetch option chain as grid with calls/puts side-by-side |
| `get_risk_free_rate()` | Get current 13-week T-bill rate (defaults to 5% on error) |

**OptionLeg Properties (Data Cleaning):**

| Property/Method | Description |
|-----------------|-------------|
| `mid_price` | Mid-price (mark) as average of bid and ask |
| `spread` | Bid-ask spread (ask - bid) |
| `spread_pct` | Spread as percentage of mid-price (returns `inf` if mid ≤ 0) |
| `is_liquid(max_spread_pct=0.50)` | Returns `True` if bid > 0 and spread_pct ≤ threshold |

**OptionChainGrid Methods:**

| Method | Description |
|--------|-------------|
| `strikes()` | Return all strike prices |
| `calls()` / `puts()` | Return all call/put OptionLeg objects |
| `get_strike(price)` | Get OptionChainRow for a specific strike |
| `atm_strike()` | Return strike closest to underlying price |
| `time_to_maturity(from_date=None)` | Time to expiration in years (365 days/year) |
| `filter_liquid(max_spread_pct=0.50)` | Return new grid with only liquid options |
| `display(num_strikes=None)` | Return formatted table string |

### Chain Analyzer

The `ChainAnalyzer` bridges live market data with the pricing engine, calculating implied volatility and Greeks for every option in a chain:

```python
from options_builder import OptionsDataConnector, ChainAnalyzer

# Fetch live option chain
conn = OptionsDataConnector()
exps = conn.get_expirations('SPY')
grid = conn.get_chain_grid('SPY', exps[1])  # Use expiration with T > 0

# Filter to liquid options
liquid_grid = grid.filter_liquid(max_spread_pct=0.30)

# Analyze chain (calculates IV and Greeks for each option)
analyzer = ChainAnalyzer()  # Fetches risk-free rate automatically
priced = analyzer.analyze(liquid_grid)

print(f"Analyzed {len(priced)} strikes")
print(f"TTM: {priced.time_to_maturity:.4f} years")
print(f"Risk-free rate: {priced.risk_free_rate:.2%}")

# Access ATM options
atm = priced.get_strike(priced.atm_strike())
if atm.call:
    c = atm.call
    print(f"ATM Call (K={c.strike}):")
    print(f"  Mid: ${c.mid_price:.2f}, IV: {c.implied_volatility:.1%}")
    print(f"  Delta: {c.delta:.3f}, Gamma: {c.gamma:.4f}")
    print(f"  Theta: {c.theta:.4f}, Vega: {c.vega:.4f}")

# Iterate through all priced options
for row in priced.rows:
    if row.call:
        print(f"K={row.strike} Call: IV={row.call.implied_volatility:.1%}, Δ={row.call.delta:+.3f}")
    if row.put:
        print(f"K={row.strike} Put:  IV={row.put.implied_volatility:.1%}, Δ={row.put.delta:+.3f}")
```

**Override Risk-Free Rate:**

```python
# Use custom risk-free rate instead of fetching from T-bills
analyzer = ChainAnalyzer(risk_free_rate=0.05)
priced = analyzer.analyze(grid)
```

**Dataclasses:**

| Class | Fields |
|-------|--------|
| `PricedOption` | `strike`, `option_type`, `bid`, `ask`, `mid_price`, `open_interest`, `volume`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`, `model_price` |
| `PricedChainRow` | `strike`, `call` (PricedOption), `put` (PricedOption) |
| `PricedChain` | `ticker`, `expiration`, `underlying_price`, `time_to_maturity`, `risk_free_rate`, `rows` |

**PricedChain Methods:**

| Method | Description |
|--------|-------------|
| `strikes()` | Return all strike prices |
| `calls()` / `puts()` | Return all PricedOption objects |
| `get_strike(price)` | Get PricedChainRow for a specific strike |
| `atm_strike()` | Return strike closest to underlying price |

**Notes:**
- Options with zero or invalid mid_price are skipped
- Options where IV solver fails to converge are skipped
- Model price is the BSM price using the calculated IV (should match mid_price)

### Data Manager

The `DataManager` stores priced option chains in Pandas DataFrames for fast lookups during strategy building:

```python
from options_builder import (
    OptionsDataConnector,
    ChainAnalyzer,
    DataManager
)

# Fetch and analyze option chain
conn = OptionsDataConnector()
exps = conn.get_expirations('SPY')
grid = conn.get_chain_grid('SPY', exps[2])
liquid_grid = grid.filter_liquid(max_spread_pct=0.30)

analyzer = ChainAnalyzer()
priced = analyzer.analyze(liquid_grid)

# Store in DataManager
dm = DataManager()
dm.add_chain(priced)

# Quick lookups
print(dm.get_cache_keys())  # [('SPY', datetime.date(2026, 3, 20))]
print(dm.get_strikes('SPY', priced.expiration))  # [580.0, 585.0, ...]

# Look up a specific option
atm_call = dm.lookup_option('SPY', priced.expiration, priced.atm_strike(), 'call')
if atm_call:
    print(f"ATM Call: ${atm_call['mid']:.2f}, IV: {atm_call['iv']:.1%}, Δ: {atm_call['delta']:.3f}")

# Get calls or puts only
calls = dm.get_calls('SPY', priced.expiration)
puts = dm.get_puts('SPY', priced.expiration)

# Filter by delta (e.g., find 30-delta puts for selling)
otm_puts = dm.filter_by_delta('SPY', priced.expiration, -0.35, -0.25, 'put')

# Filter by liquidity
liquid = dm.filter_by_liquidity('SPY', priced.expiration, min_oi=100, max_spread_pct=0.10)

# Get full DataFrame for analysis
df = dm.get_chain('SPY', priced.expiration)
print(df[['strike', 'type', 'mid', 'iv', 'delta']].head())
```

**Cache Management:**

```python
# Check what's cached
print(len(dm))  # Number of cached chains
print(('SPY', priced.expiration) in dm)  # True

# Clear specific ticker
dm.clear_cache(ticker='SPY')

# Clear all
dm.clear_cache()
```

**DataFrame Schema:**

| Column | Type | Description |
|--------|------|-------------|
| `ticker` | str | Underlying symbol |
| `expiration` | date | Expiration date |
| `type` | str | 'call' or 'put' |
| `strike` | float | Strike price |
| `bid` | float | Bid price |
| `ask` | float | Ask price |
| `mid` | float | Mid price (mark) |
| `iv` | float | Implied volatility |
| `delta` | float | Delta Greek |
| `gamma` | float | Gamma Greek |
| `theta` | float | Theta Greek |
| `vega` | float | Vega Greek |
| `open_interest` | int | Open interest |
| `volume` | int | Volume |
| `model_price` | float | BSM model price |
| `underlying_price` | float | Current stock price |
| `time_to_maturity` | float | TTM in years |
| `risk_free_rate` | float | Risk-free rate used |

**Methods:**

| Method | Description |
|--------|-------------|
| `add_chain(chain)` | Store a PricedChain (overwrites if same ticker/expiration) |
| `get_chain(ticker, expiration)` | Get full DataFrame or None |
| `get_calls(ticker, expiration)` | Get calls only |
| `get_puts(ticker, expiration)` | Get puts only |
| `lookup_option(ticker, expiration, strike, option_type)` | Get single option as dict |
| `get_strikes(ticker, expiration)` | Get sorted list of strikes |
| `filter_by_delta(ticker, expiration, min_delta, max_delta, option_type=None)` | Filter by delta range |
| `filter_by_liquidity(ticker, expiration, min_oi=0, max_spread_pct=1.0)` | Filter by OI and spread |
| `get_cache_keys()` | Get all cached (ticker, expiration) pairs |
| `clear_cache(ticker=None)` | Clear all or ticker-specific data |

### Option Strategy Builder

The `StrategyLeg` and `OptionStrategy` classes enable building and analyzing multi-leg option strategies with aggregated Greeks and cost calculations:

```python
from datetime import date
from options_builder import (
    OptionsDataConnector,
    ChainAnalyzer,
    DataManager,
    OptionStrategy,
    StrategyLeg
)

# Set up data pipeline
conn = OptionsDataConnector()
exps = conn.get_expirations('SPY')
grid = conn.get_chain_grid('SPY', exps[2])
liquid_grid = grid.filter_liquid(max_spread_pct=0.30)

analyzer = ChainAnalyzer()
priced = analyzer.analyze(liquid_grid)

dm = DataManager()
dm.add_chain(priced)

# Build a Bull Call Spread
strategy = OptionStrategy(
    ticker='SPY',
    expiration=priced.expiration,
    underlying_price=priced.underlying_price,
    name='Bull Call Spread'
)

# Add legs: Long lower strike, Short higher strike
atm = priced.atm_strike()
strategy.add_leg_from_lookup(dm, atm, 'call', 1)       # Long ATM call
strategy.add_leg_from_lookup(dm, atm + 5, 'call', -1)  # Short OTM call

# View aggregated Greeks
print(f"Strategy: {strategy.name}")
print(f"Net Premium: ${strategy.net_premium:.2f}")
print(f"Is Debit: {strategy.is_debit}")
print(f"Total Delta: {strategy.total_delta:.1f}")
print(f"Total Gamma: {strategy.total_gamma:.2f}")
print(f"Total Theta: {strategy.total_theta:.2f}")
print(f"Total Vega: {strategy.total_vega:.2f}")
```

**Position Convention:**
- `quantity > 0` = Long (buy)
- `quantity < 0` = Short (sell)
- Example: `quantity=-2` means "short 2 contracts"

**Building Legs Manually:**

```python
# Create leg from DataManager lookup result
opt_data = dm.lookup_option('SPY', priced.expiration, 500.0, 'call')
leg = StrategyLeg.from_lookup(opt_data, quantity=1)

# Access leg properties
print(f"Strike: {leg.strike}, Type: {leg.option_type}")
print(f"Is Long: {leg.is_long}, Is Call: {leg.is_call}")
print(f"Delta: {leg.delta}, Net Delta: {leg.net_delta}")
print(f"Cost: ${leg.cost:.2f}")  # Positive=debit, Negative=credit
```

**Common Strategy Examples:**

```python
# Iron Condor (4-leg credit spread)
iron_condor = OptionStrategy(
    ticker='SPY',
    expiration=priced.expiration,
    underlying_price=priced.underlying_price,
    name='Iron Condor'
)
iron_condor.add_leg_from_lookup(dm, 480.0, 'put', 1)   # Long OTM put (protection)
iron_condor.add_leg_from_lookup(dm, 490.0, 'put', -1)  # Short put (collect premium)
iron_condor.add_leg_from_lookup(dm, 510.0, 'call', -1) # Short call (collect premium)
iron_condor.add_leg_from_lookup(dm, 520.0, 'call', 1)  # Long OTM call (protection)

print(f"Credit Received: ${-iron_condor.net_premium:.2f}")
print(f"Total Delta: {iron_condor.total_delta:.1f}")  # Near zero (neutral)

# Synthetic Long (Long Call + Short Put at same strike)
synthetic = OptionStrategy(
    ticker='SPY',
    expiration=priced.expiration,
    underlying_price=priced.underlying_price,
    name='Synthetic Long'
)
synthetic.add_leg_from_lookup(dm, 500.0, 'call', 1)
synthetic.add_leg_from_lookup(dm, 500.0, 'put', -1)

print(f"Total Delta: {synthetic.total_delta:.1f}")  # ~100 (like 100 shares)
```

**Helper Methods:**

```python
# Filter legs by type
calls = strategy.calls          # All call legs
puts = strategy.puts            # All put legs
long_legs = strategy.long_legs  # All long positions
short_legs = strategy.short_legs  # All short positions

# Get unique strikes
strikes = strategy.strikes  # Sorted list of strikes

# Find specific leg
leg = strategy.get_leg(500.0, 'call')  # By strike and type

# Strategy summary
summary = strategy.summary()
print(summary)
# {'name': 'Bull Call Spread', 'ticker': 'SPY', 'expiration': ...,
#  'num_legs': 2, 'net_premium': 290.0, 'is_debit': True,
#  'total_delta': 15.0, 'total_gamma': 1.0, ...}
```

**StrategyLeg Attributes:**

| Attribute | Description |
|-----------|-------------|
| `strike` | Strike price |
| `option_type` | 'call' or 'put' |
| `quantity` | Number of contracts (negative = short) |
| `bid`, `ask`, `mid` | Market prices |
| `delta`, `gamma`, `theta`, `vega` | Per-contract Greeks |
| `iv` | Implied volatility |
| `model_price` | BSM theoretical price |
| `open_interest`, `volume` | Liquidity metrics |

**StrategyLeg Properties:**

| Property | Description |
|----------|-------------|
| `is_long` / `is_short` | Position direction |
| `is_call` / `is_put` | Option type |
| `net_delta` | Position-adjusted delta (delta × quantity × 100) |
| `net_gamma` | Position-adjusted gamma |
| `net_theta` | Position-adjusted theta |
| `net_vega` | Position-adjusted vega |
| `cost` | Cost to enter (ask × qty × 100 for long, bid × qty × 100 for short) |
| `mid_cost` | Cost using mid price |

**OptionStrategy Attributes:**

| Attribute | Description |
|-----------|-------------|
| `ticker` | Underlying symbol |
| `expiration` | Expiration date |
| `underlying_price` | Current stock price |
| `legs` | List of StrategyLeg objects |
| `name` | Strategy name (optional) |

**OptionStrategy Properties:**

| Property | Description |
|----------|-------------|
| `total_delta` | Sum of all net deltas |
| `total_gamma` | Sum of all net gammas |
| `total_theta` | Sum of all net thetas |
| `total_vega` | Sum of all net vegas |
| `net_premium` | Total cost (positive = debit, negative = credit) |
| `net_premium_mid` | Total cost using mid prices |
| `is_debit` | True if strategy costs money |
| `is_credit` | True if strategy receives premium |
| `calls` / `puts` | Filter legs by type |
| `long_legs` / `short_legs` | Filter legs by direction |
| `strikes` | Sorted unique strikes |
| `max_profit` | Maximum profit in dollars, or None if unlimited |
| `max_loss` | Maximum loss in dollars (positive), or None if unlimited |
| `breakeven_points` | List of breakeven prices (sorted ascending) |
| `risk_reward_ratio` | Ratio of max profit to max loss, or None if either is unlimited |

**OptionStrategy Methods:**

| Method | Description |
|--------|-------------|
| `add_leg(leg)` | Add a StrategyLeg object |
| `add_leg_from_lookup(dm, strike, option_type, quantity)` | Add leg from DataManager lookup |
| `get_leg(strike, option_type)` | Find leg by strike and type |
| `summary()` | Return dict with key metrics |
| `generate_price_range(pct_range, num_points)` | Generate price array for P&L calculation |
| `calculate_pnl(prices)` | Calculate total P&L at each price point |
| `pnl_data(pct_range, num_points)` | Return (prices, pnl) tuple for plotting |

**P&L Calculation (Payoff Diagrams):**

Generate the "hockey stick" payoff diagram data for any multi-leg strategy:

```python
import matplotlib.pyplot as plt
from options_builder import OptionStrategy

# Build a bull call spread
strategy = OptionStrategy(
    ticker='SPY',
    expiration=priced.expiration,
    underlying_price=500.0,
    name='Bull Call Spread'
)
strategy.add_leg_from_lookup(dm, 500.0, 'call', 1)   # Long 500C
strategy.add_leg_from_lookup(dm, 505.0, 'call', -1)  # Short 505C

# Generate P&L data (prices from 80% to 120% of underlying)
prices, pnl = strategy.pnl_data(pct_range=0.2, num_points=100)

# Plot payoff diagram
plt.figure(figsize=(10, 6))
plt.plot(prices, pnl, 'b-', linewidth=2)
plt.axhline(y=0, color='gray', linestyle='--')
plt.axvline(x=strategy.underlying_price, color='gray', linestyle=':')
plt.fill_between(prices, pnl, 0, where=(pnl > 0), alpha=0.3, color='green')
plt.fill_between(prices, pnl, 0, where=(pnl < 0), alpha=0.3, color='red')
plt.xlabel('Stock Price at Expiration')
plt.ylabel('P&L ($)')
plt.title(f'{strategy.name} Payoff Diagram')
plt.grid(True, alpha=0.3)
plt.show()
```

**P&L Formula:**

For each leg at terminal price S_T:
```
Leg P&L = payoff(S_T, K, type) × quantity × 100 - cost
```

Where:
- `payoff(S_T, K, type)` = intrinsic value at expiration (max(S_T - K, 0) for calls)
- `quantity` = number of contracts (negative for short positions)
- `cost` = premium paid/received to enter the position

**Example: Analyzing Bull Call Spread P&L:**

```python
import numpy as np

# Test specific price points
prices = np.array([490.0, 500.0, 502.5, 505.0, 510.0])
pnl = strategy.calculate_pnl(prices)

for price, pl in zip(prices, pnl):
    print(f"At ${price:.0f}: P&L = ${pl:.0f}")
# Output:
# At $490: P&L = $-290  (max loss - both expire worthless)
# At $500: P&L = $-290  (at lower strike)
# At $502: P&L = $-40   (partial profit)
# At $505: P&L = $210   (max profit reached)
# At $510: P&L = $210   (max profit capped)

# Key metrics (built-in properties)
print(f"Max Profit: ${strategy.max_profit:.0f}")
print(f"Max Loss: ${strategy.max_loss:.0f}")
print(f"Breakeven: ${strategy.breakeven_points[0]:.2f}")
print(f"Risk/Reward: {strategy.risk_reward_ratio:.2f}")
```

**Strategy Metrics:**

The built-in metric properties handle bounded and unbounded strategies:

```python
# Bounded strategy: Bull Call Spread (defined max profit/loss)
spread = OptionStrategy(ticker='SPY', expiration=exp, underlying_price=500.0)
spread.add_leg_from_lookup(dm, 500.0, 'call', 1)   # Long 500C
spread.add_leg_from_lookup(dm, 505.0, 'call', -1)  # Short 505C

print(f"Max Profit: ${spread.max_profit:.0f}")      # e.g., $210
print(f"Max Loss: ${spread.max_loss:.0f}")          # e.g., $290
print(f"Breakevens: {spread.breakeven_points}")     # e.g., [502.90]
print(f"Risk/Reward: {spread.risk_reward_ratio:.2f}") # e.g., 0.72

# Unbounded strategy: Long Call (unlimited profit potential)
long_call = OptionStrategy(ticker='SPY', expiration=exp, underlying_price=500.0)
long_call.add_leg_from_lookup(dm, 500.0, 'call', 1)

print(f"Max Profit: {long_call.max_profit}")        # None (unlimited)
print(f"Max Loss: ${long_call.max_loss:.0f}")       # Premium paid
print(f"Risk/Reward: {long_call.risk_reward_ratio}") # None

# Naked position: Short Call (unlimited loss potential)
short_call = OptionStrategy(ticker='SPY', expiration=exp, underlying_price=500.0)
short_call.add_leg_from_lookup(dm, 500.0, 'call', -1)

print(f"Max Profit: ${short_call.max_profit:.0f}")  # Premium received
print(f"Max Loss: {short_call.max_loss}")           # None (unlimited)
print(f"Risk/Reward: {short_call.risk_reward_ratio}") # None
```

### Strategy Templates (Quick-Builder)

Factory functions to create common multi-leg option strategies with a single call. Instead of manually adding each leg, use these "recipes" for standard strategies:

```python
from options_builder import (
    bull_call_spread,
    bear_call_spread,
    bull_put_spread,
    bear_put_spread,
    long_straddle,
    short_straddle,
    long_strangle,
    short_strangle,
    iron_condor,
    iron_butterfly,
)

# Bull Call Spread (debit spread, bullish)
strategy = bull_call_spread(dm, 'SPY', expiration, lower_strike=500.0, upper_strike=505.0)
print(f"Net Debit: ${strategy.net_premium:.0f}")  # e.g., $290
print(f"Max Profit: ${strategy.max_profit:.0f}")  # e.g., $210
print(f"Max Loss: ${strategy.max_loss:.0f}")      # e.g., $290

# Iron Condor (credit spread, neutral)
ic = iron_condor(
    dm, 'SPY', expiration,
    put_long_strike=490.0,
    put_short_strike=495.0,
    call_short_strike=505.0,
    call_long_strike=510.0
)
print(f"Credit Received: ${-ic.net_premium:.0f}")
print(f"Max Profit: ${ic.max_profit:.0f}")
print(f"Total Delta: {ic.total_delta:.1f}")  # Near zero (neutral)

# Multiple contracts
spread = bull_call_spread(dm, 'SPY', expiration, 500.0, 505.0, quantity=5)
```

**Available Templates:**

| Template | Legs | Type | Outlook |
|----------|------|------|---------|
| `bull_call_spread` | 2 | Debit | Moderately bullish |
| `bear_call_spread` | 2 | Credit | Moderately bearish/neutral |
| `bull_put_spread` | 2 | Credit | Moderately bullish/neutral |
| `bear_put_spread` | 2 | Debit | Moderately bearish |
| `long_straddle` | 2 | Debit | High volatility (either direction) |
| `short_straddle` | 2 | Credit | Low volatility |
| `long_strangle` | 2 | Debit | High volatility (either direction) |
| `short_strangle` | 2 | Credit | Low volatility |
| `iron_condor` | 4 | Credit | Neutral, low volatility |
| `iron_butterfly` | 4 | Credit | Neutral, very low volatility |

**Template Function Signatures:**

```python
# Vertical Spreads (2-leg)
bull_call_spread(dm, ticker, expiration, lower_strike, upper_strike, quantity=1)
bear_call_spread(dm, ticker, expiration, lower_strike, upper_strike, quantity=1)
bull_put_spread(dm, ticker, expiration, lower_strike, upper_strike, quantity=1)
bear_put_spread(dm, ticker, expiration, lower_strike, upper_strike, quantity=1)

# Neutral Strategies (2-leg)
long_straddle(dm, ticker, expiration, strike, quantity=1)
short_straddle(dm, ticker, expiration, strike, quantity=1)
long_strangle(dm, ticker, expiration, put_strike, call_strike, quantity=1)
short_strangle(dm, ticker, expiration, put_strike, call_strike, quantity=1)

# Advanced Spreads (4-leg)
iron_condor(dm, ticker, expiration, put_long, put_short, call_short, call_long, quantity=1)
iron_butterfly(dm, ticker, expiration, put_long, middle, call_long, quantity=1)
```

**Return Values:**
- Returns `OptionStrategy` object if all legs are found
- Returns `None` if any required option is missing from the DataManager
- Raises `ValueError` if strike prices are in invalid order

**Example: Complete Workflow with Templates:**

```python
from datetime import date
from options_builder import (
    OptionsDataConnector,
    ChainAnalyzer,
    DataManager,
    iron_condor,
)
import matplotlib.pyplot as plt

# 1. Fetch and analyze option chain
conn = OptionsDataConnector()
exps = conn.get_expirations('SPY')
grid = conn.get_chain_grid('SPY', exps[2])
liquid_grid = grid.filter_liquid(max_spread_pct=0.30)

analyzer = ChainAnalyzer()
priced = analyzer.analyze(liquid_grid)

dm = DataManager()
dm.add_chain(priced)

# 2. Build iron condor with template
atm = priced.atm_strike()
ic = iron_condor(
    dm, 'SPY', priced.expiration,
    put_long_strike=atm - 15,
    put_short_strike=atm - 10,
    call_short_strike=atm + 10,
    call_long_strike=atm + 15,
)

# 3. Analyze strategy
print(f"Strategy: {ic.name}")
print(f"Credit Received: ${-ic.net_premium:.0f}")
print(f"Max Profit: ${ic.max_profit:.0f}")
print(f"Max Loss: ${ic.max_loss:.0f}")
print(f"Breakevens: {ic.breakeven_points}")
print(f"Risk/Reward: {ic.risk_reward_ratio:.2f}")
print(f"Total Delta: {ic.total_delta:.1f}")
print(f"Total Theta: {ic.total_theta:.2f}")

# 4. Plot payoff diagram
prices, pnl = ic.pnl_data(pct_range=0.1)
plt.plot(prices, pnl)
plt.axhline(y=0, color='gray', linestyle='--')
plt.title('Iron Condor Payoff')
plt.xlabel('Stock Price')
plt.ylabel('P&L ($)')
plt.show()
```

### Implied Volatility Solver

Calculate implied volatility from market prices using Newton-Raphson iteration:

```python
from options_builder import implied_volatility, black_scholes

# Given a market price, solve for implied volatility
market_price = 10.45  # Observed call price
iv = implied_volatility(
    market_price=market_price,
    S=100, K=100, T=1, r=0.05,
    option_type='call',
    initial_guess=0.2  # Starting point (default: 20%)
)
print(f"Implied Volatility: {iv:.2%}")  # 20.00%

# Verify by repricing
call, put = black_scholes(S=100, K=100, T=1, r=0.05, sigma=iv)
print(f"Repriced: ${call:.2f}")  # $10.45
```

**Solver Parameters:**
- `MAX_ITERATIONS = 100` - Maximum Newton-Raphson iterations
- `TOLERANCE = 1e-6` - Convergence threshold
- `MIN_VOL = 0.0001` - Floor (0.01%)
- `MAX_VOL = 5.0` - Cap (500%)

### Payoff Functions

Calculate option payoffs at expiration for P&L diagrams and strategy analysis:

```python
from options_builder import call_payoff, put_payoff, payoff
import numpy as np

# Single values
print(call_payoff(S_T=110, K=100))  # 10 (ITM call)
print(put_payoff(S_T=90, K=100))    # 10 (ITM put)

# Arrays for P&L diagrams
S_T = np.linspace(80, 120, 100)
call_payoffs = call_payoff(S_T, K=100)
put_payoffs = put_payoff(S_T, K=100)

# Generic function with option_type parameter
payoffs = payoff(S_T, K=100, option_type='call')
```

**Put-Call Parity at Expiration:**
```python
# Call payoff - Put payoff = S_T - K (always holds)
assert np.allclose(call_payoff(S_T, K) - put_payoff(S_T, K), S_T - K)
```

### Input Validation & Boundary Handling

All pricing and Greeks functions validate inputs and handle edge cases:

```python
from options_builder import black_scholes, delta

# Input validation (raises ValueError)
black_scholes(S=-100, K=100, T=1, r=0.05, sigma=0.2)  # S must be positive
black_scholes(S=100, K=100, T=-1, r=0.05, sigma=0.2)  # T cannot be negative
black_scholes(S=100, K=100, T=1, r=0.05, sigma=-0.2)  # sigma must be positive

# T=0 boundary (at expiration) - returns intrinsic value
call, put = black_scholes(S=110, K=100, T=0, r=0.05, sigma=0.2)
print(f"Call at expiry: ${call:.2f}")  # $10.00 (intrinsic value)

# Greeks at T=0
call_delta, put_delta = delta(S=110, K=100, T=0, r=0.05, sigma=0.2)
print(f"Delta at expiry: {call_delta:.1f}")  # 1.0 (ITM call)
```

| Edge Case | Behavior |
|-----------|----------|
| `T = 0` | Returns intrinsic value (payoff at expiration) |
| `S ≤ 0` | Raises `ValueError` |
| `K ≤ 0` | Raises `ValueError` |
| `T < 0` | Raises `ValueError` |
| `sigma ≤ 0` | Raises `ValueError` |

### Market Validation

Validate the pricing engine against live market data using the validation script:

```bash
# From project root directory
cd target-financial-analyzer

# Validate SPY options (default)
python3 scripts/validate_with_market.py

# Multiple tickers
python3 scripts/validate_with_market.py --tickers AAPL MSFT SPY

# Specific option type with minimum days to expiration
python3 scripts/validate_with_market.py --tickers SPY --type call --min-dte 7
```

**Command Line Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--tickers` | `SPY` | Space-separated list of ticker symbols |
| `--type` | `both` | Option type: `call`, `put`, or `both` |
| `--min-dte` | `1` | Minimum days to expiration |

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

**How It Works:**
1. Fetches live option chain data from Yahoo Finance (yfinance)
2. Selects ATM (at-the-money) option for the nearest valid expiration
3. Extracts market-implied volatility from the option quote
4. Computes theoretical prices using Black-Scholes and Monte Carlo (100k paths)
5. Compares against market bid/ask spread

## Running Tests

The options pricing engine includes a comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_pricing.py -v      # Black-Scholes tests
pytest tests/test_greeks.py -v       # Greeks tests
pytest tests/test_monte_carlo.py -v  # Monte Carlo tests
pytest tests/test_option_class.py -v # Option class tests
pytest tests/test_iv_solver.py -v    # IV solver tests
pytest tests/test_payoffs.py -v      # Payoff tests
pytest tests/test_data_connector.py -v  # Data connector tests
pytest tests/test_chain_analyzer.py -v  # Chain analyzer tests
pytest tests/test_data_manager.py -v   # Data manager tests
pytest tests/test_strategy.py -v       # Strategy classes tests
pytest tests/test_templates.py -v      # Strategy template tests

# Run with coverage
pytest tests/ --cov=options_builder --cov-report=term-missing
```

**Test Coverage:**
- `test_pricing.py` - Black-Scholes formula validation, put-call parity, edge cases
- `test_greeks.py` - Delta, gamma, theta, vega calculations and bounds
- `test_monte_carlo.py` - GBM paths, European/Asian/barrier options, convergence
- `test_option_class.py` - Option class initialization, pricing, Greeks, payoffs, P&L
- `test_iv_solver.py` - IV convergence, input validation, edge cases
- `test_payoffs.py` - Call/put payoffs, array inputs, put-call parity
- `test_data_connector.py` - Market data fetching, option chains, risk-free rate
- `test_chain_analyzer.py` - Chain analysis, IV/Greeks calculation, PricedChain methods
- `test_data_manager.py` - DataFrame storage, lookups, filtering, cache management
- `test_strategy.py` - Strategy building, aggregated Greeks, cost calculations, P&L diagrams, helper methods
- `test_templates.py` - Strategy template factory functions, leg structure verification, directional bias validation, Greeks aggregation, quantity scaling

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Financial data sourced from SEC EDGAR
- Market data from Yahoo Finance
- Built with Plotly, python-pptx, and BeautifulSoup4
