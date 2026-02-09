"""Option class wrapper for clean strategy building."""

from dataclasses import dataclass
from typing import Literal, Union
import numpy as np

from options_builder.pricing import black_scholes
from options_builder.greeks import delta, gamma, theta, vega
from options_builder.payoffs import payoff

ArrayLike = Union[float, np.ndarray]


@dataclass
class Option:
    """
    European option with automatic pricing and Greeks.

    Attributes:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate
        sigma: Volatility
        option_type: 'call' or 'put'
        position: 1 for long, -1 for short
    """
    S: float
    K: float
    T: float
    r: float
    sigma: float
    option_type: Literal['call', 'put'] = 'call'
    position: int = 1  # 1=long, -1=short

    def __post_init__(self):
        """Calculate price and Greeks on initialization."""
        if self.position not in (1, -1):
            raise ValueError("position must be 1 (long) or -1 (short)")
        if self.option_type not in ('call', 'put'):
            raise ValueError("option_type must be 'call' or 'put'")
        self._calculate()

    def _calculate(self):
        """Compute price and all Greeks."""
        call_price, put_price = black_scholes(self.S, self.K, self.T, self.r, self.sigma)
        self.price = call_price if self.option_type == 'call' else put_price

        call_delta, put_delta = delta(self.S, self.K, self.T, self.r, self.sigma)
        self.delta = call_delta if self.option_type == 'call' else put_delta

        self.gamma = gamma(self.S, self.K, self.T, self.r, self.sigma)

        call_theta, put_theta = theta(self.S, self.K, self.T, self.r, self.sigma)
        self.theta = call_theta if self.option_type == 'call' else put_theta

        self.vega = vega(self.S, self.K, self.T, self.r, self.sigma)

    def payoff_at(self, S_T: ArrayLike) -> ArrayLike:
        """
        Calculate payoff at expiration given terminal price.

        Parameters:
            S_T: Terminal stock price(s)

        Returns:
            Position-adjusted payoff value(s)
        """
        return self.position * payoff(S_T, self.K, self.option_type)

    def pnl_at(self, S_T: ArrayLike) -> ArrayLike:
        """
        Calculate P&L at expiration (payoff minus premium paid/received).

        Parameters:
            S_T: Terminal stock price(s)

        Returns:
            Position-adjusted P&L value(s)
        """
        return self.payoff_at(S_T) - self.position * self.price

    @property
    def net_delta(self) -> float:
        """Position-adjusted delta."""
        return self.position * self.delta

    @property
    def net_gamma(self) -> float:
        """Position-adjusted gamma."""
        return self.position * self.gamma

    @property
    def net_theta(self) -> float:
        """Position-adjusted theta."""
        return self.position * self.theta

    @property
    def net_vega(self) -> float:
        """Position-adjusted vega."""
        return self.position * self.vega

    def __repr__(self) -> str:
        pos_str = "Long" if self.position == 1 else "Short"
        return (
            f"Option({pos_str} {self.option_type.capitalize()}, "
            f"S={self.S}, K={self.K}, T={self.T}, σ={self.sigma}, price={self.price:.4f})"
        )
