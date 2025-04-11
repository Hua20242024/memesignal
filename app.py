import streamlit as st
import requests
import time
import os
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# Configure audio
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
AUDIO_ENABLED = False  # Temporarily disable audio for debugging
# try:
#     import pygame
#     pygame.mixer.init()
#     AUDIO_ENABLED = True
# except:
#     AUDIO_ENABLED = False

def get_meme_coin_data(token_address):
    """Fetch coin data with better error handling"""
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
            timeout=10
        )
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data.get('pairs'):
            return None

        # Find the pair with highest liquidity
        valid_pairs = [p for p in data['pairs'] if p.get('priceUsd')]
        if not valid_pairs:
            return None

        main_pair = max(valid_pairs, 
                       key=lambda x: float(x.get('volumeUsd', 0)))
        
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

@st.cache_data(ttl=10)  # 10-second cache
def safe_get_coin_data(token_address):
    """Wrapper with validation"""
    if not token_address.startswith("0x"):
        return None
    return get_meme_coin_data(token_address)

def main():
    st.set_page_config(page_title="MemeSignal", page_icon="🚀", layout="wide")
    
    st.title("📈 MemeSignal Alert System")
    st.caption("Real-time updates every 10 seconds")

    # Input with validation
    token_address = st.text_input(
        "Token Contract Address (0x...)",
        value="0xdAC17F958D2ee523a2206206994597C13D831ec7",  # Example: USDT
        help="Must start with 0x and be 42 characters long"
    ).strip()

    if len(token_address) != 42 or not token_address.startswith("0x"):
        st.error("❌ Invalid contract address format")
        return

    # Get data with loading state
    with st.spinner("Fetching latest data..."):
        coin_data = safe_get_coin_data(token_address)
    
    if not coin_data:
        st.error("Failed to fetch data - check contract address or try again later")
        return

    # Display section
    current_price = coin_data['price']
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(
            label=f"Current {coin_data['base_token']} Price",
            value=f"${current_price:.8f}",
            delta=f"{coin_data['change_24h']:.2f}% (24h)"
        )
    with col2:
        st.caption(f"Last update: {timestamp}")

    # Auto-refresh logic
    refresh_time = st.slider("Refresh interval (seconds)", 10, 60, 30)
    time.sleep(refresh_time)
    st.rerun()

if __name__ == "__main__":
    main()
