"""Multi-leg option strategy classes."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Literal

import numpy as np

from options_builder.data_manager import DataManager
from options_builder.payoffs import payoff


@dataclass
class StrategyLeg:
    """
    Single leg in an option strategy.

    Wraps option data with position quantity.
    Negative quantity = short, positive = long.
    """
    strike: float
    option_type: Literal['call', 'put']
    quantity: int  # Negative = short, positive = long

    # Market data
    bid: float
    ask: float
    mid: float

    # Greeks (per contract, not position-adjusted)
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float

    # Pricing
    model_price: float
    open_interest: int = 0
    volume: int = 0

    @classmethod
    def from_lookup(cls, option_data: dict, quantity: int) -> 'StrategyLeg':
        """
        Create a leg from DataManager lookup result.

        Args:
            option_data: Dict from dm.lookup_option()
            quantity: Number of contracts (negative = short)
        """
        return cls(
            strike=option_data['strike'],
            option_type=option_data['type'],
            quantity=quantity,
            bid=option_data['bid'],
            ask=option_data['ask'],
            mid=option_data['mid'],
            delta=option_data['delta'],
            gamma=option_data['gamma'],
            theta=option_data['theta'],
            vega=option_data['vega'],
            iv=option_data['iv'],
            model_price=option_data['model_price'],
            open_interest=option_data.get('open_interest', 0),
            volume=option_data.get('volume', 0),
        )

    @property
    def is_long(self) -> bool:
        """True if this is a long position."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """True if this is a short position."""
        return self.quantity < 0

    @property
    def is_call(self) -> bool:
        """True if this is a call option."""
        return self.option_type == 'call'

    @property
    def is_put(self) -> bool:
        """True if this is a put option."""
        return self.option_type == 'put'

    # Net Greeks (position-adjusted, per 100 shares per contract)
    @property
    def net_delta(self) -> float:
        """Position-adjusted delta (per 100 shares)."""
        return self.delta * self.quantity * 100

    @property
    def net_gamma(self) -> float:
        """Position-adjusted gamma (per 100 shares)."""
        return self.gamma * self.quantity * 100

    @property
    def net_theta(self) -> float:
        """Position-adjusted theta (per 100 shares)."""
        return self.theta * self.quantity * 100

    @property
    def net_vega(self) -> float:
        """Position-adjusted vega (per 100 shares)."""
        return self.vega * self.quantity * 100

    @property
    def cost(self) -> float:
        """
        Cost to enter this leg (positive = debit, negative = credit).

        Long positions cost money (buy at ask).
        Short positions receive credit (sell at bid).
        """
        if self.quantity > 0:
            # Long: pay ask price
            return self.ask * self.quantity * 100
        else:
            # Short: receive bid price (quantity is negative)
            return self.bid * self.quantity * 100

    @property
    def mid_cost(self) -> float:
        """Cost using mid price (for analysis)."""
        return self.mid * self.quantity * 100


@dataclass
class OptionStrategy:
    """
    Multi-leg option strategy container.

    Holds multiple StrategyLeg objects and provides
    aggregated Greeks and cost calculations.
    """
    ticker: str
    expiration: date
    underlying_price: float
    legs: list[StrategyLeg] = field(default_factory=list)

    # Optional metadata
    name: str = ""  # e.g., "Iron Condor", "Bull Call Spread"

    def add_leg(self, leg: StrategyLeg) -> None:
        """Add a leg to the strategy."""
        self.legs.append(leg)

    def add_leg_from_lookup(
        self,
        dm: DataManager,
        strike: float,
        option_type: str,
        quantity: int
    ) -> bool:
        """
        Add a leg by looking up option in DataManager.

        Returns:
            True if option found and added, False otherwise
        """
        opt = dm.lookup_option(self.ticker, self.expiration, strike, option_type)
        if opt is None:
            return False
        self.legs.append(StrategyLeg.from_lookup(opt, quantity))
        return True

    def __len__(self) -> int:
        """Number of legs in strategy."""
        return len(self.legs)

    # Aggregated Greeks
    @property
    def total_delta(self) -> float:
        """Sum of position-adjusted deltas."""
        return sum(leg.net_delta for leg in self.legs)

    @property
    def total_gamma(self) -> float:
        """Sum of position-adjusted gammas."""
        return sum(leg.net_gamma for leg in self.legs)

    @property
    def total_theta(self) -> float:
        """Sum of position-adjusted thetas."""
        return sum(leg.net_theta for leg in self.legs)

    @property
    def total_vega(self) -> float:
        """Sum of position-adjusted vegas."""
        return sum(leg.net_vega for leg in self.legs)

    # Cost calculations
    @property
    def net_premium(self) -> float:
        """
        Net cost to enter strategy.

        Positive = net debit (you pay)
        Negative = net credit (you receive)
        """
        return sum(leg.cost for leg in self.legs)

    @property
    def net_premium_mid(self) -> float:
        """Net cost using mid prices."""
        return sum(leg.mid_cost for leg in self.legs)

    @property
    def is_debit(self) -> bool:
        """True if strategy costs money to enter."""
        return self.net_premium > 0

    @property
    def is_credit(self) -> bool:
        """True if strategy receives premium."""
        return self.net_premium < 0

    # Leg access helpers
    @property
    def calls(self) -> list[StrategyLeg]:
        """All call legs."""
        return [leg for leg in self.legs if leg.is_call]

    @property
    def puts(self) -> list[StrategyLeg]:
        """All put legs."""
        return [leg for leg in self.legs if leg.is_put]

    @property
    def long_legs(self) -> list[StrategyLeg]:
        """All long legs."""
        return [leg for leg in self.legs if leg.is_long]

    @property
    def short_legs(self) -> list[StrategyLeg]:
        """All short legs."""
        return [leg for leg in self.legs if leg.is_short]

    @property
    def strikes(self) -> list[float]:
        """All unique strikes, sorted."""
        return sorted(set(leg.strike for leg in self.legs))

    def get_leg(self, strike: float, option_type: str) -> Optional[StrategyLeg]:
        """Get leg by strike and type."""
        for leg in self.legs:
            if leg.strike == strike and leg.option_type == option_type:
                return leg
        return None

    def summary(self) -> dict:
        """
        Strategy summary as dict.

        Returns:
            Dict with key metrics for display
        """
        return {
            'name': self.name or 'Custom Strategy',
            'ticker': self.ticker,
            'expiration': self.expiration,
            'underlying_price': self.underlying_price,
            'num_legs': len(self.legs),
            'net_premium': self.net_premium,
            'is_debit': self.is_debit,
            'total_delta': self.total_delta,
            'total_gamma': self.total_gamma,
            'total_theta': self.total_theta,
            'total_vega': self.total_vega,
        }

    def generate_price_range(
        self,
        pct_range: float = 0.2,
        num_points: int = 100
    ) -> np.ndarray:
        """
        Generate array of prices for P&L calculation.

        Args:
            pct_range: Percentage above/below current price (0.2 = 80% to 120%)
            num_points: Number of price points

        Returns:
            NumPy array of prices from (1-pct_range) to (1+pct_range) of underlying
        """
        low = self.underlying_price * (1 - pct_range)
        high = self.underlying_price * (1 + pct_range)
        return np.linspace(low, high, num_points)

    def calculate_pnl(self, prices: np.ndarray) -> np.ndarray:
        """
        Calculate total P&L at each price point.

        For each leg: P&L = (intrinsic_value × quantity × 100) - cost

        Args:
            prices: Array of terminal stock prices

        Returns:
            Array of P&L values (in dollars)
        """
        total_pnl = np.zeros_like(prices)
        for leg in self.legs:
            intrinsic = payoff(prices, leg.strike, leg.option_type)
            leg_pnl = intrinsic * leg.quantity * 100 - leg.cost
            total_pnl += leg_pnl
        return total_pnl

    def pnl_data(
        self,
        pct_range: float = 0.2,
        num_points: int = 100
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convenience method returning price range and P&L for plotting.

        Args:
            pct_range: Percentage above/below current price
            num_points: Number of price points

        Returns:
            Tuple of (prices, pnl) arrays for matplotlib
        """
        prices = self.generate_price_range(pct_range, num_points)
        pnl = self.calculate_pnl(prices)
        return prices, pnl
