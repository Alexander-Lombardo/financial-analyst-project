# Global constants for option pricing

# Risk-free rate (annualized, e.g., 0.05 = 5%)
RISK_FREE_RATE = 0.05

# Default time to maturity in years (e.g., 30 days = 30/365)
DEFAULT_TIME_TO_MATURITY = 30 / 365

# Trading days per year (for annualization)
TRADING_DAYS_PER_YEAR = 252

# Calendar days per year
CALENDAR_DAYS_PER_YEAR = 365

# Monte Carlo defaults
DEFAULT_NUM_PATHS = 10_000        # Number of simulation paths
DEFAULT_NUM_STEPS = 252           # Time steps (daily for 1 year)
MC_SEED = None                    # Random seed (None = non-deterministic)
MC_ANTITHETIC = True              # Use antithetic variates by default
