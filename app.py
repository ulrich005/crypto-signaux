import streamlit as st

# Dictionnaire complet des 20 cryptos
crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Tether (USDT)': 'USDT-USD',
    'BNB': 'BNB-USD',
    'Solana (SOL)': 'SOL-USD',
    'XRP': 'XRP-USD',
    'USDC': 'USDC-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD',
    'Avalanche (AVAX)': 'AVAX-USD',
    'Shiba Inu (SHIB)': 'SHIB-USD',
    'Polkadot (DOT)': 'DOT-USD',
    'TRON (TRX)': 'TRX-USD',
    'Toncoin (TON)': 'TON11419-USD',
    'Chainlink (LINK)': 'LINK-USD',
    'Polygon (MATIC)': 'MATIC-USD',
    'Litecoin (LTC)': 'LTC-USD',
    'Uniswap (UNI)': 'UNI7083-USD',
    'Internet Computer (ICP)': 'ICP-USD',
    'Stellar (XLM)': 'XLM-USD'
}

# Test d'affichage
st.title("Test du menu déroulant")
crypto_name = st.selectbox("Choisir une crypto", list(crypto_options.keys()))
st.write(f"Vous avez choisi : {crypto_name} → Ticker : {crypto_options[crypto_name]}")

