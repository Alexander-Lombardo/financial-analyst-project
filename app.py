"""Options Trading Dashboard - Streamlit Application."""

import streamlit as st
from datetime import date, datetime

from options_builder import (
    DataManager,
    OptionsDataConnector,
    ChainAnalyzer,
)


def init_session_state() -> None:
    """Initialize session state with defaults."""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    if 'connector' not in st.session_state:
        st.session_state.connector = OptionsDataConnector()
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = None
    if 'underlying_price' not in st.session_state:
        st.session_state.underlying_price = None
    if 'expirations' not in st.session_state:
        st.session_state.expirations = []
    if 'selected_expiration' not in st.session_state:
        st.session_state.selected_expiration = None
    if 'risk_free_rate' not in st.session_state:
        st.session_state.risk_free_rate = 5.0
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'chain_data' not in st.session_state:
        st.session_state.chain_data = None


def validate_and_fetch_ticker(ticker: str) -> bool:
    """
    Validate ticker and fetch underlying price and expirations.

    Args:
        ticker: Stock ticker symbol

    Returns:
        True if ticker is valid and data was fetched successfully
    """
    if not ticker or not ticker.strip():
        st.session_state.error_message = "Please enter a ticker symbol"
        return False

    ticker = ticker.strip().upper()
    connector = st.session_state.connector

    try:
        # Fetch underlying price
        quote = connector.get_underlying(ticker)
        st.session_state.underlying_price = quote.price

        # Fetch expiration dates
        expirations = connector.get_expirations(ticker)

        # Filter to future dates only
        today = date.today()
        future_expirations = [
            exp for exp in expirations
            if datetime.strptime(exp, '%Y-%m-%d').date() >= today
        ]

        if not future_expirations:
            st.session_state.error_message = f"No future expiration dates available for {ticker}"
            return False

        st.session_state.expirations = future_expirations
        st.session_state.current_ticker = ticker
        st.session_state.error_message = None
        st.session_state.selected_expiration = None
        st.session_state.chain_data = None

        return True

    except ValueError as e:
        st.session_state.error_message = str(e)
        st.session_state.current_ticker = None
        st.session_state.underlying_price = None
        st.session_state.expirations = []
        st.session_state.selected_expiration = None
        st.session_state.chain_data = None
        return False
    except Exception:
        st.session_state.error_message = "Unable to fetch data. Please try again."
        st.session_state.current_ticker = None
        st.session_state.underlying_price = None
        st.session_state.expirations = []
        st.session_state.selected_expiration = None
        st.session_state.chain_data = None
        return False


def fetch_chain_data(expiration: str) -> bool:
    """
    Fetch and analyze option chain for selected expiration.

    Args:
        expiration: Expiration date string (YYYY-MM-DD)

    Returns:
        True if chain was fetched and analyzed successfully
    """
    ticker = st.session_state.current_ticker
    if not ticker:
        return False

    connector = st.session_state.connector
    data_manager = st.session_state.data_manager
    risk_free_rate = st.session_state.risk_free_rate / 100  # Convert from percentage

    try:
        # Fetch the chain grid
        grid = connector.get_chain_grid(ticker, expiration)

        # Analyze with Greeks and IV
        analyzer = ChainAnalyzer(risk_free_rate=risk_free_rate)
        priced_chain = analyzer.analyze(grid)

        # Store in data manager
        data_manager.add_chain(priced_chain)

        st.session_state.chain_data = priced_chain
        st.session_state.selected_expiration = expiration
        st.session_state.error_message = None

        return True

    except ValueError as e:
        st.session_state.error_message = str(e)
        return False
    except Exception:
        st.session_state.error_message = "Unable to fetch option chain. Please try again."
        return False


def format_expiration_option(exp_str: str) -> str:
    """Format expiration date with days to expiration."""
    exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
    days = (exp_date - date.today()).days
    return f"{exp_str} ({days}d)"


