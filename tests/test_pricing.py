import numpy as np
import pytest

from options_builder.pricing import black_scholes


class TestBlackScholes:
    """Tests for the Black-Scholes-Merton pricing function."""

    def test_atm_option_known_values(self):
        """Test at-the-money option with known reference values."""
        call, put = black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert call == pytest.approx(10.4506, rel=1e-3)
        assert put == pytest.approx(5.5735, rel=1e-3)

    def test_put_call_parity(self):
        """Verify put-call parity: C - P = S - K*e^(-rT)."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        call, put = black_scholes(S, K, T, r, sigma)
        parity_lhs = call - put
        parity_rhs = S - K * np.exp(-r * T)
        assert parity_lhs == pytest.approx(parity_rhs, rel=1e-10)

    @pytest.mark.parametrize("S,K,T,r,sigma", [
        (100, 100, 1, 0.05, 0.2),
        (50, 60, 0.5, 0.03, 0.25),
        (150, 100, 2, 0.08, 0.3),
        (100, 120, 0.25, 0.02, 0.15),
    ])
    def test_put_call_parity_various_params(self, S, K, T, r, sigma):
        """Put-call parity should hold for various parameter combinations."""
        call, put = black_scholes(S, K, T, r, sigma)
        parity_lhs = call - put
        parity_rhs = S - K * np.exp(-r * T)
        assert parity_lhs == pytest.approx(parity_rhs, rel=1e-10)

    def test_deep_itm_call(self):
        """Deep in-the-money call should be close to intrinsic value."""
        S, K, T, r = 150, 100, 0.1, 0.05
        call, _ = black_scholes(S, K, T, r, sigma=0.2)
        intrinsic = S - K * np.exp(-r * T)
        assert call >= intrinsic
        assert call == pytest.approx(intrinsic, rel=0.01)

    def test_deep_otm_call(self):
        """Deep out-of-the-money call should be close to zero."""
        call, _ = black_scholes(S=50, K=150, T=0.1, r=0.05, sigma=0.2)
        assert call == pytest.approx(0, abs=0.01)

    def test_deep_itm_put(self):
        """Deep in-the-money put should be close to intrinsic value."""
        S, K, T, r = 50, 100, 0.1, 0.05
        _, put = black_scholes(S, K, T, r, sigma=0.2)
        intrinsic = K * np.exp(-r * T) - S
        assert put >= intrinsic
        assert put == pytest.approx(intrinsic, rel=0.01)

    def test_deep_otm_put(self):
        """Deep out-of-the-money put should be close to zero."""
        _, put = black_scholes(S=150, K=50, T=0.1, r=0.05, sigma=0.2)
        assert put == pytest.approx(0, abs=0.01)

    def test_higher_volatility_increases_prices(self):
        """Higher volatility should increase both call and put prices."""
        call_low, put_low = black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.1)
        call_high, put_high = black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.3)
        assert call_high > call_low
        assert put_high > put_low

    def test_longer_maturity_increases_atm_prices(self):
        """Longer time to maturity should increase ATM option prices."""
        call_short, put_short = black_scholes(S=100, K=100, T=0.25, r=0.05, sigma=0.2)
        call_long, put_long = black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert call_long > call_short
        assert put_long > put_short

    def test_prices_are_non_negative(self):
        """Option prices should always be non-negative."""
        call, put = black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert call >= 0
        assert put >= 0
