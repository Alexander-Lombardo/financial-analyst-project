import numpy as np
from scipy.stats import norm


def _validate_inputs(S, K, T, r, sigma) -> None:
    """
    Validate BSM inputs for Greeks calculation.
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


def _compute_d1_d2(S, K, T, r, sigma):
    """Shared helper to compute d1 and d2."""
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2


def delta(S, K, T, r, sigma):
    """
    Calculate Delta - sensitivity of option price to stock price.

    Returns: (call_delta, put_delta)
    - Call delta: N(d1), ranges from 0 to 1
    - Put delta: N(d1) - 1, ranges from -1 to 0
    """
    _validate_inputs(S, K, T, r, sigma)

    # At expiration: delta is 1 (ITM) or 0 (OTM) for calls, -1 or 0 for puts
    if np.isscalar(T) and T == 0:
        call_delta = 1.0 if S > K else (0.5 if S == K else 0.0)
        put_delta = -1.0 if S < K else (-0.5 if S == K else 0.0)
        return call_delta, put_delta

    d1, _ = _compute_d1_d2(S, K, T, r, sigma)
    call_delta = norm.cdf(d1)
    put_delta = call_delta - 1
    return call_delta, put_delta


def gamma(S, K, T, r, sigma):
    """
    Calculate Gamma - rate of change of delta (same for call and put).

    Returns: gamma value
    - Gamma = N'(d1) / (S * σ * √T)
    """
    _validate_inputs(S, K, T, r, sigma)

    # At expiration: gamma is 0 (delta is binary)
    if np.isscalar(T) and T == 0:
        return 0.0

    d1, _ = _compute_d1_d2(S, K, T, r, sigma)
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))


def theta(S, K, T, r, sigma):
    """
    Calculate Theta - sensitivity to time decay (per year).

    Returns: (call_theta, put_theta)
    - Negative values indicate price decreases as time passes
    """
    _validate_inputs(S, K, T, r, sigma)

    # At expiration: theta is 0 (no more time value to decay)
    if np.isscalar(T) and T == 0:
        return 0.0, 0.0

    d1, d2 = _compute_d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)

    common = -S * norm.pdf(d1) * sigma / (2 * sqrt_T)
    call_theta = common - r * K * np.exp(-r * T) * norm.cdf(d2)
    put_theta = common + r * K * np.exp(-r * T) * norm.cdf(-d2)

    return call_theta, put_theta


def vega(S, K, T, r, sigma):
    """
    Calculate Vega - sensitivity to volatility (same for call and put).

    Returns: vega value (per 1 unit change in sigma, not per 1%)
    - Vega = S * N'(d1) * √T
    """
    _validate_inputs(S, K, T, r, sigma)

    # At expiration: vega is 0 (volatility doesn't matter)
    if np.isscalar(T) and T == 0:
        return 0.0

    d1, _ = _compute_d1_d2(S, K, T, r, sigma)
    return S * norm.pdf(d1) * np.sqrt(T)


def greeks(S, K, T, r, sigma):
    """
    Calculate all Greeks at once (more efficient for full analysis).

    Returns: dict with all Greeks
        - 'call_delta', 'put_delta': Delta values
        - 'gamma': Gamma (same for call and put)
        - 'call_theta', 'put_theta': Theta values
        - 'vega': Vega (same for call and put)
    """
    _validate_inputs(S, K, T, r, sigma)

    # Handle T=0 edge case (scalar only)
    if np.isscalar(T) and T == 0:
        call_delta = 1.0 if S > K else (0.5 if S == K else 0.0)
        put_delta = -1.0 if S < K else (-0.5 if S == K else 0.0)
        return {
            'call_delta': call_delta,
            'put_delta': put_delta,
            'gamma': 0.0,
            'call_theta': 0.0,
            'put_theta': 0.0,
            'vega': 0.0
        }

    d1, d2 = _compute_d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    call_delta = norm.cdf(d1)
    put_delta = call_delta - 1

    g = pdf_d1 / (S * sigma * sqrt_T)

    v = S * pdf_d1 * sqrt_T

    common = -S * pdf_d1 * sigma / (2 * sqrt_T)
    call_theta = common - r * K * np.exp(-r * T) * norm.cdf(d2)
    put_theta = common + r * K * np.exp(-r * T) * norm.cdf(-d2)

    return {
        'call_delta': call_delta,
        'put_delta': put_delta,
        'gamma': g,
        'call_theta': call_theta,
        'put_theta': put_theta,
        'vega': v
    }
