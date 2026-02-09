"""Options market data connector using yfinance."""

import math
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

import yfinance as yf


@dataclass
class UnderlyingQuote:
    """Current quote for underlying asset."""
    ticker: str
    price: float
    timestamp: datetime


@dataclass
class OptionQuote:
    """Single option contract quote."""
    ticker: str
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: date
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float


class OptionsDataConnector:
    """
    Fetches stock prices and option chains from Yahoo Finance.

    Usage:
        connector = OptionsDataConnector()
        quote = connector.get_underlying('AAPL')
        expirations = connector.get_expirations('AAPL')
        chain = connector.get_option_chain('AAPL', '2026-03-20')
    """

    def __init__(self):
        self._cache = {}  # Simple in-memory cache

    def get_underlying(self, ticker: str) -> UnderlyingQuote:
        """Fetch current price for underlying asset."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
        except Exception as e:
            raise ValueError(f"Could not get price for {ticker}") from e

        price = (
            info.get('regularMarketPrice') or
            info.get('currentPrice') or
            info.get('previousClose')
        )

        if price is None:
            raise ValueError(f"Could not get price for {ticker}")

        return UnderlyingQuote(
            ticker=ticker.upper(),
            price=float(price),
            timestamp=datetime.now()
        )

    def get_expirations(self, ticker: str) -> list[str]:
        """Get available option expiration dates."""
        stock = yf.Ticker(ticker)
        expirations = stock.options

        if not expirations:
            raise ValueError(f"No options available for {ticker}")

        return list(expirations)

    def get_option_chain(
        self,
        ticker: str,
        expiration: str,
        option_type: Optional[str] = None
    ) -> list[OptionQuote]:
        """
        Fetch option chain for a specific expiration.

        Parameters:
            ticker: Stock symbol
            expiration: Expiration date (YYYY-MM-DD)
            option_type: 'call', 'put', or None for both

        Returns:
            List of OptionQuote objects
        """
        stock = yf.Ticker(ticker)
        chain = stock.option_chain(expiration)

        quotes = []
        exp_date = datetime.strptime(expiration, '%Y-%m-%d').date()

        if option_type in (None, 'call'):
            for _, row in chain.calls.iterrows():
                quotes.append(self._row_to_quote(
                    ticker, 'call', exp_date, row
                ))

        if option_type in (None, 'put'):
            for _, row in chain.puts.iterrows():
                quotes.append(self._row_to_quote(
                    ticker, 'put', exp_date, row
                ))

        return quotes

    def _row_to_quote(
        self,
        ticker: str,
        option_type: str,
        expiration: date,
        row
    ) -> OptionQuote:
        """Convert DataFrame row to OptionQuote."""
        return OptionQuote(
            ticker=ticker.upper(),
            option_type=option_type,
            strike=float(row['strike']),
            expiration=expiration,
            bid=self._safe_float(row.get('bid', 0)),
            ask=self._safe_float(row.get('ask', 0)),
            last=self._safe_float(row.get('lastPrice', 0)),
            volume=self._safe_int(row.get('volume', 0)),
            open_interest=self._safe_int(row.get('openInterest', 0)),
            implied_volatility=self._safe_float(row.get('impliedVolatility', 0))
        )

    def _safe_float(self, value) -> float:
        """Convert value to float, handling NaN and None."""
        if value is None:
            return 0.0
        try:
            result = float(value)
            return 0.0 if math.isnan(result) else result
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value) -> int:
        """Convert value to int, handling NaN and None."""
        if value is None:
            return 0
        try:
            fval = float(value)
            return 0 if math.isnan(fval) else int(fval)
        except (ValueError, TypeError):
            return 0

    def get_risk_free_rate(self) -> float:
        """Get current risk-free rate (13-week T-bill)."""
        try:
            tbill = yf.Ticker("^IRX")
            rate = tbill.info.get('regularMarketPrice', 5.0) / 100
            return rate
        except Exception:
            return 0.05  # Default fallback
