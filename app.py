"""Options Trading Dashboard - Streamlit Application."""

import streamlit as st
import plotly.graph_objects as go
from datetime import date, datetime
from typing import Optional

from options_builder import (
    DataManager,
    OptionsDataConnector,
    ChainAnalyzer,
    OptionStrategy,
    StrategyLeg,
    bull_call_spread,
    payoff,
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
    if 'strategy' not in st.session_state:
        st.session_state.strategy = None
    if 'chart_show_legs' not in st.session_state:
        st.session_state.chart_show_legs = False
    if 'chart_pct_range' not in st.session_state:
        st.session_state.chart_pct_range = 0.20


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
    """Render debug expander showing chain data and demo strategy loader."""
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

            # Demo strategy loader
            st.write("---")
            st.write("**Demo Strategy:**")
            if st.button("Load Demo Strategy", key="load_demo_btn"):
                if load_demo_strategy():
                    st.success("Loaded ATM Bull Call Spread")
                    st.rerun()
                else:
                    st.error("Could not create demo strategy")

            # Show current strategy info
            if st.session_state.strategy:
                strategy = st.session_state.strategy
                st.write(f"Current: {strategy.name} ({len(strategy.legs)} legs)")
                if st.button("Clear Strategy", key="clear_strategy_btn"):
                    st.session_state.strategy = None
                    st.rerun()


def build_pnl_chart(strategy: OptionStrategy) -> go.Figure:
    """
    Create Plotly figure with P&L curve, breakeven lines, and annotations.

    Args:
        strategy: OptionStrategy with legs

    Returns:
        Plotly Figure object
    """
    pct_range = st.session_state.chart_pct_range
    prices, pnl = strategy.pnl_data(pct_range=pct_range, num_points=200)

    fig = go.Figure()

    # Total P&L line with fill to zero
    fig.add_trace(go.Scatter(
        x=prices,
        y=pnl,
        mode='lines',
        name='Total P&L',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)',
        hovertemplate='Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>'
    ))

    # Individual leg traces (optional)
    if st.session_state.chart_show_legs:
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for i, leg in enumerate(strategy.legs):
            leg_prices, leg_pnl = _calculate_leg_pnl(leg, prices)
            direction = "Long" if leg.quantity > 0 else "Short"
            leg_name = f"{direction} {leg.option_type.title()} ${leg.strike:.0f}"
            fig.add_trace(go.Scatter(
                x=leg_prices,
                y=leg_pnl,
                mode='lines',
                name=leg_name,
                line=dict(color=colors[i % len(colors)], width=1, dash='dash'),
                hovertemplate=f'{leg_name}<br>Price: $%{{x:.2f}}<br>P&L: $%{{y:.2f}}<extra></extra>'
            ))

    # Horizontal line at y=0 (breakeven reference)
    fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)

    # Vertical line at current underlying price
    fig.add_vline(
        x=strategy.underlying_price,
        line_dash="dot",
        line_color="orange",
        line_width=2,
        annotation_text=f"Current: ${strategy.underlying_price:.2f}",
        annotation_position="top"
    )

    # Breakeven points marked with vertical dashed green lines
    for be in strategy.breakeven_points:
        fig.add_vline(
            x=be,
            line_dash="dash",
            line_color="green",
            line_width=1,
            annotation_text=f"BE: ${be:.2f}",
            annotation_position="bottom"
        )

    # Layout
    fig.update_layout(
        title=f"{strategy.name or 'Strategy'} P&L at Expiration",
        xaxis_title="Stock Price at Expiration ($)",
        yaxis_title="Profit/Loss ($)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        height=400
    )

    return fig


def _calculate_leg_pnl(leg: StrategyLeg, prices) -> tuple:
    """Calculate P&L for a single leg across price range."""
    import numpy as np
    intrinsic = payoff(prices, leg.strike, leg.option_type)
    leg_pnl = intrinsic * leg.quantity * 100 - leg.cost
    return prices, leg_pnl


