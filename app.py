import streamlit as st
import requests
import time
import plotly.graph_objects as go
from datetime import datetime

# Configure settings
API_TIMEOUT = 10
REFRESH_INTERVAL = 10  # Seconds between updates

def get_meme_coin_data(token_address):
    """Fetch current price and pair data with error handling"""
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
            timeout=API_TIMEOUT
        )
        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get('pairs'):
            return None

        # Find the most liquid pair
        valid_pairs = [p for p in data['pairs'] if p.get('priceUsd')]
        if not valid_pairs:
            return None

        main_pair = max(valid_pairs, key=lambda x: float(x.get('volumeUsd', 0)))
        
        return {
            'price': float(main_pair['priceUsd']),
            'pair_address': main_pair['pairAddress'],
            'base_token': main_pair['baseToken']['symbol'],
            'quote_token': main_pair['quoteToken']['symbol'],
            'change_24h': float(main_pair.get('priceChange', {}).get('h24', 0))
        }

    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def get_historical_data(pair_address):
    """Fetch price history for charts"""
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/pairs/{pair_address}",
            timeout=API_TIMEOUT
        )
        data = response.json()
        return data.get('pair', {}).get('priceHistory', [])
    except:
        return None

def main():
    st.set_page_config(page_title="MemeSignal", page_icon="🚀", layout="wide")
    
    st.title("📈 MemeSignal Price Tracker")
    st.caption("Live price charts for any meme coin")
    
    # Address input with validation
    token_address = st.text_input(
        "Enter Token Contract Address (0x...)",
        value="0xdAC17F958D2ee523a2206206994597C13D831ec7",  # Example address
        help="Must be a valid Ethereum contract address starting with 0x"
    ).strip()

    # Validate address format
    if not token_address.startswith("0x") or len(token_address) != 42:
        st.error("⚠️ Invalid contract address format")
        st.stop()

    # Get current data
    coin_data = get_meme_coin_data(token_address)
    if not coin_data:
        st.error("Failed to fetch coin data - check address or try again later")
        st.stop()

    # Get historical data
    history = get_historical_data(coin_data['pair_address'])
    if not history:
        st.warning("Could not load price history")
        st.stop()

    # Process historical data for plotting
    times = [datetime.fromtimestamp(h['timestamp']/1000) for h in history]
    prices = [float(h['priceUsd']) for h in history]

    # Create Plotly chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=prices,
        mode='lines',
        line=dict(color='#00FF00', width=2),
        name='Price'
    ))
    
    fig.update_layout(
        title=f"{coin_data['base_token']} Price History",
        xaxis_title='Date/Time',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        hovermode="x unified"
    )

    # Display metrics and chart
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric(
            label="Current Price",
            value=f"${coin_data['price']:.8f}",
            delta=f"{coin_data['change_24h']:.2f}% (24h)"
        )
        st.write(f"**Pair:** {coin_data['base_token']}/{coin_data['quote_token']}")
        st.write(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

    # Auto-refresh logic
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

if __name__ == "__main__":
    main()
