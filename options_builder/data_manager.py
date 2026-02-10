"""Data Manager: Pandas-based storage for option chain data."""

import pandas as pd
from datetime import date
from typing import Optional

from options_builder.chain_analyzer import PricedChain, PricedOption


class DataManager:
    """
    Manages option chain data in Pandas DataFrames for fast lookups.

    Stores priced chains in memory, organized by (ticker, expiration).
    Provides filtering and lookup methods for strategy building.
    """

    # DataFrame column definitions
    COLUMNS = [
        'ticker', 'expiration', 'type', 'strike',
        'bid', 'ask', 'mid', 'iv',
        'delta', 'gamma', 'theta', 'vega',
        'open_interest', 'volume', 'model_price',
        'underlying_price', 'time_to_maturity', 'risk_free_rate'
    ]

    def __init__(self):
        """Initialize empty DataManager."""
        self._cache: dict[tuple[str, date], pd.DataFrame] = {}

    def add_chain(self, chain: PricedChain) -> None:
        """
        Add a priced chain to the manager.

        Flattens PricedChain into DataFrame rows (one row per option).
        Overwrites any existing data for the same (ticker, expiration).

        Args:
            chain: PricedChain from ChainAnalyzer
        """
        rows = []
        for priced_row in chain.rows:
            for opt in [priced_row.call, priced_row.put]:
                if opt is not None:
                    rows.append(self._option_to_row(opt, chain))

        df = pd.DataFrame(rows, columns=self.COLUMNS)
        key = (chain.ticker.upper(), chain.expiration)
        self._cache[key] = df

    def _option_to_row(self, opt: PricedOption, chain: PricedChain) -> list:
        """Convert PricedOption to DataFrame row."""
        return [
            chain.ticker.upper(),
            chain.expiration,
            opt.option_type,
            opt.strike,
            opt.bid,
            opt.ask,
            opt.mid_price,
            opt.implied_volatility,
            opt.delta,
            opt.gamma,
            opt.theta,
            opt.vega,
            opt.open_interest,
            opt.volume,
            opt.model_price,
            chain.underlying_price,
            chain.time_to_maturity,
            chain.risk_free_rate
        ]

    def get_chain(self, ticker: str, expiration: date) -> Optional[pd.DataFrame]:
        """
        Get full DataFrame for a ticker/expiration.

        Returns:
            DataFrame with all options, or None if not found
        """
        key = (ticker.upper(), expiration)
        return self._cache.get(key)

    def get_calls(self, ticker: str, expiration: date) -> Optional[pd.DataFrame]:
        """Get only call options."""
        df = self.get_chain(ticker, expiration)
        if df is None:
            return None
        return df[df['type'] == 'call'].copy()

    def get_puts(self, ticker: str, expiration: date) -> Optional[pd.DataFrame]:
        """Get only put options."""
        df = self.get_chain(ticker, expiration)
        if df is None:
            return None
        return df[df['type'] == 'put'].copy()

    def lookup_option(
        self,
        ticker: str,
        expiration: date,
        strike: float,
        option_type: str
    ) -> Optional[dict]:
        """
        Look up a specific option by strike and type.

        Args:
            ticker: Stock symbol
            expiration: Expiration date
            strike: Strike price
            option_type: 'call' or 'put'

        Returns:
            Dict with option data, or None if not found
        """
        df = self.get_chain(ticker, expiration)
        if df is None:
            return None

        mask = (df['strike'] == strike) & (df['type'] == option_type)
        matches = df[mask]

        if matches.empty:
            return None
        return matches.iloc[0].to_dict()

    def get_strikes(self, ticker: str, expiration: date) -> list[float]:
        """Get all unique strike prices, sorted."""
        df = self.get_chain(ticker, expiration)
        if df is None:
            return []
        return sorted(df['strike'].unique().tolist())

    def filter_by_delta(
        self,
        ticker: str,
        expiration: date,
        min_delta: float,
        max_delta: float,
        option_type: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Filter options by delta range.

        Args:
            ticker: Stock symbol
            expiration: Expiration date
            min_delta: Minimum delta (inclusive)
            max_delta: Maximum delta (inclusive)
            option_type: Optional filter for 'call' or 'put'

        Returns:
            Filtered DataFrame
        """
        df = self.get_chain(ticker, expiration)
        if df is None:
            return None

        mask = (df['delta'] >= min_delta) & (df['delta'] <= max_delta)
        if option_type:
            mask &= (df['type'] == option_type)

        return df[mask].copy()

    def filter_by_liquidity(
        self,
        ticker: str,
        expiration: date,
        min_oi: int = 0,
        max_spread_pct: float = 1.0
    ) -> Optional[pd.DataFrame]:
        """
        Filter options by liquidity criteria.

        Args:
            ticker: Stock symbol
            expiration: Expiration date
            min_oi: Minimum open interest
            max_spread_pct: Maximum spread as fraction of mid price

        Returns:
            Filtered DataFrame
        """
        df = self.get_chain(ticker, expiration)
        if df is None:
            return None

        spread_pct = (df['ask'] - df['bid']) / df['mid']
        mask = (df['open_interest'] >= min_oi) & (spread_pct <= max_spread_pct)

        return df[mask].copy()

    def get_cache_keys(self) -> list[tuple[str, date]]:
        """Get all cached (ticker, expiration) pairs."""
        return list(self._cache.keys())

    def clear_cache(self, ticker: Optional[str] = None) -> None:
        """
        Clear cached data.

        Args:
            ticker: If provided, only clear data for this ticker.
                   If None, clear all data.
        """
        if ticker is None:
            self._cache.clear()
        else:
            ticker = ticker.upper()
            keys_to_remove = [k for k in self._cache if k[0] == ticker]
            for key in keys_to_remove:
                del self._cache[key]

    def __len__(self) -> int:
        """Return number of cached chains."""
        return len(self._cache)

    def __contains__(self, key: tuple[str, date]) -> bool:
        """Check if (ticker, expiration) is cached."""
        return (key[0].upper(), key[1]) in self._cache
