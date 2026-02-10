"""Tests for OptionStrategy and StrategyLeg."""

import pytest
import numpy as np
from datetime import date

from options_builder.strategy import StrategyLeg, OptionStrategy
from options_builder.data_manager import DataManager
from options_builder.chain_analyzer import PricedChain, PricedChainRow, PricedOption


@pytest.fixture
def sample_option_data():
    """Sample option data dict (as from dm.lookup_option)."""
    return {
        'ticker': 'SPY',
        'expiration': date(2026, 3, 20),
        'type': 'call',
        'strike': 500.0,
        'bid': 4.80,
        'ask': 5.20,
        'mid': 5.00,
        'iv': 0.20,
        'delta': 0.50,
        'gamma': 0.03,
        'theta': -0.05,
        'vega': 0.20,
        'open_interest': 1000,
        'volume': 500,
        'model_price': 5.02,
        'underlying_price': 500.0,
        'time_to_maturity': 0.1,
        'risk_free_rate': 0.05,
    }


@pytest.fixture
def sample_dm():
    """DataManager with sample chain for testing."""
    dm = DataManager()
    rows = [
        PricedChainRow(
            strike=495.0,
            call=PricedOption(
                strike=495.0, option_type='call',
                bid=9.80, ask=10.20, mid_price=10.0,
                open_interest=500, volume=200,
                implied_volatility=0.22, delta=0.65,
                gamma=0.02, theta=-0.04, vega=0.18,
                model_price=10.05
            ),
            put=PricedOption(
                strike=495.0, option_type='put',
                bid=2.30, ask=2.70, mid_price=2.5,
                open_interest=600, volume=150,
                implied_volatility=0.22, delta=-0.35,
                gamma=0.02, theta=-0.03, vega=0.18,
                model_price=2.52
            )
        ),
        PricedChainRow(
            strike=500.0,
            call=PricedOption(
                strike=500.0, option_type='call',
                bid=4.80, ask=5.20, mid_price=5.0,
                open_interest=1000, volume=500,
                implied_volatility=0.20, delta=0.50,
                gamma=0.03, theta=-0.05, vega=0.20,
                model_price=5.02
            ),
            put=PricedOption(
                strike=500.0, option_type='put',
                bid=4.80, ask=5.20, mid_price=5.0,
                open_interest=1200, volume=400,
                implied_volatility=0.20, delta=-0.50,
                gamma=0.03, theta=-0.04, vega=0.20,
                model_price=5.01
            )
        ),
        PricedChainRow(
            strike=505.0,
            call=PricedOption(
                strike=505.0, option_type='call',
                bid=2.30, ask=2.70, mid_price=2.5,
                open_interest=800, volume=300,
                implied_volatility=0.18, delta=0.35,
                gamma=0.02, theta=-0.03, vega=0.15,
                model_price=2.48
            ),
            put=PricedOption(
                strike=505.0, option_type='put',
                bid=9.80, ask=10.20, mid_price=10.0,
                open_interest=400, volume=100,
                implied_volatility=0.18, delta=-0.65,
                gamma=0.02, theta=-0.04, vega=0.15,
                model_price=9.98
            )
        ),
    ]
    chain = PricedChain(
        ticker='SPY',
        expiration=date(2026, 3, 20),
        underlying_price=500.0,
        time_to_maturity=0.1,
        risk_free_rate=0.05,
        rows=rows
    )
    dm.add_chain(chain)
    return dm


