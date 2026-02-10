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
    black_scholes,
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
    if 'leg_builder_key' not in st.session_state:
        st.session_state.leg_builder_key = 0
    if 'scenario_dte' not in st.session_state:
        st.session_state.scenario_dte = None  # None = at expiration
    if 'scenario_iv_shift' not in st.session_state:
        st.session_state.scenario_iv_shift = 0.0  # Percentage shift (-50 to +50)


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
        st.session_state.strategy = None  # Clear strategy on ticker change

        return True

    except ValueError as e:
        st.session_state.error_message = str(e)
        st.session_state.current_ticker = None
        st.session_state.underlying_price = None
        st.session_state.expirations = []
        st.session_state.selected_expiration = None
        st.session_state.chain_data = None
        st.session_state.strategy = None
        return False
    except Exception:
        st.session_state.error_message = "Unable to fetch data. Please try again."
        st.session_state.current_ticker = None
        st.session_state.underlying_price = None
        st.session_state.expirations = []
        st.session_state.selected_expiration = None
        st.session_state.chain_data = None
        st.session_state.strategy = None
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
        st.session_state.strategy = None  # Clear strategy on expiration change

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

    Includes scenario P&L line when DTE or IV shift is active.

    Args:
        strategy: OptionStrategy with legs

    Returns:
        Plotly Figure object
    """
    pct_range = st.session_state.chart_pct_range
    prices, pnl = strategy.pnl_data(pct_range=pct_range, num_points=200)

    # Get scenario parameters
    scenario_dte = st.session_state.scenario_dte
    iv_shift = st.session_state.scenario_iv_shift
    risk_free_rate = st.session_state.risk_free_rate / 100.0

    # Determine if we need to show scenario line
    show_scenario = scenario_dte is not None or iv_shift != 0

    fig = go.Figure()

    # Expiration P&L line (always shown, but styled differently if scenario is active)
    if show_scenario:
        # Lighter style for expiration line when scenario is active
        fig.add_trace(go.Scatter(
            x=prices,
            y=pnl,
            mode='lines',
            name='P&L at Expiration',
            line=dict(color='#1f77b4', width=1, dash='dot'),
            hovertemplate='Expiration<br>Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>'
        ))

        # Scenario P&L line (primary)
        dte_for_calc = scenario_dte if scenario_dte is not None else 0
        scenario_pnl = calculate_scenario_pnl(
            strategy=strategy,
            prices=prices,
            dte=dte_for_calc,
            iv_shift=iv_shift,
            risk_free_rate=risk_free_rate
        )

        # Build scenario label
        scenario_parts = []
        if scenario_dte is not None:
            scenario_parts.append(f"{scenario_dte}d")
        if iv_shift != 0:
            scenario_parts.append(f"IV {iv_shift:+d}%")
        scenario_label = f"P&L ({', '.join(scenario_parts)})" if scenario_parts else "P&L (Scenario)"

        fig.add_trace(go.Scatter(
            x=prices,
            y=scenario_pnl,
            mode='lines',
            name=scenario_label,
            line=dict(color='#e377c2', width=2),
            fill='tozeroy',
            fillcolor='rgba(227, 119, 194, 0.2)',
            hovertemplate=f'{scenario_label}<br>Price: $%{{x:.2f}}<br>P&L: $%{{y:.2f}}<extra></extra>'
        ))
    else:
        # Standard expiration P&L (no scenario active)
        fig.add_trace(go.Scatter(
            x=prices,
            y=pnl,
            mode='lines',
            name='P&L at Expiration',
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

    # Build title
    if show_scenario:
        title_parts = [strategy.name or 'Strategy', 'P&L']
        if scenario_dte is not None:
            title_parts.append(f"at {scenario_dte}d DTE")
        if iv_shift != 0:
            title_parts.append(f"IV {iv_shift:+d}%")
        title = ' '.join(title_parts)
    else:
        title = f"{strategy.name or 'Strategy'} P&L at Expiration"

    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Stock Price ($)",
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


def render_greeks_dashboard() -> None:
    """Render the Greeks dashboard with net Greek values."""
    st.subheader("Greeks Dashboard")

    strategy = st.session_state.strategy

    if not strategy or len(strategy.legs) == 0:
        st.info("Add strategy legs to see Greeks")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta = strategy.total_delta
        st.metric(
            label="Net Delta",
            value=f"{delta:+.2f}",
            delta="per 100 shares" if delta != 0 else None,
            delta_color="normal" if delta >= 0 else "inverse"
        )

    with col2:
        gamma = strategy.total_gamma
        st.metric(
            label="Net Gamma",
            value=f"{gamma:+.4f}",
            delta="per $1 move" if gamma != 0 else None,
            delta_color="normal" if gamma >= 0 else "inverse"
        )

    with col3:
        theta = strategy.total_theta
        st.metric(
            label="Net Theta",
            value=f"{theta:+.2f}",
            delta="per day" if theta != 0 else None,
            delta_color="inverse" if theta >= 0 else "normal"  # Positive theta is good (seller)
        )

    with col4:
        vega = strategy.total_vega
        st.metric(
            label="Net Vega",
            value=f"{vega:+.2f}",
            delta="per 1% IV" if vega != 0 else None,
            delta_color="normal" if vega >= 0 else "inverse"
        )


def calculate_scenario_pnl(
    strategy: OptionStrategy,
    prices: 'np.ndarray',
    dte: int,
    iv_shift: float,
    risk_free_rate: float
) -> 'np.ndarray':
    """
    Calculate P&L at a specific DTE and IV scenario using Black-Scholes.

    Args:
        strategy: OptionStrategy with legs
        prices: Array of underlying prices
        dte: Days to expiration for scenario
        iv_shift: Percentage shift to IV (-50 to +50)
        risk_free_rate: Risk-free rate as decimal

    Returns:
        Array of P&L values at each price point
    """
    import numpy as np

    # Convert DTE to years
    T = dte / 365.0

    total_pnl = np.zeros_like(prices, dtype=float)

    for leg in strategy.legs:
        # Adjust IV by shift percentage
        adjusted_iv = leg.iv * (1 + iv_shift / 100.0)
        adjusted_iv = max(0.01, adjusted_iv)  # Floor at 1% to avoid errors

        if T == 0:
            # At expiration - use intrinsic value
            if leg.option_type == 'call':
                option_values = np.maximum(prices - leg.strike, 0)
            else:
                option_values = np.maximum(leg.strike - prices, 0)
        else:
            # Use BSM for mid-life valuation
            option_values = np.zeros_like(prices, dtype=float)
            for i, S in enumerate(prices):
                try:
                    call_price, put_price = black_scholes(
                        S=S,
                        K=leg.strike,
                        T=T,
                        r=risk_free_rate,
                        sigma=adjusted_iv
                    )
                    if leg.option_type == 'call':
                        option_values[i] = call_price
                    else:
                        option_values[i] = put_price
                except ValueError:
                    # Handle edge cases
                    if leg.option_type == 'call':
                        option_values[i] = max(S - leg.strike, 0)
                    else:
                        option_values[i] = max(leg.strike - S, 0)

        # P&L = (current value * quantity * 100) - entry cost
        leg_pnl = option_values * leg.quantity * 100 - leg.cost
        total_pnl += leg_pnl

    return total_pnl


def get_actual_dte() -> int:
    """Get actual days to expiration from selected expiration."""
    exp = st.session_state.selected_expiration
    if not exp:
        return 30  # Default

    exp_date = datetime.strptime(exp, '%Y-%m-%d').date()
    return max(0, (exp_date - date.today()).days)


def render_sensitivity_sliders() -> None:
    """Render DTE and IV sensitivity sliders."""
    st.subheader("Sensitivity Analysis")

    strategy = st.session_state.strategy
    if not strategy or len(strategy.legs) == 0:
        st.info("Add strategy legs to see sensitivity analysis")
        return

    actual_dte = get_actual_dte()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Days to Expiration**")

        # Toggle for at-expiration vs custom DTE
        use_expiration = st.checkbox(
            "Show at expiration",
            value=st.session_state.scenario_dte is None,
            key="scenario_at_expiration"
        )

        if use_expiration:
            st.session_state.scenario_dte = None
            st.caption(f"Showing P&L at expiration (T=0)")
        else:
            # DTE slider
            dte = st.slider(
                "DTE",
                min_value=0,
                max_value=max(actual_dte, 1),
                value=st.session_state.scenario_dte if st.session_state.scenario_dte is not None else actual_dte,
                key="dte_slider"
            )
            st.session_state.scenario_dte = dte
            st.caption(f"Showing P&L with {dte} days remaining")

    with col2:
        st.write("**Implied Volatility Shift**")

        iv_shift = st.slider(
            "IV Shift (%)",
            min_value=-50,
            max_value=50,
            value=int(st.session_state.scenario_iv_shift),
            step=5,
            key="iv_shift_slider",
            help="Shift all leg IVs by this percentage"
        )
        st.session_state.scenario_iv_shift = float(iv_shift)

        if iv_shift == 0:
            st.caption("Using current IV levels")
        elif iv_shift > 0:
            st.caption(f"IV increased by {iv_shift}%")
        else:
            st.caption(f"IV decreased by {abs(iv_shift)}%")


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


def get_atm_strike_index(strikes: list[float], underlying_price: float) -> int:
    """Find index of ATM strike (closest to underlying price)."""
    if not strikes:
        return 0
    min_diff = float('inf')
    atm_idx = 0
    for i, strike in enumerate(strikes):
        diff = abs(strike - underlying_price)
        if diff < min_diff:
            min_diff = diff
            atm_idx = i
    return atm_idx


def get_moneyness_label(strike: float, underlying_price: float, option_type: str) -> str:
    """Get moneyness indicator (ITM/ATM/OTM) for a strike."""
    diff = abs(strike - underlying_price)
    threshold = underlying_price * 0.01  # 1% threshold for ATM

    if diff < threshold:
        return "ATM"

    if option_type == 'call':
        return "ITM" if strike < underlying_price else "OTM"
    else:  # put
        return "ITM" if strike > underlying_price else "OTM"


def add_leg_to_strategy(strike: float, option_type: str, action: str, quantity: int) -> bool:
    """
    Add a leg to the current strategy.

    If strategy doesn't exist, creates one first.
    If duplicate leg exists (same strike/type), updates quantity instead.

    Args:
        strike: Strike price
        option_type: 'call' or 'put'
        action: 'Buy' or 'Sell'
        quantity: Number of contracts (always positive)

    Returns:
        True if leg was added/updated successfully
    """
    chain_data = st.session_state.chain_data
    data_manager = st.session_state.data_manager

    if not chain_data:
        return False

    # Convert action to signed quantity
    signed_quantity = quantity if action == "Buy" else -quantity

    # Create strategy if needed
    if st.session_state.strategy is None:
        st.session_state.strategy = OptionStrategy(
            ticker=chain_data.ticker,
            expiration=chain_data.expiration,
            underlying_price=chain_data.underlying_price,
            name="Custom Strategy"
        )

    strategy = st.session_state.strategy

    # Check for duplicate leg (same strike and type)
    existing_leg = strategy.get_leg(strike, option_type.lower())
    if existing_leg:
        # Sum quantities - if opposite signs cancel out, remove the leg
        new_quantity = existing_leg.quantity + signed_quantity
        if new_quantity == 0:
            # Cancel out - remove the leg
            strategy.remove_leg_by_key(strike, option_type.lower())
        else:
            # Update by removing old and adding new with combined quantity
            strategy.remove_leg_by_key(strike, option_type.lower())
            return strategy.add_leg_from_lookup(
                dm=data_manager,
                strike=strike,
                option_type=option_type.lower(),
                quantity=new_quantity
            )
        return True

    # Add new leg
    return strategy.add_leg_from_lookup(
        dm=data_manager,
        strike=strike,
        option_type=option_type.lower(),
        quantity=signed_quantity
    )


def remove_leg_from_strategy(index: int) -> bool:
    """
    Remove a leg from the strategy by index.

    Args:
        index: Index of leg to remove

    Returns:
        True if leg was removed
    """
    strategy = st.session_state.strategy
    if strategy is None:
        return False

    result = strategy.remove_leg(index)

    # Clear strategy if no legs remain
    if len(strategy.legs) == 0:
        st.session_state.strategy = None

    return result


def clear_strategy() -> None:
    """Remove all legs and reset strategy."""
    st.session_state.strategy = None
    st.session_state.leg_builder_key += 1  # Force widget refresh


def render_leg_row(index: int, leg: StrategyLeg) -> None:
    """
    Render a single leg display row with remove button.

    Args:
        index: Leg index in strategy
        leg: StrategyLeg to display
    """
    col1, col2, col3 = st.columns([4, 2, 1])

    direction = "Long" if leg.quantity > 0 else "Short"
    qty = abs(leg.quantity)
    cost = leg.cost
    cost_label = "debit" if cost > 0 else "credit"

    with col1:
        st.write(f"**{index + 1}.** {direction} {qty}x ${leg.strike:.0f} {leg.option_type.title()}")

    with col2:
        st.write(f"${abs(cost):.2f} {cost_label}")

    with col3:
        if st.button("Remove", key=f"remove_leg_{index}_{st.session_state.leg_builder_key}"):
            remove_leg_from_strategy(index)
            st.rerun()


def render_leg_builder() -> None:
    """Render the strategy leg builder UI."""
    st.subheader("Strategy Builder")

    chain_data = st.session_state.chain_data
    data_manager = st.session_state.data_manager
    underlying_price = st.session_state.underlying_price

    # Check if we have the required data
    if not chain_data:
        st.info("Select an expiration date to build a strategy")
        return

    # Get available strikes
    strikes = data_manager.get_strikes(chain_data.ticker, chain_data.expiration)
    if not strikes:
        st.warning("No strikes available for selected expiration")
        return

    # Add new leg section
    st.write("**Add New Leg:**")

    col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 1])

    with col1:
        # Strike selectbox with moneyness indicators
        atm_idx = get_atm_strike_index(strikes, underlying_price)

        # Default to Call for moneyness calculation
        strike_options = [
            f"${s:.0f} ({get_moneyness_label(s, underlying_price, 'call')})"
            for s in strikes
        ]

        selected_strike_option = st.selectbox(
            "Strike",
            options=strike_options,
            index=atm_idx,
            key=f"leg_strike_{st.session_state.leg_builder_key}"
        )
        # Extract strike value from the formatted string
        selected_strike = strikes[strike_options.index(selected_strike_option)]

    with col2:
        option_type = st.radio(
            "Type",
            options=["Call", "Put"],
            horizontal=True,
            key=f"leg_type_{st.session_state.leg_builder_key}"
        )

    with col3:
        action = st.radio(
            "Action",
            options=["Buy", "Sell"],
            horizontal=True,
            key=f"leg_action_{st.session_state.leg_builder_key}"
        )

    with col4:
        quantity = st.number_input(
            "Qty",
            min_value=1,
            max_value=100,
            value=1,
            key=f"leg_qty_{st.session_state.leg_builder_key}"
        )

    with col5:
        st.write("")  # Spacer for alignment
        st.write("")
        if st.button("Add", key=f"add_leg_{st.session_state.leg_builder_key}"):
            if add_leg_to_strategy(selected_strike, option_type, action, quantity):
                st.rerun()
            else:
                st.error("Could not add leg. Please try again.")

    st.divider()

    # Current legs section
    strategy = st.session_state.strategy

    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.write("**Current Legs:**")
    with header_col2:
        if strategy and len(strategy.legs) > 0:
            if st.button("Clear All", key=f"clear_all_{st.session_state.leg_builder_key}"):
                clear_strategy()
                st.rerun()

    if strategy and len(strategy.legs) > 0:
        for i, leg in enumerate(strategy.legs):
            render_leg_row(i, leg)

        st.divider()

        # Net cost summary
        premium = strategy.net_premium
        if premium > 0:
            st.write(f"**Net: ${premium:.2f} Debit**")
        elif premium < 0:
            st.write(f"**Net: ${abs(premium):.2f} Credit**")
        else:
            st.write("**Net: $0.00**")
    else:
        st.info("No legs added yet")


def render_placeholders() -> None:
    """Render placeholder sections for future phases."""
    st.divider()

    # Phase 4.3 - Strategy Leg Builder
    render_leg_builder()

    st.divider()

    # Phase 4.2 - P&L Chart (implemented)
    render_pnl_chart()

    st.divider()

    # Phase 4.4 - Greeks Dashboard (implemented)
    render_greeks_dashboard()

    st.divider()

    # Phase 4.5 - Sensitivity Analysis (implemented)
    render_sensitivity_sliders()


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
