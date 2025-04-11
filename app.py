import streamlit as st
import requests
import time
import plotly.graph_objects as go
from datetime import datetime

# Configure settings
API_TIMEOUT = 10
REFRESH_INTERVAL = 10  # Seconds between updates

def is_valid_address(address):
    """Check if address is Ethereum (0x...) or Solana (base58) format"""
    if address.startswith("0x") and len(address) == 42:
        return "ethereum"
    elif len(address) in [43, 44] and address[0].isupper():
        return "solana"
    return False

def get_meme_coin_data(token_address):
    """Fetch data for both Ethereum and Solana tokens"""
    chain = is_valid_address(token_address)
    if not chain:
        return None

    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(url, timeout=API_TIMEOUT)
        
        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get('pairs'):
            return None

        # Find the most liquid pair for the detected chain
        valid_pairs = [p for p in data['pairs'] 
                      if p.get('priceUsd') and p.get('chainId') == chain]
        if not valid_pairs:
            return None

        main_pair = max(valid_pairs, 
                       key=lambda x: float(x.get('volumeUsd', 0)))
        
        return {
            'price': float(main_pair['priceUsd']),
            'pair_address': main_pair['pairAddress'],
            'base_token': main_pair['baseToken']['symbol'],
            'quote_token': main_pair['quoteToken']['symbol'],
            'change_24h': float(main_pair.get('priceChange', {}).get('h24', 0)),
            'chain': chain
        }

    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="MemeSignal", page_icon="🚀", layout="wide")
    
    st.title("📈 Multi-Chain Meme Tracker")
    st.caption("Supports Ethereum (0x...) and Solana addresses")
    
    # Address input with improved validation
    token_address = st.text_input(
        "Enter Token Contract Address",
        value="FasH397CeZLNYWkd3wWK9vrmjd1z93n3b59DssRXpump",  # Example Solana address
        help="Ethereum: 0x... (42 chars) | Solana: Base58 (44 chars)"
    ).strip()

    # Validate address format
    chain_type = is_valid_address(token_address)
    if not chain_type:
        st.error("⚠️ Invalid address format - must be Ethereum (0x...) or Solana (Base58)")
        st.stop()

    # Get current data
    coin_data = get_meme_coin_data(token_address)
    if not coin_data:
        st.error("🚨 Failed to fetch data - check address or try again later")
        st.stop()

    # Display data
    st.success(f"✅ Tracking {coin_data['base_token']} on {coin_data['chain'].capitalize()}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Display metric
        st.metric(
            label="Current Price",
            value=f"${coin_data['price']:.8f}",
            delta=f"{coin_data['change_24h']:.2f}% (24h)"
        )
        
        # Get historical data
        history = get_historical_data(coin_data['pair_address'])
        if history:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[datetime.fromtimestamp(h['timestamp']/1000) for h in history],
                y=[float(h['priceUsd']) for h in history],
                mode='lines',
                line=dict(color='#00FF00' if coin_data['price'] > 0 else 'red'),
                name='Price'
            ))
            fig.update_layout(
                title=f"{coin_data['base_token']} Price History",
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write(f"**Chain:** {coin_data['chain'].capitalize()}")
        st.write(f"**Trading Pair:** {coin_data['base_token']}/{coin_data['quote_token']}")
        st.write(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

    # Auto-refresh logic
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

if __name__ == "__main__":
    main()
