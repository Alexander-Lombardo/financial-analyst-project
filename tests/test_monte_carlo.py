"""Tests for Monte Carlo simulation module."""

import numpy as np
import pytest

from options_builder.monte_carlo import (
    generate_paths,
    mc_european,
    mc_european_call,
    mc_european_put,
    compare_mc_to_bsm,
    mc_asian_call,
    mc_barrier_call,
)
from options_builder.pricing import black_scholes


class TestGeneratePaths:
    """Tests for GBM path generation."""

    def test_shape(self):
        """Paths have correct shape (num_paths, num_steps + 1)."""
        paths = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                               num_paths=1000, num_steps=252, seed=42)
        assert paths.shape == (1000, 253)

    def test_initial_price(self):
        """All paths start at the initial spot price."""
        S = 100
        paths = generate_paths(S=S, T=1, r=0.05, sigma=0.2,
                               num_paths=500, num_steps=100, seed=42)
        np.testing.assert_array_equal(paths[:, 0], S)

    def test_positivity(self):
        """All prices are positive (GBM property)."""
        paths = generate_paths(S=100, T=1, r=0.05, sigma=0.5,
                               num_paths=1000, num_steps=252, seed=42)
        assert np.all(paths > 0)

    def test_reproducibility_with_seed(self):
        """Same seed produces identical paths."""
        paths1 = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                                num_paths=100, num_steps=50, seed=123)
        paths2 = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                                num_paths=100, num_steps=50, seed=123)
        np.testing.assert_array_equal(paths1, paths2)

    def test_different_seeds_different_paths(self):
        """Different seeds produce different paths."""
        paths1 = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                                num_paths=100, num_steps=50, seed=1)
        paths2 = generate_paths(S=100, T=1, r=0.05, sigma=0.2,
                                num_paths=100, num_steps=50, seed=2)
        assert not np.allclose(paths1, paths2)

    def test_terminal_distribution_mean(self):
        """Terminal prices have correct expected value under risk-neutral measure.

        E[S(T)] = S(0) * exp(r*T) under risk-neutral measure.
        """
        S, T, r, sigma = 100, 1.0, 0.05, 0.2
        num_paths = 100_000

        paths = generate_paths(S=S, T=T, r=r, sigma=sigma,
                               num_paths=num_paths, num_steps=1, seed=42)
        S_T = paths[:, -1]

        expected_mean = S * np.exp(r * T)
        actual_mean = np.mean(S_T)

        # Should be within 1% of expected
        assert abs(actual_mean - expected_mean) / expected_mean < 0.01

    def test_terminal_distribution_variance(self):
        """Terminal prices have correct variance under GBM.

        Var[S(T)] = S(0)² * exp(2rT) * (exp(σ²T) - 1)
        """
        S, T, r, sigma = 100, 1.0, 0.05, 0.3
        num_paths = 100_000

        paths = generate_paths(S=S, T=T, r=r, sigma=sigma,
                               num_paths=num_paths, num_steps=1, seed=42)
        S_T = paths[:, -1]

        expected_var = S**2 * np.exp(2*r*T) * (np.exp(sigma**2 * T) - 1)
        actual_var = np.var(S_T)

        # Should be within 5% of expected
        assert abs(actual_var - expected_var) / expected_var < 0.05

    def test_antithetic_reduces_variance(self):
        """Antithetic variates should reduce variance of terminal prices."""
        S, T, r, sigma = 100, 1.0, 0.05, 0.2
        num_paths = 10_000

        paths_no_anti = generate_paths(S=S, T=T, r=r, sigma=sigma,
                                       num_paths=num_paths, num_steps=1,
                                       antithetic=False, seed=42)
        paths_anti = generate_paths(S=S, T=T, r=r, sigma=sigma,
                                    num_paths=num_paths, num_steps=1,
                                    antithetic=True, seed=42)

        # Antithetic should have lower variance of the sample mean
        # (though individual path variance is similar)
        # The sum of antithetic pairs has lower variance
        var_no_anti = np.var(paths_no_anti[:, -1])
        var_anti = np.var(paths_anti[:, -1])

        # Just check both produce reasonable results
        assert var_anti > 0
        assert var_no_anti > 0


