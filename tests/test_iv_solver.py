"""Tests for implied volatility solver."""

import pytest
import numpy as np
from options_builder.iv_solver import implied_volatility
from options_builder.pricing import black_scholes


class TestIVSolverConvergence:
    """Tests for IV solver convergence."""

    def test_recovers_known_volatility_call(self):
        """IV solver recovers known volatility for a call."""
        S, K, T, r = 100, 100, 1.0, 0.05
        true_sigma = 0.2

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-5

    def test_recovers_known_volatility_put(self):
        """IV solver recovers known volatility for a put."""
        S, K, T, r = 100, 100, 1.0, 0.05
        true_sigma = 0.3

        _, put_price = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(put_price, S, K, T, r, 'put')

        assert abs(recovered_iv - true_sigma) < 1e-5

    def test_itm_call(self):
        """IV solver works for ITM call."""
        S, K, T, r = 110, 100, 0.5, 0.05
        true_sigma = 0.25

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-5

    def test_otm_put(self):
        """IV solver works for OTM put."""
        S, K, T, r = 110, 100, 0.5, 0.05
        true_sigma = 0.25

        _, put_price = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(put_price, S, K, T, r, 'put')

        assert abs(recovered_iv - true_sigma) < 1e-5

    def test_high_volatility(self):
        """IV solver works for high volatility."""
        S, K, T, r = 100, 100, 1.0, 0.05
        true_sigma = 0.8

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-4

    def test_low_volatility(self):
        """IV solver works for low volatility."""
        S, K, T, r = 100, 100, 1.0, 0.05
        true_sigma = 0.05

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-4

    def test_short_maturity(self):
        """IV solver works for short maturity."""
        S, K, T, r = 100, 100, 0.01, 0.05  # ~4 days
        true_sigma = 0.2

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-3


class TestIVSolverInputValidation:
    """Tests for IV solver input validation."""

    def test_invalid_option_type(self):
        """Invalid option_type raises ValueError."""
        with pytest.raises(ValueError, match="option_type must be 'call' or 'put'"):
            implied_volatility(10, 100, 100, 1, 0.05, 'invalid')

    def test_negative_market_price(self):
        """Negative market price raises ValueError."""
        with pytest.raises(ValueError, match="market_price must be positive"):
            implied_volatility(-1, 100, 100, 1, 0.05)

    def test_zero_market_price(self):
        """Zero market price raises ValueError."""
        with pytest.raises(ValueError, match="market_price must be positive"):
            implied_volatility(0, 100, 100, 1, 0.05)

    def test_zero_time_to_maturity(self):
        """Zero time to maturity raises ValueError."""
        with pytest.raises(ValueError, match="T must be positive"):
            implied_volatility(10, 100, 100, 0, 0.05)


class TestIVSolverEdgeCases:
    """Tests for IV solver edge cases."""

    def test_different_initial_guess(self):
        """IV solver converges from different initial guesses."""
        S, K, T, r = 100, 100, 1.0, 0.05
        true_sigma = 0.25

        call_price, _ = black_scholes(S, K, T, r, true_sigma)

        # Test with different initial guesses
        for initial in [0.1, 0.5, 1.0]:
            recovered_iv = implied_volatility(
                call_price, S, K, T, r, 'call', initial_guess=initial
            )
            assert abs(recovered_iv - true_sigma) < 1e-4

    def test_deep_itm_call(self):
        """IV solver works for deep ITM call."""
        S, K, T, r = 150, 100, 0.5, 0.05
        true_sigma = 0.2

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-3

    def test_deep_otm_call(self):
        """IV solver works for deep OTM call."""
        S, K, T, r = 80, 100, 0.5, 0.05
        true_sigma = 0.3

        call_price, _ = black_scholes(S, K, T, r, true_sigma)
        recovered_iv = implied_volatility(call_price, S, K, T, r, 'call')

        assert abs(recovered_iv - true_sigma) < 1e-3
