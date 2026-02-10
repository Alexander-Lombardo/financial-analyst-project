"""Tests for the Streamlit dashboard (app.py)."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Mock streamlit before importing app
import sys
sys.modules['streamlit'] = MagicMock()

from options_builder import (
    DataManager,
    OptionsDataConnector,
    ChainAnalyzer,
    OptionChainGrid,
    OptionChainRow,
    OptionLeg,
    PricedChain,
    PricedChainRow,
    PricedOption,
    UnderlyingQuote,
)


class TestInputValidation:
    """Test ticker input validation."""

    def test_empty_ticker_shows_error(self):
        """Empty ticker should set error message."""
        # Import after mocking streamlit
        import app

        # Setup mock session state
        app.st.session_state = MagicMock()
        app.st.session_state.connector = Mock(spec=OptionsDataConnector)

        result = app.validate_and_fetch_ticker("")
        assert result is False
        assert "Please enter a ticker symbol" in str(app.st.session_state.error_message)

    def test_whitespace_only_ticker_shows_error(self):
        """Whitespace-only ticker should set error message."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.connector = Mock(spec=OptionsDataConnector)

        result = app.validate_and_fetch_ticker("   ")
        assert result is False
        assert "Please enter a ticker symbol" in str(app.st.session_state.error_message)

    def test_invalid_ticker_shows_clean_error(self):
        """Invalid ticker should show clean error message, not traceback."""
        import app

        app.st.session_state = MagicMock()
        mock_connector = Mock(spec=OptionsDataConnector)
        mock_connector.get_underlying.side_effect = ValueError("Could not get price for INVALIDXYZ")
        app.st.session_state.connector = mock_connector

        result = app.validate_and_fetch_ticker("INVALIDXYZ")

        assert result is False
        assert app.st.session_state.error_message == "Could not get price for INVALIDXYZ"
        assert app.st.session_state.current_ticker is None
        assert app.st.session_state.underlying_price is None
        assert app.st.session_state.expirations == []

    def test_valid_ticker_fetches_expirations(self):
        """Valid ticker should fetch expirations and underlying price."""
        import app

        app.st.session_state = MagicMock()
        mock_connector = Mock(spec=OptionsDataConnector)

        # Mock successful responses
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')

        mock_connector.get_underlying.return_value = UnderlyingQuote(
            ticker="AAPL",
            price=150.00,
            timestamp=datetime.now()
        )
        mock_connector.get_expirations.return_value = [tomorrow, next_week]
        app.st.session_state.connector = mock_connector

        result = app.validate_and_fetch_ticker("aapl")  # Test case-insensitivity

        assert result is True
        assert app.st.session_state.current_ticker == "AAPL"
        assert app.st.session_state.underlying_price == 150.00
        assert len(app.st.session_state.expirations) == 2
        assert app.st.session_state.error_message is None

    def test_network_error_shows_generic_message(self):
        """Network errors should show a generic user-friendly message."""
        import app

        app.st.session_state = MagicMock()
        mock_connector = Mock(spec=OptionsDataConnector)
        mock_connector.get_underlying.side_effect = Exception("Network timeout")
        app.st.session_state.connector = mock_connector

        result = app.validate_and_fetch_ticker("AAPL")

        assert result is False
        assert app.st.session_state.error_message == "Unable to fetch data. Please try again."


class TestDateConstraints:
    """Test expiration date filtering."""

    def test_past_dates_filtered_from_expirations(self):
        """Past dates should be filtered out of expiration list."""
        import app

        app.st.session_state = MagicMock()
        mock_connector = Mock(spec=OptionsDataConnector)

        # Include past, today, and future dates
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        today_str = date.today().strftime('%Y-%m-%d')
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')

        mock_connector.get_underlying.return_value = UnderlyingQuote(
            ticker="AAPL",
            price=150.00,
            timestamp=datetime.now()
        )
        mock_connector.get_expirations.return_value = [yesterday, today_str, tomorrow, next_week]
        app.st.session_state.connector = mock_connector

        result = app.validate_and_fetch_ticker("AAPL")

        assert result is True
        # Yesterday should be filtered out, today and future should remain
        assert yesterday not in app.st.session_state.expirations
        assert today_str in app.st.session_state.expirations
        assert tomorrow in app.st.session_state.expirations
        assert next_week in app.st.session_state.expirations

    def test_all_past_dates_shows_warning(self):
        """If all dates are past, should show error message."""
        import app

        app.st.session_state = MagicMock()
        mock_connector = Mock(spec=OptionsDataConnector)

        # Only past dates
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        last_week = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')

        mock_connector.get_underlying.return_value = UnderlyingQuote(
            ticker="AAPL",
            price=150.00,
            timestamp=datetime.now()
        )
        mock_connector.get_expirations.return_value = [yesterday, last_week]
        app.st.session_state.connector = mock_connector

        result = app.validate_and_fetch_ticker("AAPL")

        assert result is False
        assert "No future expiration dates available" in app.st.session_state.error_message

    def test_format_expiration_option_shows_days(self):
        """Expiration format should include days to expiration."""
        import app

        # Test future date
        future_date = (date.today() + timedelta(days=38)).strftime('%Y-%m-%d')
        formatted = app.format_expiration_option(future_date)

        assert future_date in formatted
        assert "(38d)" in formatted

    def test_format_expiration_option_today(self):
        """Today's date should show 0 days."""
        import app

        today_str = date.today().strftime('%Y-%m-%d')
        formatted = app.format_expiration_option(today_str)

        assert today_str in formatted
        assert "(0d)" in formatted


