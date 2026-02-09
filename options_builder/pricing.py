import numpy as np
from scipy.stats import norm


def _validate_inputs(S, K, T, r, sigma) -> None:
    """
    Validate BSM inputs.
    Supports both scalar and numpy array inputs.

    Raises:
        ValueError: If any input is invalid
    """
    S_arr = np.asarray(S)
    K_arr = np.asarray(K)
    T_arr = np.asarray(T)
    sigma_arr = np.asarray(sigma)

    if np.any(S_arr <= 0):
        raise ValueError("Spot price S must be positive")
    if np.any(K_arr <= 0):
        raise ValueError("Strike price K must be positive")
    if np.any(T_arr < 0):
        raise ValueError("Time to maturity T cannot be negative")
    if np.any(sigma_arr <= 0):
        raise ValueError("Volatility sigma must be positive")


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

    Raises:
        ValueError: If inputs are invalid
    """
    _validate_inputs(S, K, T, r, sigma)

    # Handle T=0 (at expiration) - scalar only
    if np.isscalar(T) and T == 0:
        call = max(S - K, 0)
        put = max(K - S, 0)
        return float(call), float(put)

    # Calculate d1 and d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Calculate call and put prices
    call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return call, put
