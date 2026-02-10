"""Chain analyzer: bridges live market data with pricing components."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from options_builder.data_connector import (
    OptionsDataConnector,
    OptionLeg,
    OptionChainGrid,
)
from options_builder.pricing import black_scholes
from options_builder.greeks import greeks
from options_builder.iv_solver import implied_volatility


@dataclass
class PricedOption:
    """Option with calculated IV and Greeks."""
    strike: float
    option_type: str  # 'call' or 'put'

    # Market data (from OptionLeg)
    bid: float
    ask: float
    mid_price: float
    open_interest: int
    volume: int

    # Calculated values
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float

    # Model price (BSM price using calculated IV)
    model_price: float


@dataclass
class PricedChainRow:
    """Row with priced call and put options."""
    strike: float
    call: Optional[PricedOption] = None
    put: Optional[PricedOption] = None


@dataclass
class PricedChain:
    """Full option chain with calculated IV and Greeks."""
    ticker: str
    expiration: date
    underlying_price: float
    time_to_maturity: float
    risk_free_rate: float
    rows: list[PricedChainRow] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)

    def strikes(self) -> list[float]:
        """Return all strike prices."""
        return [row.strike for row in self.rows]

    def calls(self) -> list[PricedOption]:
        """Return all priced call options."""
        return [row.call for row in self.rows if row.call]

    def puts(self) -> list[PricedOption]:
        """Return all priced put options."""
        return [row.put for row in self.rows if row.put]

    def get_strike(self, strike: float) -> Optional[PricedChainRow]:
        """Get row for a specific strike price."""
        for row in self.rows:
            if row.strike == strike:
                return row
        return None

    def atm_strike(self) -> float:
        """Return the at-the-money strike (closest to underlying price)."""
        return min(self.strikes(), key=lambda s: abs(s - self.underlying_price))


class ChainAnalyzer:
    """Analyzes option chains by calculating IV and Greeks for each leg."""

    def __init__(self, risk_free_rate: Optional[float] = None):
        """
        Initialize analyzer.

        Args:
            risk_free_rate: Override rate (fetches from T-bill if None)
        """
        self._risk_free_rate = risk_free_rate
        self._connector = OptionsDataConnector()

    def analyze(self, grid: OptionChainGrid) -> PricedChain:
        """
        Analyze an option chain grid, calculating IV and Greeks.

        Args:
            grid: OptionChainGrid from data connector

        Returns:
            PricedChain with calculated values for each option
        """
        r = self._risk_free_rate if self._risk_free_rate is not None else self._connector.get_risk_free_rate()
        T = grid.time_to_maturity()
        S = grid.underlying_price

        priced_rows = []
        for row in grid.rows:
            call = self._price_leg(row.call, 'call', S, T, r) if row.call else None
            put = self._price_leg(row.put, 'put', S, T, r) if row.put else None

            if call or put:
                priced_rows.append(PricedChainRow(
                    strike=row.strike,
                    call=call,
                    put=put
                ))

        return PricedChain(
            ticker=grid.ticker,
            expiration=grid.expiration,
            underlying_price=S,
            time_to_maturity=T,
            risk_free_rate=r,
            rows=priced_rows
        )

    def _price_leg(
        self,
        leg: OptionLeg,
        option_type: str,
        S: float,
        T: float,
        r: float
    ) -> Optional[PricedOption]:
        """Calculate IV and Greeks for a single leg."""
        market_price = leg.mid_price
        K = leg.strike

        # Skip if no valid market price
        if market_price <= 0:
            return None

        # Calculate implied volatility
        try:
            iv = implied_volatility(
                market_price=market_price,
                S=S, K=K, T=T, r=r,
                option_type=option_type
            )
        except ValueError:
            # IV solver failed to converge
            return None

        # Calculate Greeks
        all_greeks = greeks(S=S, K=K, T=T, r=r, sigma=iv)

        # Get model price
        call_price, put_price = black_scholes(S=S, K=K, T=T, r=r, sigma=iv)
        model_price = call_price if option_type == 'call' else put_price

        return PricedOption(
            strike=K,
            option_type=option_type,
            bid=leg.bid,
            ask=leg.ask,
            mid_price=market_price,
            open_interest=leg.open_interest,
            volume=leg.volume,
            implied_volatility=iv,
            delta=all_greeks['call_delta'] if option_type == 'call' else all_greeks['put_delta'],
            gamma=all_greeks['gamma'],
            theta=all_greeks['call_theta'] if option_type == 'call' else all_greeks['put_theta'],
            vega=all_greeks['vega'],
            model_price=model_price
        )