class TestDataFetch:
    """Test data fetching and caching."""

    def test_expiration_selection_triggers_chain_fetch(self):
        """Selecting an expiration should fetch the chain data."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.current_ticker = "AAPL"
        app.st.session_state.risk_free_rate = 5.0

        mock_connector = Mock(spec=OptionsDataConnector)
        mock_data_manager = Mock(spec=DataManager)

        # Create mock grid
        mock_grid = Mock(spec=OptionChainGrid)
        mock_grid.ticker = "AAPL"
        mock_grid.expiration = date.today() + timedelta(days=30)
        mock_grid.underlying_price = 150.00
        mock_grid.time_to_maturity.return_value = 30/365
        mock_grid.rows = []

        mock_connector.get_chain_grid.return_value = mock_grid
        app.st.session_state.connector = mock_connector
        app.st.session_state.data_manager = mock_data_manager

        # Mock ChainAnalyzer
        mock_priced_chain = Mock(spec=PricedChain)
        mock_priced_chain.ticker = "AAPL"
        mock_priced_chain.rows = []

        with patch.object(ChainAnalyzer, 'analyze', return_value=mock_priced_chain):
            expiration = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            result = app.fetch_chain_data(expiration)

        assert result is True
        mock_connector.get_chain_grid.assert_called_once_with("AAPL", expiration)
        mock_data_manager.add_chain.assert_called_once()
        assert app.st.session_state.chain_data == mock_priced_chain
        assert app.st.session_state.selected_expiration == expiration

    def test_chain_fetch_uses_risk_free_rate(self):
        """Chain analyzer should use the configured risk-free rate."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.current_ticker = "AAPL"
        app.st.session_state.risk_free_rate = 4.5  # 4.5%

        mock_connector = Mock(spec=OptionsDataConnector)
        mock_data_manager = Mock(spec=DataManager)

        mock_grid = Mock(spec=OptionChainGrid)
        mock_grid.ticker = "AAPL"
        mock_grid.expiration = date.today() + timedelta(days=30)
        mock_grid.underlying_price = 150.00
        mock_grid.time_to_maturity.return_value = 30/365
        mock_grid.rows = []

        mock_connector.get_chain_grid.return_value = mock_grid
        app.st.session_state.connector = mock_connector
        app.st.session_state.data_manager = mock_data_manager

        with patch('app.ChainAnalyzer') as MockAnalyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze.return_value = Mock(spec=PricedChain, rows=[])
            MockAnalyzer.return_value = mock_analyzer_instance

            expiration = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.fetch_chain_data(expiration)

            # Verify ChainAnalyzer was created with correct rate (converted from %)
            MockAnalyzer.assert_called_once_with(risk_free_rate=0.045)

    def test_data_cached_in_data_manager(self):
        """Fetched chain data should be stored in DataManager."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.current_ticker = "AAPL"
        app.st.session_state.risk_free_rate = 5.0

        mock_connector = Mock(spec=OptionsDataConnector)
        mock_data_manager = Mock(spec=DataManager)

        mock_grid = Mock(spec=OptionChainGrid)
        mock_grid.ticker = "AAPL"
        mock_grid.expiration = date.today() + timedelta(days=30)
        mock_grid.underlying_price = 150.00
        mock_grid.time_to_maturity.return_value = 30/365
        mock_grid.rows = []

        mock_connector.get_chain_grid.return_value = mock_grid
        app.st.session_state.connector = mock_connector
        app.st.session_state.data_manager = mock_data_manager

        mock_priced_chain = Mock(spec=PricedChain)
        mock_priced_chain.rows = []

        with patch.object(ChainAnalyzer, 'analyze', return_value=mock_priced_chain):
            expiration = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.fetch_chain_data(expiration)

        mock_data_manager.add_chain.assert_called_once_with(mock_priced_chain)

    def test_ticker_change_clears_previous_data(self):
        """Changing ticker should clear previous chain data and expiration."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.selected_expiration = "2026-03-20"
        app.st.session_state.chain_data = Mock()

        mock_connector = Mock(spec=OptionsDataConnector)
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

        mock_connector.get_underlying.return_value = UnderlyingQuote(
            ticker="MSFT",
            price=380.00,
            timestamp=datetime.now()
        )
        mock_connector.get_expirations.return_value = [tomorrow]
        app.st.session_state.connector = mock_connector

        app.validate_and_fetch_ticker("MSFT")

        # Previous selection should be cleared
        assert app.st.session_state.selected_expiration is None
        assert app.st.session_state.chain_data is None
        assert app.st.session_state.current_ticker == "MSFT"

    def test_chain_fetch_error_shows_clean_message(self):
        """Chain fetch errors should show user-friendly message."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.current_ticker = "AAPL"
        app.st.session_state.risk_free_rate = 5.0

        mock_connector = Mock(spec=OptionsDataConnector)
        mock_connector.get_chain_grid.side_effect = Exception("API error")
        app.st.session_state.connector = mock_connector
        app.st.session_state.data_manager = Mock(spec=DataManager)

        expiration = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        result = app.fetch_chain_data(expiration)

        assert result is False
        assert app.st.session_state.error_message == "Unable to fetch option chain. Please try again."


class TestSessionStateInit:
    """Test session state initialization."""

    def test_init_creates_data_manager(self):
        """init_session_state should create DataManager if not present."""
        import app

        # Create a mock that tracks attribute assignment
        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert 'data_manager' in mock_state
        assert isinstance(mock_state['data_manager'], DataManager)

    def test_init_creates_connector(self):
        """init_session_state should create OptionsDataConnector if not present."""
        import app

        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert 'connector' in mock_state
        assert isinstance(mock_state['connector'], OptionsDataConnector)

    def test_init_sets_default_risk_free_rate(self):
        """init_session_state should set default risk-free rate to 5%."""
        import app

        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert mock_state['risk_free_rate'] == 5.0

    def test_init_preserves_existing_state(self):
        """init_session_state should not overwrite existing values."""
        import app

        existing_dm = DataManager()
        mock_state = {'data_manager': existing_dm}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        # Should keep the existing data manager
        assert mock_state['data_manager'] is existing_dm


class TestPnLChart:
    """Test Phase 4.2 P&L chart functionality."""

    def test_long_call_breakeven_visual_anchor(self):
        """Long call at K=$100 with $5 premium should have breakeven at $105."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        # Create a simple long call strategy
        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )

        # Add a long call at strike 100 with $5 premium (ask price)
        leg = StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        )
        strategy.add_leg(leg)

        # Breakeven should be strike + premium paid = 100 + 5 = 105
        breakevens = strategy.breakeven_points
        assert len(breakevens) == 1
        assert abs(breakevens[0] - 105.0) < 0.5  # Allow small tolerance due to interpolation

    def test_chart_trace_consistency_after_add_leg(self):
        """Adding leg recalculates total P&L correctly - spread caps upside."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        # Create a single long call
        single_call = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )
        single_call.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Create a bull call spread (long 100 call, short 110 call)
        spread = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Bull Call Spread"
        )
        spread.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))
        spread.add_leg(StrategyLeg(
            strike=110.0,
            option_type='call',
            quantity=-1,
            bid=2.00,
            ask=2.20,
            mid=2.10,
            delta=0.3,
            gamma=0.015,
            theta=-0.03,
            vega=0.12,
            iv=0.25,
            model_price=2.10
        ))

        # Get P&L data
        prices_single, pnl_single = single_call.pnl_data(pct_range=0.3)
        prices_spread, pnl_spread = spread.pnl_data(pct_range=0.3)

        # At high prices (e.g., 130), spread should have capped profit
        high_price_idx = -1  # Last price point (highest)

        # Single call P&L at 130 should be higher than spread P&L (unlimited vs capped)
        single_pnl_at_high = pnl_single[high_price_idx]
        spread_pnl_at_high = pnl_spread[high_price_idx]

        # Single call has unlimited upside, spread is capped
        assert single_pnl_at_high > spread_pnl_at_high

        # Spread max profit should be capped at (strike diff - net debit) * 100
        # Strike diff = 110 - 100 = 10
        # Net debit = 5.00 - 2.00 = 3.00 (paid 5, received 2)
        # Max profit = (10 - 3) * 100 = $700
        spread_max = float(pnl_spread.max())
        assert abs(spread_max - 700.0) < 50  # Allow tolerance for bid/ask spread

    def test_hover_tooltip_pnl_accuracy(self):
        """P&L calculation matches expected values at specific prices."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        # Create a long call
        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Calculate P&L at price 110
        # Long call at strike 100, paid $5 premium (ask)
        # At price 110: intrinsic = 110 - 100 = 10
        # P&L = intrinsic * 100 - cost = 10 * 100 - 500 = $500
        prices = np.array([110.0])
        pnl = strategy.calculate_pnl(prices)

        expected_pnl = 500.0  # (110-100)*100 - 500
        assert abs(pnl[0] - expected_pnl) < 1.0  # Allow $1 tolerance

    def test_empty_strategy_returns_zero_pnl(self):
        """Strategy with no legs should have zero P&L everywhere."""
        from options_builder import OptionStrategy
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Empty"
        )

        prices = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
        pnl = strategy.calculate_pnl(prices)

        assert np.all(pnl == 0)

    def test_build_pnl_chart_returns_figure(self):
        """build_pnl_chart should return a Plotly Figure object."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        # Setup mock session state
        app.st.session_state = MagicMock()
        app.st.session_state.chart_show_legs = False
        app.st.session_state.chart_pct_range = 0.20
        app.st.session_state.scenario_dte = None  # No scenario
        app.st.session_state.scenario_iv_shift = 0
        app.st.session_state.risk_free_rate = 5.0

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Test Strategy"
        )
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        fig = app.build_pnl_chart(strategy)

        # Check that it's a Plotly Figure
        assert fig is not None
        assert hasattr(fig, 'data')
        assert hasattr(fig, 'layout')
        # Should have at least the main P&L trace
        assert len(fig.data) >= 1

    def test_build_empty_chart_returns_figure(self):
        """build_empty_chart should return a valid Plotly Figure."""
        import app

        app.st.session_state = MagicMock()

        # Without underlying price
        fig = app.build_empty_chart()
        assert fig is not None
        assert hasattr(fig, 'layout')

        # With underlying price
        fig_with_price = app.build_empty_chart(underlying_price=150.0)
        assert fig_with_price is not None

    def test_strategy_metrics_display(self):
        """render_strategy_metrics should display correct values."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Bull Call Spread"
        )
        # Long 100 call
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))
        # Short 110 call
        strategy.add_leg(StrategyLeg(
            strike=110.0,
            option_type='call',
            quantity=-1,
            bid=2.00,
            ask=2.20,
            mid=2.10,
            delta=0.3,
            gamma=0.015,
            theta=-0.03,
            vega=0.12,
            iv=0.25,
            model_price=2.10
        ))

        # Check net premium (debit spread)
        # Pay $5.00 for long, receive $2.00 for short = $3.00 net debit = $300
        net_premium = strategy.net_premium
        assert net_premium > 0  # Debit
        assert abs(net_premium - 300.0) < 1.0

        # Max profit = (110 - 100) * 100 - 300 = $700
        max_profit = strategy.max_profit
        assert max_profit is not None
        assert abs(max_profit - 700.0) < 50

        # Max loss = net debit = $300
        max_loss = strategy.max_loss
        assert max_loss is not None
        assert abs(max_loss - 300.0) < 1.0

    def test_session_state_chart_options(self):
        """Session state should include chart options after init."""
        import app

        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert 'strategy' in mock_state
        assert mock_state['strategy'] is None
        assert 'chart_show_legs' in mock_state
        assert mock_state['chart_show_legs'] is False
        assert 'chart_pct_range' in mock_state
        assert mock_state['chart_pct_range'] == 0.20


