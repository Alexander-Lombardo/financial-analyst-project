"""
Monte Carlo simulation for option pricing.

Uses Geometric Brownian Motion (GBM) to simulate asset paths and price options
by averaging discounted payoffs. Provides validation against analytical
Black-Scholes model and enables path-dependent option pricing.
"""

import numpy as np
from typing import Optional

from options_builder.constants import (
    DEFAULT_NUM_PATHS,
    DEFAULT_NUM_STEPS,
    MC_SEED,
    MC_ANTITHETIC,
)
from options_builder.pricing import black_scholes


def _validate_mc_inputs(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int,
    num_steps: int,
) -> None:
    """Validate Monte Carlo simulation inputs."""
    if S <= 0:
        raise ValueError("Spot price S must be positive")
    if K <= 0:
        raise ValueError("Strike price K must be positive")
    if T <= 0:
        raise ValueError("Time to maturity T must be positive")
    if sigma <= 0:
        raise ValueError("Volatility sigma must be positive")
    if num_paths < 1:
        raise ValueError("Number of paths must be at least 1")
    if num_steps < 1:
        raise ValueError("Number of steps must be at least 1")


def _create_rng(seed: Optional[int] = None) -> np.random.Generator:
    """Create a numpy random generator with optional seed."""
    return np.random.default_rng(seed)


