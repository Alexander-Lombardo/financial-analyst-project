"""Tests for OptionStrategy and StrategyLeg."""

import pytest
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