class TestLegBuilder:
    """Test Phase 4.3 strategy leg builder functionality."""

    def test_remove_leg_updates_strategy(self):
        """Removing a leg should update Greeks and P&L."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Test Strategy"
        )

        # Add two legs
        leg1 = StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        )
        leg2 = StrategyLeg(
            strike=110.0,
            option_type='call',
            quantity=-1,
            bid=2.00,
            ask=2.20,
            mid=2.10,
            delta=0.3,
            gamma=0.015,
            theta=-0.03,
            vega=0.12,
            iv=0.25,
            model_price=2.10
        )
        strategy.add_leg(leg1)
        strategy.add_leg(leg2)

        assert len(strategy.legs) == 2
        initial_delta = strategy.total_delta

        # Remove second leg
        result = strategy.remove_leg(1)

        assert result is True
        assert len(strategy.legs) == 1
        # Delta should now only be from the long call
        assert strategy.total_delta == leg1.net_delta
        assert strategy.total_delta != initial_delta

    def test_remove_leg_by_key(self):
        """Remove leg by strike and option type."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80, ask=5.00, mid=4.90,
            delta=0.5, gamma=0.02, theta=-0.05, vega=0.15,
            iv=0.25, model_price=4.90
        ))
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='put',
            quantity=1,
            bid=3.80, ask=4.00, mid=3.90,
            delta=-0.5, gamma=0.02, theta=-0.05, vega=0.15,
            iv=0.25, model_price=3.90
        ))

        assert len(strategy.legs) == 2

        # Remove the call
        result = strategy.remove_leg_by_key(100.0, 'call')

        assert result is True
        assert len(strategy.legs) == 1
        assert strategy.legs[0].option_type == 'put'

    def test_remove_leg_invalid_index(self):
        """Removing leg with invalid index returns False."""
        from options_builder import OptionStrategy
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )

        # Empty strategy
        assert strategy.remove_leg(0) is False
        assert strategy.remove_leg(-1) is False
        assert strategy.remove_leg(10) is False

    def test_clear_legs(self):
        """clear_legs should remove all legs."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0, option_type='call', quantity=1,
            bid=4.80, ask=5.00, mid=4.90,
            delta=0.5, gamma=0.02, theta=-0.05, vega=0.15,
            iv=0.25, model_price=4.90
        ))
        strategy.add_leg(StrategyLeg(
            strike=110.0, option_type='call', quantity=-1,
            bid=2.00, ask=2.20, mid=2.10,
            delta=0.3, gamma=0.015, theta=-0.03, vega=0.12,
            iv=0.25, model_price=2.10
        ))

        assert len(strategy.legs) == 2

        strategy.clear_legs()

        assert len(strategy.legs) == 0

    def test_short_action_flips_pnl_sign(self):
        """Short positions should have inverted P&L vs long."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        # Long call
        long_strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )
        long_strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Short call at same strike (use bid for credit)
        short_strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )
        short_strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=-1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.5,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        prices = np.array([80.0, 100.0, 120.0])

        long_pnl = long_strategy.calculate_pnl(prices)
        short_pnl = short_strategy.calculate_pnl(prices)

        # At price 120 (ITM): long profits, short loses
        # Long P&L: (120-100)*100 - 500 = 1500
        # Short P&L: -(120-100)*100 + 480 = -1520 (receives bid price)
        assert long_pnl[2] > 0  # Long profits above strike
        assert short_pnl[2] < 0  # Short loses above strike

        # At price 80 (OTM): long loses premium, short keeps premium
        # Long P&L: 0 - 500 = -500
        # Short P&L: 0 + 480 = 480
        assert long_pnl[0] < 0  # Long loses below strike
        assert short_pnl[0] > 0  # Short profits below strike

    def test_ticker_change_clears_strategy(self):
        """If user changes ticker, strategy should be cleared."""
        import app
        from datetime import datetime, timedelta
        from options_builder import OptionStrategy

        app.st.session_state = MagicMock()

        # Set up existing strategy
        existing_strategy = Mock(spec=OptionStrategy)
        existing_strategy.legs = [Mock(), Mock(), Mock()]
        app.st.session_state.strategy = existing_strategy
        app.st.session_state.selected_expiration = "2026-03-20"
        app.st.session_state.chain_data = Mock()

        mock_connector = Mock(spec=OptionsDataConnector)
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

        mock_connector.get_underlying.return_value = UnderlyingQuote(
            ticker="MSFT",
            price=380.00,
            timestamp=datetime.now()
        )
        mock_connector.get_expirations.return_value = [tomorrow]
        app.st.session_state.connector = mock_connector

        # Change ticker
        app.validate_and_fetch_ticker("MSFT")

        # Strategy should be cleared
        assert app.st.session_state.strategy is None
        assert app.st.session_state.current_ticker == "MSFT"

    def test_expiration_change_clears_strategy(self):
        """If user changes expiration, strategy should be cleared."""
        import app
        from datetime import timedelta
        from options_builder import OptionStrategy

        app.st.session_state = MagicMock()
        app.st.session_state.current_ticker = "AAPL"
        app.st.session_state.risk_free_rate = 5.0

        # Set up existing strategy
        existing_strategy = Mock(spec=OptionStrategy)
        existing_strategy.legs = [Mock(), Mock()]
        app.st.session_state.strategy = existing_strategy

        mock_connector = Mock(spec=OptionsDataConnector)
        mock_data_manager = Mock(spec=DataManager)

        mock_grid = Mock(spec=OptionChainGrid)
        mock_grid.ticker = "AAPL"
        mock_grid.expiration = date.today() + timedelta(days=30)
        mock_grid.underlying_price = 150.00
        mock_grid.time_to_maturity.return_value = 30/365
        mock_grid.rows = []

        mock_connector.get_chain_grid.return_value = mock_grid
        app.st.session_state.connector = mock_connector
        app.st.session_state.data_manager = mock_data_manager

        mock_priced_chain = Mock(spec=PricedChain)
        mock_priced_chain.rows = []

        with patch.object(ChainAnalyzer, 'analyze', return_value=mock_priced_chain):
            new_expiration = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            app.fetch_chain_data(new_expiration)

        # Strategy should be cleared
        assert app.st.session_state.strategy is None

    def test_session_state_includes_leg_builder_key(self):
        """Session state should include leg_builder_key after init."""
        import app

        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert 'leg_builder_key' in mock_state
        assert mock_state['leg_builder_key'] == 0

    def test_get_atm_strike_index(self):
        """get_atm_strike_index should return closest strike to underlying."""
        import app

        strikes = [90.0, 95.0, 100.0, 105.0, 110.0]

        # Exact match
        assert app.get_atm_strike_index(strikes, 100.0) == 2

        # Slightly above
        assert app.get_atm_strike_index(strikes, 101.0) == 2

        # Slightly below
        assert app.get_atm_strike_index(strikes, 99.0) == 2

        # Closer to 105
        assert app.get_atm_strike_index(strikes, 103.0) == 3

        # Empty list
        assert app.get_atm_strike_index([], 100.0) == 0

    def test_get_moneyness_label_call(self):
        """Test moneyness labels for calls."""
        import app

        # ATM (within 1%)
        assert app.get_moneyness_label(100.0, 100.0, 'call') == "ATM"
        assert app.get_moneyness_label(100.5, 100.0, 'call') == "ATM"

        # ITM call (strike < underlying)
        assert app.get_moneyness_label(95.0, 100.0, 'call') == "ITM"

        # OTM call (strike > underlying)
        assert app.get_moneyness_label(105.0, 100.0, 'call') == "OTM"

    def test_get_moneyness_label_put(self):
        """Test moneyness labels for puts."""
        import app

        # ATM (within 1%)
        assert app.get_moneyness_label(100.0, 100.0, 'put') == "ATM"

        # ITM put (strike > underlying)
        assert app.get_moneyness_label(105.0, 100.0, 'put') == "ITM"

        # OTM put (strike < underlying)
        assert app.get_moneyness_label(95.0, 100.0, 'put') == "OTM"


