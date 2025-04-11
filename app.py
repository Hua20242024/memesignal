import streamlit as st
import requests
import time
import pygame
import plotly.graph_objects as go
from datetime import datetime

# Initialize pygame for audio
pygame.mixer.init()

def get_meme_coin_data(token_address):
    """Fetch current price and pair data from DexScreener API"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'pairs' in data and len(data['pairs']) > 0:
            # Get the most liquid pair (highest volume)
            main_pair = sorted(data['pairs'], key=lambda x: float(x.get('volumeUsd', 0)), reverse=True)[0]
            return {
                'price': float(main_pair['priceUsd']),
                'pair_address': main_pair['pairAddress'],
                'base_token': main_pair['baseToken']['symbol'],
                'quote_token': main_pair['quoteToken']['symbol']
            }
        return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_historical_data(pair_address):
    """Fetch historical price data for chart"""
    url = f"https://api.dexscreener.com/latest/dex/pairs/{pair_address}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'pair' in data:
            # Extract price history (simplified - actual implementation may need to handle API limits)
            return [
                {'time': entry['timestamp'], 'price': float(entry['priceUsd'])}
                for entry in data['pair'].get('priceHistory', [])
            ]
        return []
    except:
        return []

def play_alert_sound():
    """Play alert sound when threshold is crossed"""
    try:
        sound = pygame.mixer.Sound("alert.wav")
        sound.play()
    except:
        st.warning("Couldn't play alert sound")

def main():
    st.title("🚀 Meme Coin Price Alert with Chart")
    st.markdown("Monitor meme coins with price charts and audio alerts")

    # Inputs
    token_address = st.text_input("Enter Token Contract Address", "0x...")
    
    if token_address and len(token_address) > 10:
        coin_data = get_meme_coin_data(token_address)
        
        if coin_data:
            st.success(f"Tracking: {coin_data['base_token']}/{coin_data['quote_token']}")
            
            # Display price chart
            historical_data = get_historical_data(coin_data['pair_address'])
            if historical_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[datetime.fromtimestamp(d['time']/1000) for d in historical_data],
                    y=[d['price'] for d in historical_data],
                    mode='lines',
                    name='Price'
                ))
                fig.update_layout(
                    title=f"{coin_data['base_token']} Price History",
                    xaxis_title='Time',
                    yaxis_title=f"Price ({coin_data['quote_token']})",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Couldn't load historical price data")

            # Alert configuration
            with st.expander("Set Price Alert"):
                threshold_price = st.number_input("Alert Price", 
                    min_value=0.0, 
                    step=0.000001, 
                    format="%f",
                    value=coin_data['price'] * 1.1  # Default 10% above current
                )
                alert_type = st.radio("Alert When:", ("Price Goes Above", "Price Goes Below"))
                check_interval = st.slider("Check Interval (seconds)", 10, 300, 60)
                
                if st.button("Start Monitoring"):
                    alert_active = True
                    st.session_state['monitoring'] = True
                    status_placeholder = st.empty()
                    
                    while st.session_state.get('monitoring', False):
                        current_data = get_meme_coin_data(token_address)
                        if current_data:
                            current_price = current_data['price']
                            status_placeholder.markdown(f"""
                            **Current Price:** ${current_price:.10g}  
                            **Alert Price:** ${threshold_price:.10g}  
                            **Last Check:** {datetime.now().strftime('%H:%M:%S')}
                            """)
                            
                            # Check alert condition
                            if (alert_type == "Price Goes Above" and current_price > threshold_price) or \
                               (alert_type == "Price Goes Below" and current_price < threshold_price):
                                play_alert_sound()
                                st.balloons()
                                st.success(f"ALERT! {current_data['base_token']} crossed your threshold at ${current_price:.10g}")
                                st.session_state['monitoring'] = False
                                break
                        
                        time.sleep(check_interval)

            if st.button("Stop Monitoring"):
                st.session_state['monitoring'] = False
                st.warning("Monitoring stopped")

if __name__ == "__main__":
    main()