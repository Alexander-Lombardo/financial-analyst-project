"""Payoff functions for options at expiration."""

import numpy as np
from typing import Union

ArrayLike = Union[float, np.ndarray]


def call_payoff(S_T: ArrayLike, K: float) -> ArrayLike:
    """
    Call option payoff at expiration: max(S_T - K, 0)

    Parameters:
        S_T: Terminal stock price(s)
        K: Strike price

    Returns:
        Payoff value(s)
    """
    return np.maximum(S_T - K, 0)


def put_payoff(S_T: ArrayLike, K: float) -> ArrayLike:
    """
    Put option payoff at expiration: max(K - S_T, 0)

    Parameters:
        S_T: Terminal stock price(s)
        K: Strike price

    Returns:
        Payoff value(s)
    """
    return np.maximum(K - S_T, 0)


def payoff(S_T: ArrayLike, K: float, option_type: str = 'call') -> ArrayLike:
    """
    Generic payoff function for European options at expiration.

    Parameters:
        S_T: Terminal stock price(s)
        K: Strike price
        option_type: 'call' or 'put'

    Returns:
        Payoff value(s)

    Raises:
        ValueError: If option_type is not 'call' or 'put'
    """
    if option_type == 'call':
        return call_payoff(S_T, K)
    elif option_type == 'put':
        return put_payoff(S_T, K)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