def build_empty_chart(underlying_price: Optional[float] = None) -> go.Figure:
    """
    Placeholder chart when no legs exist.

    Args:
        underlying_price: Current underlying price (optional)

    Returns:
        Plotly Figure with placeholder message
    """
    fig = go.Figure()

    # Add a horizontal line at zero
    fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)

    # Add current price line if available
    if underlying_price:
        fig.add_vline(
            x=underlying_price,
            line_dash="dot",
            line_color="orange",
            line_width=2,
            annotation_text=f"Current: ${underlying_price:.2f}",
            annotation_position="top"
        )
        # Set reasonable x-axis range
        low = underlying_price * 0.8
        high = underlying_price * 1.2
        fig.update_xaxes(range=[low, high])

    fig.update_layout(
        title="P&L at Expiration",
        xaxis_title="Stock Price at Expiration ($)",
        yaxis_title="Profit/Loss ($)",
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
        annotations=[
            dict(
                text="Add strategy legs to see P&L chart",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
        ]
    )

    return fig


def render_strategy_metrics(strategy: OptionStrategy) -> None:
    """
    Display net premium, max profit/loss, breakevens below chart.

    Args:
        strategy: OptionStrategy with calculated metrics
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        premium = strategy.net_premium
        premium_label = "Net Debit" if premium > 0 else "Net Credit"
        st.metric(
            label=premium_label,
            value=f"${abs(premium):,.2f}"
        )

    with col2:
        max_profit = strategy.max_profit
        if max_profit is None:
            st.metric(label="Max Profit", value="Unlimited")
        else:
            st.metric(label="Max Profit", value=f"${max_profit:,.2f}")

    with col3:
        max_loss = strategy.max_loss
        if max_loss is None:
            st.metric(label="Max Loss", value="Unlimited")
        else:
            st.metric(label="Max Loss", value=f"${max_loss:,.2f}")

    with col4:
        breakevens = strategy.breakeven_points
        if breakevens:
            be_str = ", ".join(f"${be:.2f}" for be in breakevens)
            st.metric(label="Breakeven(s)", value=be_str)
        else:
            st.metric(label="Breakeven(s)", value="N/A")


def render_pnl_chart() -> None:
    """Main render function for P&L chart with options expander."""
    st.subheader("P&L Chart")

    strategy = st.session_state.strategy

    # Chart options expander
    with st.expander("Chart Options", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            show_legs = st.checkbox(
                "Show individual leg traces",
                value=st.session_state.chart_show_legs,
                key="chart_show_legs_input"
            )
            st.session_state.chart_show_legs = show_legs

        with col2:
            pct_options = {
                "10%": 0.10,
                "20%": 0.20,
                "30%": 0.30,
                "40%": 0.40,
                "50%": 0.50
            }
            current_pct = st.session_state.chart_pct_range
            # Find current selection
            current_label = "20%"
            for label, val in pct_options.items():
                if abs(val - current_pct) < 0.001:
                    current_label = label
                    break

            selected_range = st.selectbox(
                "Price range",
                options=list(pct_options.keys()),
                index=list(pct_options.keys()).index(current_label),
                key="chart_pct_range_input"
            )
            st.session_state.chart_pct_range = pct_options[selected_range]

    # Build and display chart
    if strategy and len(strategy.legs) > 0:
        fig = build_pnl_chart(strategy)
        st.plotly_chart(fig, use_container_width=True)
        render_strategy_metrics(strategy)
    else:
        underlying_price = st.session_state.underlying_price
        fig = build_empty_chart(underlying_price)
        st.plotly_chart(fig, use_container_width=True)
        st.info("Add strategy legs to see P&L calculations")


def load_demo_strategy() -> bool:
    """
    Create a sample bull call spread for testing.

    Creates an ATM bull call spread using current chain data.

    Returns:
        True if demo strategy was created successfully
    """
    chain_data = st.session_state.chain_data
    data_manager = st.session_state.data_manager

    if not chain_data:
        return False

    ticker = chain_data.ticker
    expiration = chain_data.expiration
    atm_strike = chain_data.atm_strike()
    strikes = chain_data.strikes()

    # Find strikes for bull call spread (ATM and one strike above)
    try:
        atm_idx = strikes.index(atm_strike)
        if atm_idx + 1 >= len(strikes):
            return False
        upper_strike = strikes[atm_idx + 1]
    except (ValueError, IndexError):
        return False

    # Create bull call spread
    strategy = bull_call_spread(
        dm=data_manager,
        ticker=ticker,
        expiration=expiration,
        lower_strike=atm_strike,
        upper_strike=upper_strike,
        quantity=1
    )

    if strategy:
        st.session_state.strategy = strategy
        return True
    return False


def render_placeholders() -> None:
    """Render placeholder sections for future phases."""
    st.divider()

    # Phase 4.2 - P&L Chart (implemented)
    render_pnl_chart()

    st.divider()

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
