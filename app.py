import streamlit as st
import requests
import time
import plotly.graph_objects as go
from datetime import datetime
import base58  # ✅ Added for better Solana validation
import io

# Configure settings
API_TIMEOUT = 10
REFRESH_INTERVAL = 10  # Seconds between updates

def is_valid_address(address):
    """Detect Ethereum or Solana address format"""
    if address.startswith("0x") and len(address) == 42:
        return "ethereum"
    try:
        decoded = base58.b58decode(address)
        if 32 <= len(decoded) <= 64:
            return "solana"
    except Exception:
        pass
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

    # ✅ Sidebar alert settings with decimal support
    st.sidebar.subheader("📣 Price Alert Settings")
    upper_limit = st.sidebar.number_input(
        "Alert if price goes ABOVE", value=0.0, step=0.000001, format="%.6f"
    )
    lower_limit = st.sidebar.number_input(
        "Alert if price goes BELOW", value=0.0, step=0.000001, format="%.6f"
    )

    # Token input
    token_address = st.text_input(
        "Enter Token Contract Address",
        value="FasH397CeZLNYWkd3wWK9vrmjd1z93n3b59DssRXpump",
        help="Ethereum: 0x... (42 chars) | Solana: Base58 (44 chars)"
    ).strip()

    chain_type = is_valid_address(token_address)
    if not chain_type:
        st.error("⚠️ Invalid address format - must be Ethereum (0x...) or Solana (Base58)")
        st.stop()

    coin_data = get_meme_coin_data(token_address)
    if not coin_data:
        st.error("🚨 Failed to fetch data - check address or try again later")
        st.stop()

    st.success(f"✅ Tracking {coin_data['base_token']} on {coin_data['chain'].capitalize()}")

    # ✅ Alert logic
    trigger_alert = False
    alert_message = ""

    if upper_limit > 0 and coin_data['price'] > upper_limit:
        trigger_alert = True
        alert_message = f"🚨 Price went ABOVE ${upper_limit}"
    elif lower_limit > 0 and coin_data['price'] < lower_limit:
        trigger_alert = True
        alert_message = f"🚨 Price dropped BELOW ${lower_limit}"

    # ✅ Show alert
    if trigger_alert:
        st.error(alert_message)

        # ✅ Bell sound (Autoplay)
        try:
            bell_sound_url = "https://www.soundjay.com/button/beep-05.wav"  # Bell sound URL
            sound_response = requests.get(bell_sound_url)
            
            if sound_response.status_code == 200:
                # Embed audio into the page with autoplay using HTML
                sound_bytes = io.BytesIO(sound_response.content)
                sound_base64 = base64.b64encode(sound_bytes.getvalue()).decode('utf-8')
                sound_html = f'''
                    <audio autoplay>
                        <source src="data:audio/wav;base64,{sound_base64}" type="audio/wav">
                    </audio>
                '''
                st.markdown(sound_html, unsafe_allow_html=True)
            else:
                st.warning("🔇 Unable to fetch bell sound.")
        except Exception as e:
            st.warning(f"🔇 Sound alert failed: {str(e)}")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(
            label="Current Price",
            value=f"${coin_data['price']:.8f}",
            delta=f"{coin_data['change_24h']:.2f}% (24h)"
        )
    with col2:
        st.write(f"**Chain:** {coin_data['chain'].capitalize()}")
        st.write(f"**Trading Pair:** {coin_data['base_token']}/{coin_data['quote_token']}")
        st.write(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

    # Refresh loop
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

if __name__ == "__main__":
    main()
