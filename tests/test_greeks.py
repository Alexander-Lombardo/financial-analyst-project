import numpy as np
import pytest
from options_builder import delta, gamma, theta, vega, greeks


class TestDelta:
    def test_atm_call_delta_around_half(self):
        """ATM call delta should be slightly above 0.5 due to drift."""
        call_delta, _ = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert 0.5 < call_delta < 0.7

    def test_call_delta_bounds(self):
        """Call delta should be between 0 and 1."""
        call_delta, _ = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert 0 <= call_delta <= 1

    def test_put_delta_bounds(self):
        """Put delta should be between -1 and 0."""
        _, put_delta = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert -1 <= put_delta <= 0

    def test_put_call_delta_relationship(self):
        """Call delta - put delta should equal 1."""
        call_delta, put_delta = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert np.isclose(call_delta - put_delta, 1.0)

    def test_deep_itm_call_delta_near_one(self):
        """Deep ITM call should have delta near 1."""
        call_delta, _ = delta(S=150, K=100, T=1, r=0.05, sigma=0.2)
        assert call_delta > 0.95

    def test_deep_otm_call_delta_near_zero(self):
        """Deep OTM call should have delta near 0."""
        call_delta, _ = delta(S=50, K=100, T=1, r=0.05, sigma=0.2)
        assert call_delta < 0.05

    def test_known_value(self):
        """Test against known value for ATM option."""
        call_delta, put_delta = delta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert np.isclose(call_delta, 0.6368, atol=0.001)
        assert np.isclose(put_delta, -0.3632, atol=0.001)


class TestGamma:
    def test_gamma_positive(self):
        """Gamma should always be positive."""
        g = gamma(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert g > 0

    def test_atm_gamma_highest(self):
        """ATM options should have highest gamma."""
        g_atm = gamma(S=100, K=100, T=1, r=0.05, sigma=0.2)
        g_itm = gamma(S=120, K=100, T=1, r=0.05, sigma=0.2)
        g_otm = gamma(S=80, K=100, T=1, r=0.05, sigma=0.2)
        assert g_atm > g_itm
        assert g_atm > g_otm

    def test_known_value(self):
        """Test against known value."""
        g = gamma(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert np.isclose(g, 0.0188, atol=0.001)


class TestTheta:
    def test_call_theta_negative(self):
        """Call theta should be negative (time decay)."""
        call_theta, _ = theta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert call_theta < 0

    def test_known_value(self):
        """Test against known value."""
        call_theta, _ = theta(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert np.isclose(call_theta, -6.41, atol=0.1)


class TestVega:
    def test_vega_positive(self):
        """Vega should always be positive."""
        v = vega(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert v > 0

    def test_atm_vega_highest(self):
        """ATM options should have highest vega."""
        v_atm = vega(S=100, K=100, T=1, r=0.05, sigma=0.2)
        v_itm = vega(S=120, K=100, T=1, r=0.05, sigma=0.2)
        v_otm = vega(S=80, K=100, T=1, r=0.05, sigma=0.2)
        assert v_atm > v_itm
        assert v_atm > v_otm

    def test_known_value(self):
        """Test against known value."""
        v = vega(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert np.isclose(v, 37.52, atol=0.1)


class TestGreeksFunction:
    def test_returns_all_greeks(self):
        """greeks() should return dict with all Greeks."""
        result = greeks(S=100, K=100, T=1, r=0.05, sigma=0.2)
        assert 'delta' in result
        assert 'gamma' in result
        assert 'theta' in result
        assert 'vega' in result

    def test_consistency_with_individual_functions(self):
        """greeks() should match individual function results."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2

        result = greeks(S, K, T, r, sigma)
        d = delta(S, K, T, r, sigma)
        g = gamma(S, K, T, r, sigma)
        t = theta(S, K, T, r, sigma)
        v = vega(S, K, T, r, sigma)

        assert np.isclose(result['delta'][0], d[0])
        assert np.isclose(result['delta'][1], d[1])
        assert np.isclose(result['gamma'], g)
        assert np.isclose(result['theta'][0], t[0])
        assert np.isclose(result['theta'][1], t[1])
        assert np.isclose(result['vega'], v)


class TestVectorization:
    def test_delta_vectorized(self):
        """Delta should work with numpy arrays."""
        strikes = np.array([90, 95, 100, 105, 110])
        call_deltas, put_deltas = delta(S=100, K=strikes, T=1, r=0.05, sigma=0.2)
        assert len(call_deltas) == 5
        assert len(put_deltas) == 5
        # Deltas should decrease as strike increases
        assert all(np.diff(call_deltas) < 0)

    def test_gamma_vectorized(self):
        """Gamma should work with numpy arrays."""
        strikes = np.array([90, 95, 100, 105, 110])
        gammas = gamma(S=100, K=strikes, T=1, r=0.05, sigma=0.2)
        assert len(gammas) == 5
        assert all(gammas > 0)

    def test_theta_vectorized(self):
        """Theta should work with numpy arrays."""
        strikes = np.array([90, 95, 100, 105, 110])
        call_thetas, put_thetas = theta(S=100, K=strikes, T=1, r=0.05, sigma=0.2)
        assert len(call_thetas) == 5
        assert len(put_thetas) == 5

    def test_vega_vectorized(self):
        """Vega should work with numpy arrays."""
        strikes = np.array([90, 95, 100, 105, 110])
        vegas = vega(S=100, K=strikes, T=1, r=0.05, sigma=0.2)
        assert len(vegas) == 5
        assert all(vegas > 0)

    def test_greeks_vectorized(self):
        """greeks() should work with numpy arrays."""
        strikes = np.array([90, 95, 100, 105, 110])
        result = greeks(S=100, K=strikes, T=1, r=0.05, sigma=0.2)
        assert len(result['delta'][0]) == 5
        assert len(result['gamma']) == 5
        assert len(result['theta'][0]) == 5
        assert len(result['vega']) == 5
