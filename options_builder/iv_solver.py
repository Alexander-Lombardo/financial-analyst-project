"""Implied volatility solver using Newton-Raphson method."""

from options_builder.pricing import black_scholes
from options_builder.greeks import vega

MIN_VOL = 0.0001  # Floor to prevent division issues
MAX_VOL = 5.0     # Cap at 500% vol
MAX_ITERATIONS = 100
TOLERANCE = 1e-6


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = 'call',
    initial_guess: float = 0.2,
) -> float:
    """
    Calculate implied volatility using Newton-Raphson iteration.

    Parameters:
        market_price: Observed market price of the option
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        option_type: 'call' or 'put'
        initial_guess: Starting volatility estimate (default 20%)

    Returns:
        Implied volatility (annualized)

    Raises:
        ValueError: If option_type is invalid or convergence fails
    """
    if option_type not in ('call', 'put'):
        raise ValueError("option_type must be 'call' or 'put'")

    if market_price <= 0:
        raise ValueError("market_price must be positive")

    if T <= 0:
        raise ValueError("T must be positive for IV calculation")

    sigma = initial_guess

    for i in range(MAX_ITERATIONS):
        # Get theoretical price
        call, put = black_scholes(S, K, T, r, sigma)
        price = call if option_type == 'call' else put

        # Calculate error
        diff = price - market_price

        if abs(diff) < TOLERANCE:
            return sigma

        # Get vega for Newton-Raphson step
        v = vega(S, K, T, r, sigma)

        if v < 1e-10:  # Vega too small, can't continue
            break

        # Newton-Raphson update
        sigma = sigma - diff / v

        # Enforce bounds
        sigma = max(MIN_VOL, min(MAX_VOL, sigma))

    raise ValueError(f"IV solver did not converge after {MAX_ITERATIONS} iterations")