class TestStrategyLeg:
    """Tests for StrategyLeg class."""

    def test_from_lookup(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)

        assert leg.strike == 500.0
        assert leg.option_type == 'call'
        assert leg.quantity == 1
        assert leg.delta == 0.50
        assert leg.mid == 5.00

    def test_long_position(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=2)

        assert leg.is_long
        assert not leg.is_short
        assert leg.quantity == 2

    def test_short_position(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=-2)

        assert leg.is_short
        assert not leg.is_long
        assert leg.quantity == -2

    def test_is_call_put(self, sample_option_data):
        call_leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)
        assert call_leg.is_call
        assert not call_leg.is_put

        sample_option_data['type'] = 'put'
        put_leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)
        assert put_leg.is_put
        assert not put_leg.is_call

    def test_net_delta_long(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)
        # delta=0.50, quantity=1, *100 = 50
        assert leg.net_delta == 50.0

    def test_net_delta_short(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=-1)
        # delta=0.50, quantity=-1, *100 = -50
        assert leg.net_delta == -50.0

    def test_net_delta_multiple_contracts(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=3)
        # delta=0.50, quantity=3, *100 = 150
        assert leg.net_delta == 150.0

    def test_net_greeks(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=-2)

        assert leg.net_delta == -2 * 0.50 * 100
        assert leg.net_gamma == -2 * 0.03 * 100
        assert leg.net_theta == -2 * -0.05 * 100  # Note: theta is negative
        assert leg.net_vega == -2 * 0.20 * 100

    def test_cost_long(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)
        # Long pays ask: 5.20 * 1 * 100 = 520
        assert leg.cost == 520.0

    def test_cost_short(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=-1)
        # Short receives bid: 4.80 * -1 * 100 = -480
        assert leg.cost == -480.0

    def test_mid_cost(self, sample_option_data):
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=2)
        # 5.00 * 2 * 100 = 1000
        assert leg.mid_cost == 1000.0


class TestOptionStrategy:
    """Tests for OptionStrategy class."""

    def test_init_empty(self):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        assert len(strategy) == 0
        assert strategy.legs == []

    def test_add_leg(self, sample_option_data):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        leg = StrategyLeg.from_lookup(sample_option_data, quantity=1)
        strategy.add_leg(leg)

        assert len(strategy) == 1

    def test_add_leg_from_lookup(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )

        result = strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        assert result is True
        assert len(strategy) == 1
        assert strategy.legs[0].strike == 500.0

    def test_add_leg_from_lookup_not_found(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )

        result = strategy.add_leg_from_lookup(sample_dm, 999.0, 'call', 1)
        assert result is False
        assert len(strategy) == 0


class TestOptionStrategyGreeks:
    """Tests for aggregated Greeks."""

    def test_total_delta_single_leg(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)

        # delta=0.50 * 1 * 100 = 50
        assert strategy.total_delta == 50.0

    def test_total_delta_bull_call_spread(self, sample_dm):
        """Bull call spread: long lower strike, short higher strike."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0,
            name='Bull Call Spread'
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)   # Long
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)  # Short

        # Long 500C: 0.50 * 1 * 100 = 50
        # Short 505C: 0.35 * -1 * 100 = -35
        # Total: 15
        assert strategy.total_delta == 15.0

    def test_total_greeks_vertical_spread(self, sample_dm):
        """Test all Greeks for a vertical spread."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        # Delta: (0.50 - 0.35) * 100 = 15
        assert strategy.total_delta == pytest.approx(15.0)

        # Gamma: (0.03 - 0.02) * 100 = 1
        assert strategy.total_gamma == pytest.approx(1.0)

        # Theta: (-0.05 - (-0.03)) * 100 = -2
        assert strategy.total_theta == pytest.approx(-2.0)

        # Vega: (0.20 - 0.15) * 100 = 5
        assert strategy.total_vega == pytest.approx(5.0)


