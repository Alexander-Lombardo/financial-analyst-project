"""Options market data connector using yfinance."""

import math
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

import yfinance as yf


@dataclass
class OptionLeg:
    """Single option leg with key data points."""
    strike: float
    last: float
    bid: float
    ask: float
    open_interest: int
    volume: int = 0
    implied_volatility: float = 0.0


@dataclass
class OptionChainRow:
    """A single row in the option chain grid (one strike price)."""
    strike: float
    call: Optional[OptionLeg] = None
    put: Optional[OptionLeg] = None


@dataclass
class OptionChainGrid:
    """
    Option chain grid with calls and puts side-by-side by strike.

    Attributes:
        ticker: Underlying symbol
        expiration: Option expiration date
        underlying_price: Current price of underlying
        rows: List of OptionChainRow, sorted by strike
    """
    ticker: str
    expiration: date
    underlying_price: float
    rows: list[OptionChainRow] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)

    def strikes(self) -> list[float]:
        """Return all strike prices."""
        return [row.strike for row in self.rows]

    def calls(self) -> list[OptionLeg]:
        """Return all call legs (excluding None)."""
        return [row.call for row in self.rows if row.call is not None]

    def puts(self) -> list[OptionLeg]:
        """Return all put legs (excluding None)."""
        return [row.put for row in self.rows if row.put is not None]

    def get_strike(self, strike: float) -> Optional[OptionChainRow]:
        """Get row for a specific strike price."""
        for row in self.rows:
            if row.strike == strike:
                return row
        return None

    def atm_strike(self) -> float:
        """Return the at-the-money strike (closest to underlying price)."""
        if not self.rows:
            raise ValueError("No strikes available")
        return min(self.strikes(), key=lambda s: abs(s - self.underlying_price))

    def display(self, num_strikes: Optional[int] = None) -> str:
        """
        Return a formatted string table of the option chain.

        Args:
            num_strikes: Limit to N strikes around ATM (None for all)
        """
        if not self.rows:
            return "No option data available"

        rows_to_display = self.rows
        if num_strikes:
            atm = self.atm_strike()
            atm_idx = next(i for i, r in enumerate(self.rows) if r.strike == atm)
            start = max(0, atm_idx - num_strikes // 2)
            end = min(len(self.rows), start + num_strikes)
            rows_to_display = self.rows[start:end]

        # Header
        lines = [
            f"Option Chain: {self.ticker} | Exp: {self.expiration} | Underlying: ${self.underlying_price:.2f}",
            "-" * 90,
            f"{'CALLS':^40} | {'STRIKE':^8} | {'PUTS':^40}",
            f"{'OI':>8} {'Bid':>8} {'Ask':>8} {'Last':>8} | {'':^8} | {'Last':<8} {'Bid':<8} {'Ask':<8} {'OI':<8}",
            "-" * 90,
        ]

        for row in rows_to_display:
            c = row.call
            p = row.put
            atm_marker = " *" if abs(row.strike - self.underlying_price) == abs(self.atm_strike() - self.underlying_price) else "  "

            call_str = f"{c.open_interest:>8} {c.bid:>8.2f} {c.ask:>8.2f} {c.last:>8.2f}" if c else " " * 35
            put_str = f"{p.last:<8.2f} {p.bid:<8.2f} {p.ask:<8.2f} {p.open_interest:<8}" if p else " " * 35

            lines.append(f"{call_str} | {row.strike:>6.2f}{atm_marker} | {put_str}")

        lines.append("-" * 90)
        return "\n".join(lines)


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

    def get_chain_grid(
        self,
        ticker: str,
        expiration: str
    ) -> OptionChainGrid:
        """
        Fetch option chain as a grid with calls/puts side-by-side by strike.

        Parameters:
            ticker: Stock symbol
            expiration: Expiration date (YYYY-MM-DD)

        Returns:
            OptionChainGrid with rows indexed by strike price
        """
        stock = yf.Ticker(ticker)
        chain = stock.option_chain(expiration)
        exp_date = datetime.strptime(expiration, '%Y-%m-%d').date()

        # Get underlying price
        underlying = self.get_underlying(ticker)

        # Build lookup dicts by strike
        calls_by_strike = {}
        for _, row in chain.calls.iterrows():
            strike = float(row['strike'])
            calls_by_strike[strike] = OptionLeg(
                strike=strike,
                last=self._safe_float(row.get('lastPrice', 0)),
                bid=self._safe_float(row.get('bid', 0)),
                ask=self._safe_float(row.get('ask', 0)),
                open_interest=self._safe_int(row.get('openInterest', 0)),
                volume=self._safe_int(row.get('volume', 0)),
                implied_volatility=self._safe_float(row.get('impliedVolatility', 0))
            )

        puts_by_strike = {}
        for _, row in chain.puts.iterrows():
            strike = float(row['strike'])
            puts_by_strike[strike] = OptionLeg(
                strike=strike,
                last=self._safe_float(row.get('lastPrice', 0)),
                bid=self._safe_float(row.get('bid', 0)),
                ask=self._safe_float(row.get('ask', 0)),
                open_interest=self._safe_int(row.get('openInterest', 0)),
                volume=self._safe_int(row.get('volume', 0)),
                implied_volatility=self._safe_float(row.get('impliedVolatility', 0))
            )

        # Combine all strikes and sort
        all_strikes = sorted(set(calls_by_strike.keys()) | set(puts_by_strike.keys()))

        rows = [
            OptionChainRow(
                strike=strike,
                call=calls_by_strike.get(strike),
                put=puts_by_strike.get(strike)
            )
            for strike in all_strikes
        ]

        return OptionChainGrid(
            ticker=ticker.upper(),
            expiration=exp_date,
            underlying_price=underlying.price,
            rows=rows
        )

    def get_risk_free_rate(self) -> float:
        """Get current risk-free rate (13-week T-bill)."""
        try:
            tbill = yf.Ticker("^IRX")
            rate = tbill.info.get('regularMarketPrice', 5.0) / 100
            return rate
        except Exception:
            return 0.05  # Default fallback