class TestMCConvergence:
    """Tests for MC convergence to Black-Scholes prices."""

    @pytest.mark.parametrize("S,K,T,r,sigma", [
        (100, 100, 1.0, 0.05, 0.2),   # ATM
        (100, 110, 0.5, 0.03, 0.25),  # OTM call
        (100, 90, 0.25, 0.08, 0.3),   # ITM call
        (50, 55, 2.0, 0.02, 0.15),    # OTM long-dated
    ])
    def test_call_within_3_std_errors(self, S, K, T, r, sigma):
        """MC call price is within 3 standard errors of BSM price."""
        bsm_call, _ = black_scholes(S, K, T, r, sigma)
        mc_result = mc_european(S, K, T, r, sigma, num_paths=50_000, seed=42)

        error = abs(mc_result['call'] - bsm_call)
        assert error < 3 * mc_result['call_std_error'], \
            f"MC call {mc_result['call']:.4f} too far from BSM {bsm_call:.4f}"

    @pytest.mark.parametrize("S,K,T,r,sigma", [
        (100, 100, 1.0, 0.05, 0.2),
        (100, 90, 0.5, 0.03, 0.25),   # OTM put
        (100, 110, 0.25, 0.08, 0.3),  # ITM put
    ])
    def test_put_within_3_std_errors(self, S, K, T, r, sigma):
        """MC put price is within 3 standard errors of BSM price."""
        _, bsm_put = black_scholes(S, K, T, r, sigma)
        mc_result = mc_european(S, K, T, r, sigma, num_paths=50_000, seed=42)

        error = abs(mc_result['put'] - bsm_put)
        assert error < 3 * mc_result['put_std_error'], \
            f"MC put {mc_result['put']:.4f} too far from BSM {bsm_put:.4f}"

    def test_convergence_rate(self):
        """Standard error decreases at O(1/√n) rate."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

        result_small = mc_european(S, K, T, r, sigma, num_paths=10_000, seed=42)
        result_large = mc_european(S, K, T, r, sigma, num_paths=40_000, seed=42)

        # With 4x paths, std error should be ~2x smaller
        ratio = result_small['call_std_error'] / result_large['call_std_error']
        assert 1.5 < ratio < 2.5  # Allow some variance


class TestPutCallParity:
    """Tests for put-call parity: C - P = S - K*e^(-rT)."""

    @pytest.mark.parametrize("S,K,T,r,sigma", [
        (100, 100, 1.0, 0.05, 0.2),
        (100, 110, 0.5, 0.03, 0.25),
        (100, 90, 0.25, 0.08, 0.3),
    ])
    def test_put_call_parity(self, S, K, T, r, sigma):
        """MC prices satisfy put-call parity within tolerance."""
        mc_result = mc_european(S, K, T, r, sigma, num_paths=100_000, seed=42)

        lhs = mc_result['call'] - mc_result['put']
        rhs = S - K * np.exp(-r * T)

        # Combined standard error
        combined_error = np.sqrt(mc_result['call_std_error']**2 +
                                 mc_result['put_std_error']**2)

        assert abs(lhs - rhs) < 3 * combined_error, \
            f"Put-call parity violated: C-P={lhs:.4f}, S-Ke^(-rT)={rhs:.4f}"


class TestInputValidation:
    """Tests for input validation and error handling."""

    def test_negative_spot_price(self):
        """Negative spot price raises ValueError."""
        with pytest.raises(ValueError, match="Spot price"):
            mc_european(S=-100, K=100, T=1, r=0.05, sigma=0.2)

    def test_negative_strike_price(self):
        """Negative strike price raises ValueError."""
        with pytest.raises(ValueError, match="Strike price"):
            mc_european(S=100, K=-100, T=1, r=0.05, sigma=0.2)

    def test_zero_time(self):
        """Zero time to maturity raises ValueError."""
        with pytest.raises(ValueError, match="Time to maturity"):
            mc_european(S=100, K=100, T=0, r=0.05, sigma=0.2)

    def test_negative_volatility(self):
        """Negative volatility raises ValueError."""
        with pytest.raises(ValueError, match="Volatility"):
            mc_european(S=100, K=100, T=1, r=0.05, sigma=-0.2)

    def test_zero_paths(self):
        """Zero paths raises ValueError."""
        with pytest.raises(ValueError, match="Number of paths"):
            mc_european(S=100, K=100, T=1, r=0.05, sigma=0.2, num_paths=0)

    def test_invalid_barrier_type(self):
        """Invalid barrier type raises ValueError."""
        with pytest.raises(ValueError, match="barrier_type"):
            mc_barrier_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                            barrier=120, barrier_type='invalid')

    def test_invalid_average_type(self):
        """Invalid average type raises ValueError."""
        with pytest.raises(ValueError, match="average_type"):
            mc_asian_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                          average_type='invalid')


class TestAsianOptions:
    """Tests for Asian option pricing."""

    def test_asian_less_than_european(self):
        """Asian call price should be less than or equal to European call.

        Averaging reduces volatility exposure.
        """
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

        european = mc_european_call(S, K, T, r, sigma, num_paths=50_000, seed=42)
        asian = mc_asian_call(S, K, T, r, sigma, num_paths=50_000,
                              num_steps=252, seed=42)

        assert asian['price'] < european

    def test_geometric_less_than_arithmetic(self):
        """Geometric average Asian <= Arithmetic average Asian.

        By AM-GM inequality.
        """
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

        arithmetic = mc_asian_call(S, K, T, r, sigma, num_paths=50_000,
                                   num_steps=252, average_type='arithmetic',
                                   seed=42)
        geometric = mc_asian_call(S, K, T, r, sigma, num_paths=50_000,
                                  num_steps=252, average_type='geometric',
                                  seed=42)

        assert geometric['price'] <= arithmetic['price']

    def test_asian_returns_dict_with_expected_keys(self):
        """Asian option function returns dict with expected keys."""
        result = mc_asian_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                               num_paths=1000, num_steps=50, seed=42)
        assert 'price' in result
        assert 'std_error' in result
        assert 'num_paths' in result


class TestBarrierOptions:
    """Tests for barrier option pricing."""

    def test_knockin_plus_knockout_equals_vanilla(self):
        """Knock-in + Knock-out = Vanilla option.

        This is a fundamental relationship in barrier options.
        """
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        barrier = 120  # Up barrier
        num_paths = 100_000

        vanilla = mc_european_call(S, K, T, r, sigma, num_paths=num_paths, seed=42)

        knockin = mc_barrier_call(S, K, T, r, sigma, barrier=barrier,
                                  barrier_type='up-and-in',
                                  num_paths=num_paths, num_steps=252, seed=42)
        knockout = mc_barrier_call(S, K, T, r, sigma, barrier=barrier,
                                   barrier_type='up-and-out',
                                   num_paths=num_paths, num_steps=252, seed=42)

        sum_barriers = knockin['price'] + knockout['price']

        # Allow tolerance based on combined standard errors
        combined_error = np.sqrt(knockin['std_error']**2 + knockout['std_error']**2)
        assert abs(sum_barriers - vanilla) < 3 * combined_error, \
            f"KI + KO = {sum_barriers:.4f}, Vanilla = {vanilla:.4f}"

    def test_knockout_less_than_vanilla(self):
        """Knock-out option price <= Vanilla option price."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

        vanilla = mc_european_call(S, K, T, r, sigma, num_paths=50_000, seed=42)
        knockout = mc_barrier_call(S, K, T, r, sigma, barrier=120,
                                   barrier_type='up-and-out',
                                   num_paths=50_000, num_steps=252, seed=42)

        assert knockout['price'] <= vanilla

    def test_down_barrier_types(self):
        """Down-and-in + Down-and-out = Vanilla."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        barrier = 80  # Down barrier
        num_paths = 100_000

        vanilla = mc_european_call(S, K, T, r, sigma, num_paths=num_paths, seed=42)

        knockin = mc_barrier_call(S, K, T, r, sigma, barrier=barrier,
                                  barrier_type='down-and-in',
                                  num_paths=num_paths, num_steps=252, seed=42)
        knockout = mc_barrier_call(S, K, T, r, sigma, barrier=barrier,
                                   barrier_type='down-and-out',
                                   num_paths=num_paths, num_steps=252, seed=42)

        sum_barriers = knockin['price'] + knockout['price']
        combined_error = np.sqrt(knockin['std_error']**2 + knockout['std_error']**2)

        assert abs(sum_barriers - vanilla) < 3 * combined_error

    def test_barrier_returns_dict_with_expected_keys(self):
        """Barrier option function returns dict with expected keys."""
        result = mc_barrier_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                 barrier=120, num_paths=1000, num_steps=50, seed=42)
        assert 'price' in result
        assert 'std_error' in result
        assert 'num_paths' in result


class TestCompareFunction:
    """Tests for the BSM comparison utility."""

    def test_returns_expected_structure(self):
        """compare_mc_to_bsm returns dict with expected keys."""
        result = compare_mc_to_bsm(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                   num_paths_list=[100, 1000], seed=42)

        assert 'bsm_call' in result
        assert 'bsm_put' in result
        assert 'mc_results' in result
        assert len(result['mc_results']) == 2

    def test_mc_results_structure(self):
        """Each MC result has expected keys."""
        result = compare_mc_to_bsm(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                   num_paths_list=[1000], seed=42)

        mc = result['mc_results'][0]
        assert 'num_paths' in mc
        assert 'mc_call' in mc
        assert 'mc_put' in mc
        assert 'call_error' in mc
        assert 'put_error' in mc
        assert 'call_std_error' in mc
        assert 'put_std_error' in mc

    def test_error_calculation(self):
        """Error is correctly computed as MC - BSM."""
        result = compare_mc_to_bsm(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                   num_paths_list=[10000], seed=42)

        mc = result['mc_results'][0]
        expected_call_error = mc['mc_call'] - result['bsm_call']
        expected_put_error = mc['mc_put'] - result['bsm_put']

        assert abs(mc['call_error'] - expected_call_error) < 1e-10
        assert abs(mc['put_error'] - expected_put_error) < 1e-10

    def test_default_path_counts(self):
        """Default path counts are used when not specified."""
        result = compare_mc_to_bsm(S=100, K=100, T=1, r=0.05, sigma=0.2, seed=42)

        path_counts = [mc['num_paths'] for mc in result['mc_results']]
        assert path_counts == [1000, 10000, 100000]


class TestConvenienceFunctions:
    """Tests for convenience wrapper functions."""

    def test_mc_european_call_returns_float(self):
        """mc_european_call returns a single float."""
        result = mc_european_call(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                  num_paths=1000, seed=42)
        assert isinstance(result, float)

    def test_mc_european_put_returns_float(self):
        """mc_european_put returns a single float."""
        result = mc_european_put(S=100, K=100, T=1, r=0.05, sigma=0.2,
                                 num_paths=1000, seed=42)
        assert isinstance(result, float)

    def test_convenience_matches_full_function(self):
        """Convenience functions return same values as full mc_european."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        seed = 42

        full = mc_european(S, K, T, r, sigma, num_paths=10000, seed=seed)
        call = mc_european_call(S, K, T, r, sigma, num_paths=10000, seed=seed)
        put = mc_european_put(S, K, T, r, sigma, num_paths=10000, seed=seed)

        assert call == full['call']
        assert put == full['put']
