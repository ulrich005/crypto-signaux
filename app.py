import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime

# Configuration Streamlit
st.set_page_config(page_title="Crypto Signal App", layout="wide")

# Liste des 20 cryptos populaires
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

# Sidebar inputs
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# Actualisation sur bouton
if st.sidebar.button("🔄 Actualiser les signaux"):
    df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
    if df.empty:
        st.error("Aucune donnée disponible pour cette période.")
        st.stop()

    close_series = pd.Series(df['Close'].values.flatten(), index=df.index)

    df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
    df['macd'] = ta.trend.MACD(close=close_series).macd()
    df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=close_series, window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=close_series, window=26).ema_indicator()

    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mavg'] = bb.bollinger_mavg()
    df.dropna(inplace=True)

    df['signal'] = 'Hold'
    for i in range(2, len(df)):
        if close_series.iloc[i] > close_series.iloc[i-1] and close_series.iloc[i-1] > close_series.iloc[i-2]:
            df.iloc[i, df.columns.get_loc('signal')] = 'Buy'
        elif close_series.iloc[i] < close_series.iloc[i-1] and close_series.iloc[i-1] < close_series.iloc[i-2]:
            df.iloc[i, df.columns.get_loc('signal')] = 'Sell'

    if signal_filter != "Tous":
        df = df[df['signal'] == signal_filter]

    def decision(row):
        if row['rsi'] < 30 and row['macd'] > 0 and row['ema_12'] > row['ema_26']:
            return "BUY"
        elif row['rsi'] > 70 and row['macd'] < 0 and row['ema_12'] < row['ema_26']:
            return "SELL"
        else:
            return "HOLD"

    signal = decision({
        'rsi': float(df['rsi'].iloc[-1]),
        'macd': float(df['macd'].iloc[-1]),
        'ema_12': float(df['ema_12'].iloc[-1]),
        'ema_26': float(df['ema_26'].iloc[-1])
    })

    st.title(f"📊 Recommandation de trading pour {crypto_name}")
    if signal == "BUY":
        st.success(f"📈 Signal actuel : {signal} – Conditions favorables à l'achat.")
    elif signal == "SELL":
        st.error(f"📉 Signal actuel : {signal} – Risque élevé, possible retournement.")
    else:
        st.warning(f"⏸ Signal actuel : {signal} – Attendre confirmation.")

    st.subheader("📋 Données techniques récentes")
    st.dataframe(df[['Close', 'rsi', 'macd', 'sma', 'ema_12', 'ema_26', 'bb_upper', 'bb_lower', 'signal']].tail(10))

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Clôture', color='blue')
    ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--', color='orange')
    ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--', color='red')
    ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':', color='gray')
    ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':', color='gray')
    ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
    ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
    ax.set_title(f"Graphique avec indicateurs pour {ticker}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix ($)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Télécharger CSV", csv, f"{ticker}_signaux.csv", "text/csv")