def render_sidebar() -> None:
    """Render sidebar with global inputs."""
    st.sidebar.header("Options Parameters")

    # Ticker input
    ticker_input = st.sidebar.text_input(
        "Ticker Symbol",
        value=st.session_state.current_ticker or "",
        placeholder="e.g., AAPL",
        key="ticker_input"
    )

    # Fetch button for ticker
    if st.sidebar.button("Fetch Data", key="fetch_btn"):
        validate_and_fetch_ticker(ticker_input)

    # Display error if present
    if st.session_state.error_message:
        st.sidebar.error(st.session_state.error_message)

    st.sidebar.divider()

    # Risk-free rate section
    st.sidebar.subheader("Risk-Free Rate")

    use_auto_rate = st.sidebar.checkbox(
        "Fetch T-bill rate automatically",
        value=False,
        key="auto_rate"
    )

    if use_auto_rate:
        try:
            auto_rate = st.session_state.connector.get_risk_free_rate() * 100
            st.session_state.risk_free_rate = auto_rate
            st.sidebar.info(f"Current T-bill rate: {auto_rate:.2f}%")
        except Exception:
            st.sidebar.warning("Could not fetch T-bill rate. Using manual input.")
            use_auto_rate = False

    if not use_auto_rate:
        risk_free_rate = st.sidebar.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=st.session_state.risk_free_rate,
            step=0.25,
            key="risk_free_input"
        )
        st.session_state.risk_free_rate = risk_free_rate

    st.sidebar.divider()

    # Expiration date selector
    st.sidebar.subheader("Expiration Date")

    if st.session_state.expirations:
        # Format options with days to expiration
        exp_options = st.session_state.expirations
        formatted_options = [format_expiration_option(exp) for exp in exp_options]

        # Find current selection index
        current_idx = 0
        if st.session_state.selected_expiration:
            try:
                current_idx = exp_options.index(st.session_state.selected_expiration)
            except ValueError:
                current_idx = 0

        selected_formatted = st.sidebar.selectbox(
            "Select Expiration",
            options=formatted_options,
            index=current_idx,
            key="expiration_select"
        )

        # Extract the date part (remove the days suffix)
        if selected_formatted:
            selected_exp = selected_formatted.split(" (")[0]

            # Fetch chain if expiration changed
            if selected_exp != st.session_state.selected_expiration:
                fetch_chain_data(selected_exp)
    else:
        st.sidebar.info("Enter a ticker and click 'Fetch Data' to see expirations")


def render_header() -> None:
    """Render main header with current parameters."""
    st.title("Options Trading Dashboard")

    if st.session_state.current_ticker:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Ticker",
                value=st.session_state.current_ticker
            )

        with col2:
            price = st.session_state.underlying_price
            st.metric(
                label="Underlying Price",
                value=f"${price:.2f}" if price else "N/A"
            )

        with col3:
            exp = st.session_state.selected_expiration
            if exp:
                exp_date = datetime.strptime(exp, '%Y-%m-%d').date()
                days = (exp_date - date.today()).days
                st.metric(
                    label="Expiration",
                    value=exp,
                    delta=f"{days}d to exp"
                )
            else:
                st.metric(label="Expiration", value="Not Selected")

        with col4:
            st.metric(
                label="Risk-Free Rate",
                value=f"{st.session_state.risk_free_rate:.2f}%"
            )
    else:
        st.info("Enter a ticker symbol in the sidebar to get started")


def render_debug_section() -> None:
    """Render debug expander showing chain data (placeholder for Phase 4.2)."""
    if st.session_state.chain_data:
        with st.expander("Debug: Chain Data", expanded=False):
            chain = st.session_state.chain_data

            st.write(f"**Ticker:** {chain.ticker}")
            st.write(f"**Expiration:** {chain.expiration}")
            st.write(f"**Underlying Price:** ${chain.underlying_price:.2f}")
            st.write(f"**Time to Maturity:** {chain.time_to_maturity:.4f} years")
            st.write(f"**Risk-Free Rate:** {chain.risk_free_rate:.4f}")
            st.write(f"**Number of Strikes:** {len(chain.rows)}")

            # Show sample data
            st.write("---")
            st.write("**Sample Options (ATM area):**")

            atm_strike = chain.atm_strike()
            strikes = chain.strikes()
            atm_idx = strikes.index(atm_strike)

            # Show 3 strikes around ATM
            start_idx = max(0, atm_idx - 1)
            end_idx = min(len(strikes), atm_idx + 2)

            for i in range(start_idx, end_idx):
                row = chain.rows[i]
                st.write(f"**Strike ${row.strike:.2f}**")

                if row.call:
                    st.write(f"  Call: IV={row.call.implied_volatility:.2%}, "
                            f"Delta={row.call.delta:.3f}, Mid=${row.call.mid_price:.2f}")

                if row.put:
                    st.write(f"  Put: IV={row.put.implied_volatility:.2%}, "
                            f"Delta={row.put.delta:.3f}, Mid=${row.put.mid_price:.2f}")


def render_placeholders() -> None:
    """Render placeholder sections for future phases."""
    st.divider()

    # Phase 4.2 placeholder
    st.subheader("P&L Chart")
    st.info("Phase 4.2: Plotly P&L chart will be added here")

    # Phase 4.3 placeholder
    st.subheader("Strategy Builder")
    st.info("Phase 4.3: Strategy leg builder will be added here")

    # Phase 4.4 placeholder
    st.subheader("Greeks Dashboard")
    st.info("Phase 4.4: Greek metrics dashboard will be added here")

    # Phase 4.5 placeholder
    st.subheader("Sensitivity Analysis")
    st.info("Phase 4.5: DTE and IV sliders for sensitivity analysis will be added here")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Options Trading Dashboard",
        page_icon="📈",
        layout="wide"
    )

    # Initialize session state
    init_session_state()

    # Render components
    render_sidebar()
    render_header()
    render_debug_section()
    render_placeholders()


if __name__ == "__main__":
    main()