class TestOptionStrategyCost:
    """Tests for strategy cost calculations."""

    def test_net_premium_debit(self, sample_dm):
        """Bull call spread is a debit spread."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)   # Long: pay ask
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)  # Short: receive bid

        # Long 500C: 5.20 * 1 * 100 = 520 (debit)
        # Short 505C: 2.30 * -1 * 100 = -230 (credit)
        # Net: 290 (debit)
        assert strategy.net_premium == pytest.approx(290.0)
        assert strategy.is_debit
        assert not strategy.is_credit

    def test_net_premium_credit(self, sample_dm):
        """Bear call spread is a credit spread."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', -1)  # Short: receive bid
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', 1)   # Long: pay ask

        # Short 500C: 4.80 * -1 * 100 = -480 (credit)
        # Long 505C: 2.70 * 1 * 100 = 270 (debit)
        # Net: -210 (credit)
        assert strategy.net_premium == pytest.approx(-210.0)
        assert strategy.is_credit
        assert not strategy.is_debit

    def test_net_premium_mid(self, sample_dm):
        """Net premium using mid prices."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        # Long 500C: 5.00 * 1 * 100 = 500
        # Short 505C: 2.50 * -1 * 100 = -250
        # Net: 250
        assert strategy.net_premium_mid == pytest.approx(250.0)


class TestOptionStrategyHelpers:
    """Tests for helper methods."""

    def test_calls_and_puts(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'put', -1)

        assert len(strategy.calls) == 1
        assert len(strategy.puts) == 1

    def test_long_and_short_legs(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        assert len(strategy.long_legs) == 1
        assert len(strategy.short_legs) == 1

    def test_strikes(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        assert strategy.strikes == [500.0, 505.0]

    def test_get_leg(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        leg = strategy.get_leg(500.0, 'call')
        assert leg is not None
        assert leg.quantity == 1

        assert strategy.get_leg(999.0, 'call') is None

    def test_summary(self, sample_dm):
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0,
            name='Bull Call Spread'
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)

        summary = strategy.summary()

        assert summary['name'] == 'Bull Call Spread'
        assert summary['ticker'] == 'SPY'
        assert summary['num_legs'] == 2
        assert summary['is_debit'] is True
        assert 'total_delta' in summary


class TestOptionStrategyPnL:
    """Tests for P&L calculation."""

    def test_generate_price_range(self, sample_dm):
        """Price range should span 80% to 120% of underlying."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )

        prices = strategy.generate_price_range(pct_range=0.2, num_points=5)

        assert len(prices) == 5
        assert prices[0] == pytest.approx(400.0)   # 80%
        assert prices[-1] == pytest.approx(600.0)  # 120%
        assert prices[2] == pytest.approx(500.0)   # center

    def test_long_call_pnl(self, sample_dm):
        """Long call: max loss = premium, unlimited upside."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)

        prices = np.array([450.0, 500.0, 550.0])
        pnl = strategy.calculate_pnl(prices)

        # At 450: payoff=0, cost=520 → P&L = -520
        assert pnl[0] == pytest.approx(-520.0)

        # At 500: payoff=0, cost=520 → P&L = -520
        assert pnl[1] == pytest.approx(-520.0)

        # At 550: payoff=50*100=5000, cost=520 → P&L = 4480
        assert pnl[2] == pytest.approx(4480.0)

    def test_bull_call_spread_pnl(self, sample_dm):
        """Bull call spread: capped profit and loss."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)   # Long 500C
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)  # Short 505C

        prices = np.array([490.0, 502.5, 510.0])
        pnl = strategy.calculate_pnl(prices)

        # Below 500: both expire worthless
        # Long 500C: payoff=0, cost=520 → -520
        # Short 505C: payoff=0, cost=-230 → +230
        # Total: -290
        assert pnl[0] == pytest.approx(-290.0)

        # At 502.5: long call ITM by 2.5
        # Long 500C: payoff=2.5*100=250, cost=520 → -270
        # Short 505C: payoff=0, cost=-230 → +230
        # Total: -40
        assert pnl[1] == pytest.approx(-40.0)

        # Above 505: max profit = spread width - net debit = 500 - 290 = 210
        # Long 500C: payoff=10*100=1000, cost=520 → +480
        # Short 505C: payoff=5*100=500, cost=-230 (we owe 500) → -270
        # Total: 210
        assert pnl[2] == pytest.approx(210.0)

    def test_pnl_data_returns_tuple(self, sample_dm):
        """pnl_data should return (prices, pnl) tuple."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)

        prices, pnl = strategy.pnl_data(num_points=50)

        assert len(prices) == 50
        assert len(pnl) == 50
        assert isinstance(prices, np.ndarray)
        assert isinstance(pnl, np.ndarray)

    def test_short_put_pnl(self, sample_dm):
        """Short put: max profit = premium, large downside risk."""
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'put', -1)

        prices = np.array([450.0, 500.0, 550.0])
        pnl = strategy.calculate_pnl(prices)

        # Short 500P cost = bid * -1 * 100 = 4.80 * -1 * 100 = -480 (credit)

        # At 450: payoff=50, quantity=-1 → we owe 50*100=5000
        # P&L = -5000 - (-480) = -5000 + 480 = -4520
        assert pnl[0] == pytest.approx(-4520.0)

        # At 500: payoff=0, we keep premium
        # P&L = 0 - (-480) = 480
        assert pnl[1] == pytest.approx(480.0)

        # At 550: payoff=0, we keep premium
        # P&L = 0 - (-480) = 480
        assert pnl[2] == pytest.approx(480.0)


class TestPhase3Validation:
    """Phase 3 validation tests for strategy logic."""

    def test_synthetic_long_delta_zero_sum(self, sample_dm):
        """
        Step 3.1: Synthetic Long (Long Call + Short Put at same strike).
        Net Delta should be approximately 100 (representing 1.0 delta per share).
        """
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0,
            name='Synthetic Long'
        )
        # Long Call + Short Put at same strike = Synthetic Long Stock
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'put', -1)

        # Long 500C delta: 0.50 * 1 * 100 = 50
        # Short 500P delta: -0.50 * -1 * 100 = 50
        # Total: 100 (equivalent to owning 100 shares)
        assert strategy.total_delta == pytest.approx(100.0, rel=0.01)

    def test_bull_call_spread_pnl_constant_above_upper_strike(self, sample_dm):
        """
        Step 3.2: Bull Call Spread P&L is constant above upper strike.
        For K1=500, K2=505, P&L should be identical at 510, 520, 550, 600.
        """
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0,
            name='Bull Call Spread'
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)   # Long lower
        strategy.add_leg_from_lookup(sample_dm, 505.0, 'call', -1)  # Short upper

        # Test prices above upper strike (505)
        prices_above = np.array([510.0, 520.0, 550.0, 600.0])
        pnl = strategy.calculate_pnl(prices_above)

        # All P&L values should be identical (max profit)
        max_profit = pnl[0]
        for i, p in enumerate(pnl):
            assert p == pytest.approx(max_profit), f"P&L at {prices_above[i]} differs from max profit"

        # Verify the max profit equals spread width minus net debit
        # Spread width: 5 * 100 = 500
        # Net debit: 520 - 230 = 290
        # Max profit: 500 - 290 = 210
        assert max_profit == pytest.approx(210.0)

    def test_long_call_max_loss_bounded_by_premium(self, sample_dm):
        """
        Step 3.3: Max Loss on Long Call never exceeds premium paid.
        The payoff floor max(0, S-K) ensures loss is capped.
        """
        strategy = OptionStrategy(
            ticker='SPY',
            expiration=date(2026, 3, 20),
            underlying_price=500.0
        )
        strategy.add_leg_from_lookup(sample_dm, 500.0, 'call', 1)

        # Premium paid = ask * quantity * 100 = 5.20 * 1 * 100 = 520
        premium_paid = strategy.net_premium
        assert premium_paid == pytest.approx(520.0)

        # Test across wide range of prices, including extreme lows
        prices = np.linspace(0, 600, 1000)
        pnl = strategy.calculate_pnl(prices)

        # Max loss should equal premium paid (no more)
        max_loss = -pnl.min()
        assert max_loss == pytest.approx(premium_paid)

        # Verify no P&L value is worse than -premium
        assert all(p >= -premium_paid for p in pnl), "P&L dropped below max loss bound"