def generate_paths(
    S: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int = DEFAULT_NUM_PATHS,
    num_steps: int = DEFAULT_NUM_STEPS,
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> np.ndarray:
    """
    Generate asset price paths using Geometric Brownian Motion.

    Uses the exact solution to the GBM SDE (not Euler discretization):
        S(t+dt) = S(t) * exp((r - 0.5*σ²)*dt + σ*√dt*Z)
    where Z ~ N(0,1)

    Parameters:
        S: Initial spot price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)
        num_paths: Number of simulation paths
        num_steps: Number of time steps
        antithetic: Use antithetic variates for variance reduction
        seed: Random seed for reproducibility (None = non-deterministic)

    Returns:
        np.ndarray: Price paths of shape (num_paths, num_steps + 1)
                    Column 0 is the initial price S
    """
    _validate_mc_inputs(S, K=1.0, T=T, r=r, sigma=sigma,
                        num_paths=num_paths, num_steps=num_steps)

    rng = _create_rng(seed)
    dt = T / num_steps

    # Drift and diffusion terms
    drift = (r - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    if antithetic:
        # Generate half the paths and mirror them
        half_paths = (num_paths + 1) // 2
        Z = rng.standard_normal((half_paths, num_steps))
        Z = np.vstack([Z, -Z[:num_paths - half_paths]])
    else:
        Z = rng.standard_normal((num_paths, num_steps))

    # Compute log returns and cumulative sum
    log_returns = drift + diffusion * Z
    log_paths = np.cumsum(log_returns, axis=1)

    # Prepend zeros for initial price and convert to price space
    log_paths = np.hstack([np.zeros((num_paths, 1)), log_paths])
    paths = S * np.exp(log_paths)

    return paths


def mc_european(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int = DEFAULT_NUM_PATHS,
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> dict:
    """
    Price European call and put options using Monte Carlo simulation.

    Call = e^(-rT) * E[max(S(T) - K, 0)]
    Put  = e^(-rT) * E[max(K - S(T), 0)]

    Parameters:
        S: Current spot price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)
        num_paths: Number of simulation paths
        antithetic: Use antithetic variates for variance reduction
        seed: Random seed for reproducibility

    Returns:
        dict: {
            'call': call price,
            'put': put price,
            'call_std_error': standard error of call estimate,
            'put_std_error': standard error of put estimate,
            'num_paths': number of paths used
        }
    """
    _validate_mc_inputs(S, K, T, r, sigma, num_paths, num_steps=1)

    # For European options, we only need terminal prices (1 step)
    paths = generate_paths(S, T, r, sigma, num_paths, num_steps=1,
                          antithetic=antithetic, seed=seed)
    S_T = paths[:, -1]

    # Calculate payoffs
    call_payoffs = np.maximum(S_T - K, 0)
    put_payoffs = np.maximum(K - S_T, 0)

    # Discount factor
    discount = np.exp(-r * T)

    # Prices are discounted expected payoffs
    call_price = discount * np.mean(call_payoffs)
    put_price = discount * np.mean(put_payoffs)

    # Standard errors
    call_std_error = discount * np.std(call_payoffs, ddof=1) / np.sqrt(num_paths)
    put_std_error = discount * np.std(put_payoffs, ddof=1) / np.sqrt(num_paths)

    return {
        'call': call_price,
        'put': put_price,
        'call_std_error': call_std_error,
        'put_std_error': put_std_error,
        'num_paths': num_paths,
    }


def mc_european_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int = DEFAULT_NUM_PATHS,
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> float:
    """
    Price a European call option using Monte Carlo simulation.

    Convenience function that returns only the call price.
    """
    result = mc_european(S, K, T, r, sigma, num_paths, antithetic, seed)
    return result['call']


def mc_european_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int = DEFAULT_NUM_PATHS,
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> float:
    """
    Price a European put option using Monte Carlo simulation.

    Convenience function that returns only the put price.
    """
    result = mc_european(S, K, T, r, sigma, num_paths, antithetic, seed)
    return result['put']


def compare_mc_to_bsm(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths_list: list[int] = None,
    seed: Optional[int] = MC_SEED,
) -> dict:
    """
    Compare Monte Carlo prices to Black-Scholes analytical prices.

    Useful for validating MC implementation and studying convergence.

    Parameters:
        S: Current spot price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)
        num_paths_list: List of path counts to test (default: [1000, 10000, 100000])
        seed: Random seed for reproducibility

    Returns:
        dict: {
            'bsm_call': analytical call price,
            'bsm_put': analytical put price,
            'mc_results': list of dicts with MC results for each path count
        }
    """
    if num_paths_list is None:
        num_paths_list = [1000, 10000, 100000]

    # Get analytical prices
    bsm_call, bsm_put = black_scholes(S, K, T, r, sigma)

    mc_results = []
    for num_paths in num_paths_list:
        mc = mc_european(S, K, T, r, sigma, num_paths=num_paths, seed=seed)
        mc_results.append({
            'num_paths': num_paths,
            'mc_call': mc['call'],
            'mc_put': mc['put'],
            'call_error': mc['call'] - bsm_call,
            'put_error': mc['put'] - bsm_put,
            'call_std_error': mc['call_std_error'],
            'put_std_error': mc['put_std_error'],
        })

    return {
        'bsm_call': bsm_call,
        'bsm_put': bsm_put,
        'mc_results': mc_results,
    }


def mc_asian_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    num_paths: int = DEFAULT_NUM_PATHS,
    num_steps: int = DEFAULT_NUM_STEPS,
    average_type: str = 'arithmetic',
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> dict:
    """
    Price an Asian call option (average price option) using Monte Carlo.

    The payoff is based on the average price over the life of the option:
        Payoff = max(A - K, 0)
    where A is the arithmetic or geometric average of prices.

    Parameters:
        S: Current spot price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)
        num_paths: Number of simulation paths
        num_steps: Number of time steps for averaging
        average_type: 'arithmetic' or 'geometric'
        antithetic: Use antithetic variates for variance reduction
        seed: Random seed for reproducibility

    Returns:
        dict: {
            'price': option price,
            'std_error': standard error of estimate,
            'num_paths': number of paths used
        }
    """
    if average_type not in ('arithmetic', 'geometric'):
        raise ValueError("average_type must be 'arithmetic' or 'geometric'")

    _validate_mc_inputs(S, K, T, r, sigma, num_paths, num_steps)

    paths = generate_paths(S, T, r, sigma, num_paths, num_steps,
                          antithetic=antithetic, seed=seed)

    # Calculate average prices (excluding initial price for path-average)
    if average_type == 'arithmetic':
        averages = np.mean(paths[:, 1:], axis=1)
    else:  # geometric
        averages = np.exp(np.mean(np.log(paths[:, 1:]), axis=1))

    # Calculate payoffs
    payoffs = np.maximum(averages - K, 0)

    # Discount and compute statistics
    discount = np.exp(-r * T)
    price = discount * np.mean(payoffs)
    std_error = discount * np.std(payoffs, ddof=1) / np.sqrt(num_paths)

    return {
        'price': price,
        'std_error': std_error,
        'num_paths': num_paths,
    }


def mc_barrier_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    barrier: float,
    barrier_type: str = 'up-and-out',
    num_paths: int = DEFAULT_NUM_PATHS,
    num_steps: int = DEFAULT_NUM_STEPS,
    antithetic: bool = MC_ANTITHETIC,
    seed: Optional[int] = MC_SEED,
) -> dict:
    """
    Price a barrier call option using Monte Carlo simulation.

    Barrier types:
        - 'up-and-out': Option expires worthless if price goes above barrier
        - 'up-and-in': Option only activates if price goes above barrier
        - 'down-and-out': Option expires worthless if price goes below barrier
        - 'down-and-in': Option only activates if price goes below barrier

    Parameters:
        S: Current spot price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annualized)
        sigma: Volatility (annualized)
        barrier: Barrier level
        barrier_type: Type of barrier ('up-and-out', 'up-and-in',
                      'down-and-out', 'down-and-in')
        num_paths: Number of simulation paths
        num_steps: Number of time steps
        antithetic: Use antithetic variates for variance reduction
        seed: Random seed for reproducibility

    Returns:
        dict: {
            'price': option price,
            'std_error': standard error of estimate,
            'num_paths': number of paths used
        }
    """
    valid_types = ('up-and-out', 'up-and-in', 'down-and-out', 'down-and-in')
    if barrier_type not in valid_types:
        raise ValueError(f"barrier_type must be one of {valid_types}")

    _validate_mc_inputs(S, K, T, r, sigma, num_paths, num_steps)

    if barrier <= 0:
        raise ValueError("Barrier must be positive")

    paths = generate_paths(S, T, r, sigma, num_paths, num_steps,
                          antithetic=antithetic, seed=seed)

    S_T = paths[:, -1]
    vanilla_payoffs = np.maximum(S_T - K, 0)

    # Determine if barrier was hit
    if barrier_type.startswith('up'):
        barrier_hit = np.any(paths >= barrier, axis=1)
    else:  # down
        barrier_hit = np.any(paths <= barrier, axis=1)

    # Apply barrier logic
    if barrier_type.endswith('out'):
        # Knock-out: payoff is zero if barrier was hit
        payoffs = np.where(barrier_hit, 0, vanilla_payoffs)
    else:  # in
        # Knock-in: payoff only if barrier was hit
        payoffs = np.where(barrier_hit, vanilla_payoffs, 0)

    # Discount and compute statistics
    discount = np.exp(-r * T)
    price = discount * np.mean(payoffs)
    std_error = discount * np.std(payoffs, ddof=1) / np.sqrt(num_paths)

    return {
        'price': price,
        'std_error': std_error,
        'num_paths': num_paths,
    }
