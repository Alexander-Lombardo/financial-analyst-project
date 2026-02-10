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
