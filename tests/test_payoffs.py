"""Tests for payoff functions."""

import pytest
import numpy as np
from options_builder.payoffs import call_payoff, put_payoff, payoff


class TestCallPayoff:
    """Tests for call_payoff function."""

    def test_itm_call(self):
        """Call is ITM when S_T > K."""
        assert call_payoff(110, 100) == 10

    def test_atm_call(self):
        """Call is ATM when S_T == K."""
        assert call_payoff(100, 100) == 0

    def test_otm_call(self):
        """Call is OTM when S_T < K."""
        assert call_payoff(90, 100) == 0

    def test_array_input(self):
        """Call payoff works with numpy arrays."""
        S_T = np.array([90, 100, 110, 120])
        K = 100
        expected = np.array([0, 0, 10, 20])
        np.testing.assert_array_equal(call_payoff(S_T, K), expected)


class TestPutPayoff:
    """Tests for put_payoff function."""

    def test_itm_put(self):
        """Put is ITM when S_T < K."""
        assert put_payoff(90, 100) == 10

    def test_atm_put(self):
        """Put is ATM when S_T == K."""
        assert put_payoff(100, 100) == 0

    def test_otm_put(self):
        """Put is OTM when S_T > K."""
        assert put_payoff(110, 100) == 0

    def test_array_input(self):
        """Put payoff works with numpy arrays."""
        S_T = np.array([80, 90, 100, 110])
        K = 100
        expected = np.array([20, 10, 0, 0])
        np.testing.assert_array_equal(put_payoff(S_T, K), expected)


class TestGenericPayoff:
    """Tests for generic payoff function."""

    def test_call_option_type(self):
        """Generic payoff with option_type='call'."""
        assert payoff(110, 100, 'call') == 10
        assert payoff(90, 100, 'call') == 0

    def test_put_option_type(self):
        """Generic payoff with option_type='put'."""
        assert payoff(90, 100, 'put') == 10
        assert payoff(110, 100, 'put') == 0

    def test_invalid_option_type(self):
        """Invalid option_type raises ValueError."""
        with pytest.raises(ValueError, match="option_type must be 'call' or 'put'"):
            payoff(100, 100, 'invalid')

    def test_default_is_call(self):
        """Default option_type is 'call'."""
        assert payoff(110, 100) == 10  # Call payoff


class TestPayoffProperties:
    """Tests for general payoff properties."""

    def test_call_put_parity_payoff(self):
        """Call payoff - Put payoff = S_T - K."""
        S_T = np.linspace(50, 150, 100)
        K = 100
        call_p = call_payoff(S_T, K)
        put_p = put_payoff(S_T, K)
        np.testing.assert_array_almost_equal(call_p - put_p, S_T - K)

    def test_non_negative_payoffs(self):
        """Payoffs are always non-negative."""
        S_T = np.linspace(0.1, 200, 100)
        K = 100
        assert np.all(call_payoff(S_T, K) >= 0)
        assert np.all(put_payoff(S_T, K) >= 0)
