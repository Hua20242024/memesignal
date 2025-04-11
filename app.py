import streamlit as st
import requests
import time
import os
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# Initialize audio system safely
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
    pygame.mixer.init()
    AUDIO_ENABLED = True
except:
    AUDIO_ENABLED = False

def generate_beep():
    """Generate a beep sound programmatically"""
    sample_rate = 44100
    duration = 0.3
    freq = 880
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    audio = np.int16(wave * 32767)
    return audio

def play_alert_sound():
    """Play sound or fallback to visual alert"""
    if AUDIO_ENABLED:
        try:
            beep_sound = pygame.mixer.Sound(buffer=generate_beep())
            beep_sound.play()
        except:
            show_visual_alert()
    else:
        show_visual_alert()

def show_visual_alert():
    """Fallback visual notification"""
    st.toast("🚨 PRICE ALERT!", icon="⚠️")
    st.balloons()

def get_meme_coin_data(token_address):
    """Fetch current price data from DexScreener"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if 'pairs' in data and len(data['pairs']) > 0:
            main_pair = sorted(data['pairs'], 
                             key=lambda x: float(x.get('volumeUsd', 0)), 
                             reverse=True)[0]
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
    url = f"https://api.dexscreener.com/latest/dex/pairs/{pair_address}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get('pair', {}).get('priceHistory', [])[:200]  # Last 200 points
    except:
        return []

def main():
    st.set_page_config(page_title="MemeSignal", page_icon="🚀", layout="wide")
    
    st.title("📈 MemeSignal Alert System")
    st.caption("Get real-time alerts for your favorite meme coins")
    
    with st.expander("⚙️ Setup Alert", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            token_address = st.text_input(
                "Token Contract Address",
                placeholder="0x...",
                help="Paste the full contract address from DexScreener"
            )
        with col2:
            if token_address:
                if st.button("🔍 Verify Token"):
                    with st.spinner("Checking token..."):
                        coin_data = get_meme_coin_data(token_address)
                        if coin_data:
                            st.success(f"Tracking: {coin_data['base_token']}")
    
    if 'token_address' in locals() and token_address:
        coin_data = get_meme_coin_data(token_address)
        if coin_data:
            # Price display
            current_price = coin_data['price']
            st.metric(
                label=f"Current {coin_data['base_token']} Price",
                value=f"${current_price:.8f}",
                delta=f"{coin_data['change_24h']:.2f}% (24h)"
            )
            
            # Chart
            history = get_historical_data(coin_data['pair_address'])
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
            
            # Alert configuration
            with st.form("alert_form"):
                col1, col2 = st.columns(2)
                with col1:
                    alert_price = st.number_input(
                        "Alert Price (USD)",
                        min_value=0.00000001,
                        value=current_price * 1.1,
                        format="%.8f"
                    )
                with col2:
                    alert_condition = st.radio(
                        "Trigger when:",
                        ("Price Goes Above", "Price Goes Below"),
                        horizontal=True
                    )
                
                if st.form_submit_button("💾 Save Alert", use_container_width=True):
                    st.session_state['alert'] = {
                        'price': alert_price,
                        'condition': alert_condition,
                        'token': coin_data['base_token'],
                        'active': True
                    }
                    st.success(f"Alert set for {coin_data['base_token']}!")
            
            # Monitoring loop
            if 'alert' in st.session_state:
                st.info(f"Monitoring: {st.session_state['alert']['token']} "
                       f"({st.session_state['alert']['condition']} "
                       f"${st.session_state['alert']['price']:.8f})")
                
                if st.button("🛑 Stop Monitoring"):
                    st.session_state.pop('alert')
                    st.rerun()
                
                # Check price condition
                current_price = coin_data['price']
                alert = st.session_state['alert']
                
                condition_met = (
                    (alert['condition'] == "Price Goes Above" and current_price > alert['price']) or
                    (alert['condition'] == "Price Goes Below" and current_price < alert['price'])
                )
                
                if condition_met:
                    play_alert_sound()
                    st.error(f"🚨 ALERT! {alert['token']} is now at ${current_price:.8f}")
                    st.session_state.pop('alert')
                    st.rerun()

if __name__ == "__main__":
    main()
