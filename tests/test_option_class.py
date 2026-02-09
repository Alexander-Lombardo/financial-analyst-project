"""Tests for Option class wrapper."""

import pytest
import numpy as np
from options_builder.option import Option
from options_builder.pricing import black_scholes
from options_builder.greeks import delta, gamma, theta, vega


class TestOptionInitialization:
    """Tests for Option class initialization."""

    def test_call_option_creation(self):
        """Create a basic call option."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        assert opt.option_type == 'call'
        assert opt.position == 1

    def test_put_option_creation(self):
        """Create a basic put option."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put')
        assert opt.option_type == 'put'

    def test_short_position(self):
        """Create a short option."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, position=-1)
        assert opt.position == -1

    def test_invalid_position(self):
        """Invalid position raises ValueError."""
        with pytest.raises(ValueError, match="position must be 1"):
            Option(S=100, K=100, T=1, r=0.05, sigma=0.2, position=2)

    def test_invalid_option_type(self):
        """Invalid option_type raises ValueError."""
        with pytest.raises(ValueError, match="option_type must be"):
            Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='straddle')


class TestOptionPricing:
    """Tests for Option pricing accuracy."""

    def test_call_price_matches_bsm(self):
        """Call price matches Black-Scholes."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma, option_type='call')
        expected_call, _ = black_scholes(S, K, T, r, sigma)
        assert abs(opt.price - expected_call) < 1e-10

    def test_put_price_matches_bsm(self):
        """Put price matches Black-Scholes."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma, option_type='put')
        _, expected_put = black_scholes(S, K, T, r, sigma)
        assert abs(opt.price - expected_put) < 1e-10


class TestOptionGreeks:
    """Tests for Option Greeks accuracy."""

    def test_call_delta(self):
        """Call delta matches direct calculation."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma, option_type='call')
        expected_delta, _ = delta(S, K, T, r, sigma)
        assert abs(opt.delta - expected_delta) < 1e-10

    def test_put_delta(self):
        """Put delta matches direct calculation."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma, option_type='put')
        _, expected_delta = delta(S, K, T, r, sigma)
        assert abs(opt.delta - expected_delta) < 1e-10

    def test_gamma(self):
        """Gamma matches direct calculation."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma)
        expected_gamma = gamma(S, K, T, r, sigma)
        assert abs(opt.gamma - expected_gamma) < 1e-10

    def test_call_theta(self):
        """Call theta matches direct calculation."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma, option_type='call')
        expected_theta, _ = theta(S, K, T, r, sigma)
        assert abs(opt.theta - expected_theta) < 1e-10

    def test_vega(self):
        """Vega matches direct calculation."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        opt = Option(S=S, K=K, T=T, r=r, sigma=sigma)
        expected_vega = vega(S, K, T, r, sigma)
        assert abs(opt.vega - expected_vega) < 1e-10


class TestOptionPayoff:
    """Tests for Option payoff calculations."""

    def test_long_call_payoff_itm(self):
        """Long call payoff when ITM."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        assert opt.payoff_at(110) == 10

    def test_long_call_payoff_otm(self):
        """Long call payoff when OTM."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        assert opt.payoff_at(90) == 0

    def test_short_call_payoff_itm(self):
        """Short call payoff when ITM."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call', position=-1)
        assert opt.payoff_at(110) == -10

    def test_long_put_payoff_itm(self):
        """Long put payoff when ITM."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put')
        assert opt.payoff_at(90) == 10

    def test_short_put_payoff_itm(self):
        """Short put payoff when ITM."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put', position=-1)
        assert opt.payoff_at(90) == -10

    def test_payoff_array(self):
        """Payoff works with array input."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        S_T = np.array([90, 100, 110])
        expected = np.array([0, 0, 10])
        np.testing.assert_array_equal(opt.payoff_at(S_T), expected)


class TestOptionPnL:
    """Tests for Option P&L calculations."""

    def test_long_call_pnl(self):
        """Long call P&L calculation."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        premium = opt.price
        # At S_T=120, payoff is 20, P&L is 20 - premium
        expected_pnl = 20 - premium
        assert abs(opt.pnl_at(120) - expected_pnl) < 1e-10

    def test_short_call_pnl(self):
        """Short call P&L calculation (receives premium)."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call', position=-1)
        premium = opt.price
        # At S_T=120, payoff is -20, P&L is -20 + premium (received)
        expected_pnl = -20 + premium
        assert abs(opt.pnl_at(120) - expected_pnl) < 1e-10

    def test_breakeven_call(self):
        """Call breakeven at strike + premium."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        breakeven = 100 + opt.price
        assert abs(opt.pnl_at(breakeven)) < 1e-10


class TestNetGreeks:
    """Tests for position-adjusted Greeks."""

    def test_long_net_delta(self):
        """Long position net_delta equals delta."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        assert opt.net_delta == opt.delta

    def test_short_net_delta(self):
        """Short position net_delta is negative delta."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call', position=-1)
        assert opt.net_delta == -opt.delta

    def test_short_net_gamma(self):
        """Short position net_gamma is negative gamma."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, position=-1)
        assert opt.net_gamma == -opt.gamma

    def test_short_net_theta(self):
        """Short position net_theta is negative theta (positive for seller)."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, position=-1)
        # Theta is negative for long, so net_theta for short is positive
        assert opt.net_theta == -opt.theta
        assert opt.net_theta > 0  # Short benefits from time decay

    def test_short_net_vega(self):
        """Short position net_vega is negative vega."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, position=-1)
        assert opt.net_vega == -opt.vega


class TestOptionRepr:
    """Tests for Option string representation."""

    def test_long_call_repr(self):
        """Long call repr."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
        repr_str = repr(opt)
        assert "Long" in repr_str
        assert "Call" in repr_str
        assert "S=100" in repr_str

    def test_short_put_repr(self):
        """Short put repr."""
        opt = Option(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put', position=-1)
        repr_str = repr(opt)
        assert "Short" in repr_str
        assert "Put" in repr_str