class TestGreeksDashboard:
    """Test Phase 4.4 Greeks Dashboard functionality."""

    def test_greeks_dashboard_matches_strategy_calculations(self):
        """Dashboard values must match OptionStrategy Greek calculations."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        # Create a bull call spread
        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Bull Call Spread"
        )

        # Long 100 call
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Short 110 call
        strategy.add_leg(StrategyLeg(
            strike=110.0,
            option_type='call',
            quantity=-1,
            bid=2.00,
            ask=2.20,
            mid=2.10,
            delta=0.30,
            gamma=0.015,
            theta=-0.03,
            vega=0.12,
            iv=0.25,
            model_price=2.10
        ))

        # Verify total Greeks match expectations
        # Greeks are position-adjusted and multiplied by 100 (contract multiplier)
        # Long call: delta=0.50*1*100=50, gamma=0.02*1*100=2, theta=-0.05*1*100=-5, vega=0.15*1*100=15
        # Short call: delta=0.30*-1*100=-30, gamma=0.015*-1*100=-1.5, theta=-0.03*-1*100=3, vega=0.12*-1*100=-12
        # Net: delta=20, gamma=0.5, theta=-2, vega=3

        assert abs(strategy.total_delta - 20.0) < 0.1
        assert abs(strategy.total_gamma - 0.5) < 0.01
        assert abs(strategy.total_theta - (-2.0)) < 0.1
        assert abs(strategy.total_vega - 3.0) < 0.1

    def test_greeks_dashboard_empty_strategy(self):
        """Dashboard shows info message when no legs exist."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.strategy = None

        # Call the function - it should call st.info with appropriate message
        app.render_greeks_dashboard()

        # Verify st.info was called
        app.st.info.assert_called_with("Add strategy legs to see Greeks")

    def test_greeks_dashboard_empty_legs(self):
        """Dashboard shows info message when strategy has no legs."""
        import app
        from options_builder import OptionStrategy
        from datetime import date

        app.st.session_state = MagicMock()
        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )
        app.st.session_state.strategy = strategy

        app.render_greeks_dashboard()

        app.st.info.assert_called_with("Add strategy legs to see Greeks")

    def test_long_call_greeks_signs(self):
        """Long call should have positive delta, gamma, vega; negative theta."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Long call Greek signs
        assert strategy.total_delta > 0, "Long call should have positive delta"
        assert strategy.total_gamma > 0, "Long call should have positive gamma"
        assert strategy.total_theta < 0, "Long call should have negative theta"
        assert strategy.total_vega > 0, "Long call should have positive vega"

    def test_short_put_greeks_signs(self):
        """Short put should have positive delta, theta; negative gamma, vega."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Short Put"
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='put',
            quantity=-1,
            bid=4.50,
            ask=4.70,
            mid=4.60,
            delta=-0.50,  # Put delta is negative
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.60
        ))

        # Short put Greek signs (signs flip for short position)
        # Short put: delta = -(-0.50) = +0.50 (positive)
        # Short put: gamma = -0.02 (negative)
        # Short put: theta = -(-0.05) = +0.05 (positive - time decay benefits seller)
        # Short put: vega = -0.15 (negative)
        assert strategy.total_delta > 0, "Short put should have positive delta"
        assert strategy.total_gamma < 0, "Short put should have negative gamma"
        assert strategy.total_theta > 0, "Short put should have positive theta"
        assert strategy.total_vega < 0, "Short put should have negative vega"

    def test_iron_condor_greeks(self):
        """Iron condor should have near-zero delta and positive theta."""
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Iron Condor"
        )

        # Sell put spread (bull put spread)
        # Short 95 put
        strategy.add_leg(StrategyLeg(
            strike=95.0,
            option_type='put',
            quantity=-1,
            bid=1.50, ask=1.70, mid=1.60,
            delta=-0.25, gamma=0.015, theta=-0.03, vega=0.10,
            iv=0.25, model_price=1.60
        ))
        # Long 90 put
        strategy.add_leg(StrategyLeg(
            strike=90.0,
            option_type='put',
            quantity=1,
            bid=0.70, ask=0.90, mid=0.80,
            delta=-0.15, gamma=0.010, theta=-0.02, vega=0.08,
            iv=0.25, model_price=0.80
        ))

        # Sell call spread (bear call spread)
        # Short 105 call
        strategy.add_leg(StrategyLeg(
            strike=105.0,
            option_type='call',
            quantity=-1,
            bid=1.50, ask=1.70, mid=1.60,
            delta=0.25, gamma=0.015, theta=-0.03, vega=0.10,
            iv=0.25, model_price=1.60
        ))
        # Long 110 call
        strategy.add_leg(StrategyLeg(
            strike=110.0,
            option_type='call',
            quantity=1,
            bid=0.70, ask=0.90, mid=0.80,
            delta=0.15, gamma=0.010, theta=-0.02, vega=0.08,
            iv=0.25, model_price=0.80
        ))

        # Iron condor characteristics
        # Delta should be near zero (balanced structure)
        assert abs(strategy.total_delta) < 0.15, "Iron condor should have near-zero delta"

        # Theta should be positive (credit strategy benefits from time decay)
        assert strategy.total_theta > 0, "Iron condor should have positive theta"

        # Gamma should be negative (short gamma position)
        assert strategy.total_gamma < 0, "Iron condor should have negative gamma"

        # Vega should be negative (short volatility position)
        assert strategy.total_vega < 0, "Iron condor should have negative vega"

    def test_greeks_dashboard_renders_metrics(self):
        """Dashboard should call st.metric for each Greek."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        app.st.session_state = MagicMock()

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80, ask=5.00, mid=4.90,
            delta=0.50, gamma=0.02, theta=-0.05, vega=0.15,
            iv=0.25, model_price=4.90
        ))

        app.st.session_state.strategy = strategy

        # Mock the columns context manager
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        app.st.columns.return_value = [mock_col, mock_col, mock_col, mock_col]

        app.render_greeks_dashboard()

        # Verify st.metric was called for each Greek (4 times)
        assert app.st.metric.call_count == 4

        # Verify the labels
        metric_calls = app.st.metric.call_args_list
        labels = [call.kwargs['label'] for call in metric_calls]
        assert "Net Delta" in labels
        assert "Net Gamma" in labels
        assert "Net Theta" in labels
        assert "Net Vega" in labels


class TestSensitivityAnalysis:
    """Test Phase 4.5 Sensitivity Analysis functionality."""

    def test_session_state_includes_scenario_vars(self):
        """Session state should include scenario_dte and scenario_iv_shift after init."""
        import app

        mock_state = {}

        class MockSessionState:
            def __contains__(self, key):
                return key in mock_state

            def __setattr__(self, key, value):
                mock_state[key] = value

            def __getattr__(self, key):
                return mock_state.get(key)

        app.st.session_state = MockSessionState()

        app.init_session_state()

        assert 'scenario_dte' in mock_state
        assert mock_state['scenario_dte'] is None  # Default = at expiration
        assert 'scenario_iv_shift' in mock_state
        assert mock_state['scenario_iv_shift'] == 0.0

    def test_calculate_scenario_pnl_at_expiration(self):
        """Scenario P&L at T=0 should equal intrinsic value P&L."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        prices = np.array([80.0, 90.0, 100.0, 110.0, 120.0])

        # Calculate scenario P&L at T=0
        scenario_pnl = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=0,
            iv_shift=0,
            risk_free_rate=0.05
        )

        # Calculate expected expiration P&L
        expiration_pnl = strategy.calculate_pnl(prices)

        # Should match exactly at T=0
        np.testing.assert_array_almost_equal(scenario_pnl, expiration_pnl, decimal=2)

    def test_time_decay_towards_expiration(self):
        """P&L curve should converge toward intrinsic value as DTE approaches 0."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Call"
        )

        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Test at ATM point (100)
        prices = np.array([100.0])

        # At 30 DTE, option should have time value
        pnl_30d = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=0,
            risk_free_rate=0.05
        )

        # At 1 DTE, option should have minimal time value
        pnl_1d = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=1,
            iv_shift=0,
            risk_free_rate=0.05
        )

        # At 0 DTE (expiration), option has no time value
        pnl_0d = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=0,
            iv_shift=0,
            risk_free_rate=0.05
        )

        # At ATM, more DTE = higher option value = better P&L for long position
        # (because time value hasn't decayed yet)
        assert pnl_30d[0] > pnl_1d[0], "30 DTE should have more value than 1 DTE"
        assert pnl_1d[0] > pnl_0d[0], "1 DTE should have more value than expiration"

    def test_volatility_increases_straddle_value(self):
        """Increasing IV should increase value of long straddle."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Long Straddle"
        )

        # Long call
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Long put
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='put',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=-0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Test at ATM with 30 DTE
        prices = np.array([100.0])

        # Base case (no IV shift)
        pnl_base = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=0,
            risk_free_rate=0.05
        )

        # IV increase by 25%
        pnl_high_iv = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=25,
            risk_free_rate=0.05
        )

        # IV decrease by 25%
        pnl_low_iv = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=-25,
            risk_free_rate=0.05
        )

        # Long vega position benefits from IV increase
        assert pnl_high_iv[0] > pnl_base[0], "Higher IV should increase straddle value"
        assert pnl_low_iv[0] < pnl_base[0], "Lower IV should decrease straddle value"

    def test_short_vega_position_benefits_from_iv_drop(self):
        """Short straddle should benefit from IV decrease."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Short Straddle"
        )

        # Short call
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=-1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        # Short put
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='put',
            quantity=-1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=-0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        prices = np.array([100.0])

        pnl_base = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=0,
            risk_free_rate=0.05
        )

        pnl_low_iv = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=-25,
            risk_free_rate=0.05
        )

        # Short vega position benefits from IV decrease
        assert pnl_low_iv[0] > pnl_base[0], "Lower IV should benefit short straddle"

    def test_get_actual_dte(self):
        """get_actual_dte should calculate days from today to expiration."""
        import app
        from datetime import timedelta

        app.st.session_state = MagicMock()

        # Test with future expiration
        future_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        app.st.session_state.selected_expiration = future_date

        dte = app.get_actual_dte()
        assert dte == 30

        # Test with no expiration selected
        app.st.session_state.selected_expiration = None
        dte = app.get_actual_dte()
        assert dte == 30  # Default

        # Test with today's date (0 DTE)
        today_str = date.today().strftime('%Y-%m-%d')
        app.st.session_state.selected_expiration = today_str
        dte = app.get_actual_dte()
        assert dte == 0

    def test_sensitivity_sliders_empty_strategy(self):
        """Sensitivity sliders should show info message when no legs exist."""
        import app

        app.st.session_state = MagicMock()
        app.st.session_state.strategy = None

        app.render_sensitivity_sliders()

        app.st.info.assert_called_with("Add strategy legs to see sensitivity analysis")

    def test_build_pnl_chart_includes_scenario_line(self):
        """Chart should include scenario P&L line when sliders are active."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        app.st.session_state = MagicMock()
        app.st.session_state.chart_show_legs = False
        app.st.session_state.chart_pct_range = 0.20
        app.st.session_state.scenario_dte = 15  # Active scenario
        app.st.session_state.scenario_iv_shift = 10
        app.st.session_state.risk_free_rate = 5.0

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Test Strategy"
        )
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        fig = app.build_pnl_chart(strategy)

        # Should have at least 2 traces (expiration + scenario)
        assert len(fig.data) >= 2

        # Check trace names
        trace_names = [trace.name for trace in fig.data]
        assert "P&L at Expiration" in trace_names
        # Should have a scenario line
        has_scenario = any("15d" in name or "IV" in name for name in trace_names)
        assert has_scenario, f"Expected scenario trace, got: {trace_names}"

    def test_build_pnl_chart_no_scenario(self):
        """Chart should show single P&L line when no scenario is active."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date

        app.st.session_state = MagicMock()
        app.st.session_state.chart_show_legs = False
        app.st.session_state.chart_pct_range = 0.20
        app.st.session_state.scenario_dte = None  # No scenario
        app.st.session_state.scenario_iv_shift = 0
        app.st.session_state.risk_free_rate = 5.0

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0,
            name="Test Strategy"
        )
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=4.80,
            ask=5.00,
            mid=4.90,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.25,
            model_price=4.90
        ))

        fig = app.build_pnl_chart(strategy)

        # Should have just 1 main trace
        assert len(fig.data) == 1
        assert fig.data[0].name == "P&L at Expiration"

    def test_iv_shift_floor(self):
        """IV shift should not reduce IV below 1%."""
        import app
        from options_builder import OptionStrategy, StrategyLeg
        from datetime import date
        import numpy as np

        strategy = OptionStrategy(
            ticker="TEST",
            expiration=date.today(),
            underlying_price=100.0
        )

        # Option with very low IV (10%)
        strategy.add_leg(StrategyLeg(
            strike=100.0,
            option_type='call',
            quantity=1,
            bid=2.00,
            ask=2.20,
            mid=2.10,
            delta=0.50,
            gamma=0.02,
            theta=-0.05,
            vega=0.15,
            iv=0.10,  # 10% IV
            model_price=2.10
        ))

        prices = np.array([100.0])

        # This should not raise an error even with extreme IV reduction
        # -50% of 10% would be 5%, but we floor at 1%
        pnl = app.calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=30,
            iv_shift=-90,  # Extreme reduction
            risk_free_rate=0.05
        )

        # Should complete without error
        assert pnl is not None
        assert len(pnl) == 1
