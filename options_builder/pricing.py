import numpy as np
from scipy.stats import norm


def black_scholes(S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    """
    Calculate European option prices using Black-Scholes-Merton model.

    Parameters:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)

    Returns:
        tuple: (call_price, put_price)
    """
    # Calculate d1 and d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Calculate call and put prices
    call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return call, put
