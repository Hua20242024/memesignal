import streamlit as st
import requests
import time
import os
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# Configure audio (same as before)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
    pygame.mixer.init()
    AUDIO_ENABLED = True
except:
    AUDIO_ENABLED = False

def generate_beep():
    sample_rate = 44100
    duration = 0.3
    freq = 880    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    return np.int16(wave * 32767)

def play_alert_sound():
    if AUDIO_ENABLED:
        try:
            beep_sound = pygame.mixer.Sound(buffer=generate_beep())
            beep_sound.play()
        except:
            st.toast("🔔 Price Alert!", icon="⚠️")
    else:
        st.toast("🔔 Price Alert!", icon="⚠️")

# Add cached data fetcher with 5-second refresh
@st.cache_data(ttl=5)  # Auto-refresh every 5 seconds
def get_cached_coin_data(token_address):
    return get_meme_coin_data(token_address)

@st.cache_data(ttl=30)  # Refresh historical data every 30 seconds
def get_cached_history(pair_address):
    return get_historical_data(pair_address)

# Keep existing get_meme_coin_data and get_historical_data functions

def main():
    st.set_page_config(page_title="MemeSignal", page_icon="🚀", layout="wide")
    
    st.title("📈 MemeSignal Alert System")
    st.caption("Real-time updates every 5 seconds")
    
    # Input section
    token_address = st.text_input(
        "Token Contract Address",
        value="FasH397CeZLNYWkd3wWK9vrmjd1z93n3b59DssRXpump",
        help="Paste the full contract address from DexScreener"
    )
    
    if token_address:
        # Get fresh data using cached function
        coin_data = get_cached_coin_data(token_address)
        
        if coin_data:
            # Display auto-updating price
            current_price = coin_data['price']
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                st.metric(
                    label=f"Current {coin_data['base_token']} Price",
                    value=f"${current_price:.8f}",
                    delta=f"{coin_data['change_24h']:.2f}% (24h)"
                )
            with col3:
                st.caption(f"Last update: {timestamp}")
            
            # Auto-updating chart
            history = get_cached_history(coin_data['pair_address'])
            if history:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[datetime.fromtimestamp(h['timestamp']/1000) for h in history],
                    y=[float(h['priceUsd']) for h in history],
                    mode='lines',
                    line=dict(color='#00ff88', width=2),
                    name='Price'
                ))
                fig.update_layout(
                    title=f"{coin_data['base_token']} Price History",
                    xaxis_title='Time',
                    yaxis_title='Price (USD)',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Alert system
            with st.expander("⚡ Active Alerts", expanded=True):
                alert_price = st.number_input(
                    "Alert Price (USD)",
                    min_value=0.00000001,
                    value=current_price * 1.1,
                    format="%.8f",
                    key="alert_price"
                )
                alert_condition = st.radio(
                    "Trigger when:",
                    ("Price Goes Above", "Price Goes Below"),
                    horizontal=True,
                    key="alert_condition"
                )
                
                if st.button("💥 Activate Alert"):
                    st.session_state['alert'] = {
                        'price': alert_price,
                        'condition': alert_condition,
                        'token': coin_data['base_token'],
                        'active': True
                    }
                
                if 'alert' in st.session_state:
                    st.success(f"Active alert for {st.session_state['alert']['token']}")
                    condition_met = (
                        (st.session_state['alert']['condition'] == "Price Goes Above" 
                         and current_price > st.session_state['alert']['price']) or
                        (st.session_state['alert']['condition'] == "Price Goes Below" 
                         and current_price < st.session_state['alert']['price'])
                    )
                    
                    if condition_met:
                        play_alert_sound()
                        st.error(f"🚨 ALERT TRIGGERED AT ${current_price:.8f}")
                        st.session_state.pop('alert')
            
            # Force refresh every 5 seconds
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    main()
