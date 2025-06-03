import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Crypto Signal App", layout="wide")

crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

@st.cache_data
def load_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date)
    if 'Close' not in df.columns:
        raise ValueError("Colonne 'Close' manquante.")
    
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()
    
    close = pd.to_numeric(close, errors='coerce')
    df = pd.DataFrame({'Close': close})
    df.dropna(inplace=True)

    if df.empty:
        raise ValueError("Données de clôture indisponibles ou invalides.")
    
    return df

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
    macd = ta.trend.MACD(close=df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator()
    df.dropna(inplace=True)
    return df

def get_smart_signal(row):
    try:
        if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
            return 'Buy'
        elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
            return 'Sell'
        else:
            return 'Hold'
    except:
        return 'Hold'

st.sidebar.title("Paramètres")
crypto_name = st.sidebar.selectbox("Crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime.now())
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

st.title(f"📈 {crypto_name} - Signaux de Trading")

try:
    df = load_data(ticker, start_date, end_date)
    df = calculate_indicators(df)
    df['signal'] = df.apply(get_smart_signal, axis=1)
    df['timestamp'] = df.index.strftime('%Y-%m-%d %H:%M:%S')

    if signal_filter != "Tous":
        df = df[df['signal'] == signal_filter]

    st.subheader("📋 Derniers signaux")
    st.dataframe(df[['timestamp', 'Close', 'rsi', 'macd', 'ema_12', 'ema_26', 'signal']].tail(20))

    st.subheader("📊 Graphique des signaux")
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Close', color='blue')
    ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--')
    ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--')
    ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', color='green', marker='^', s=100)
    ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', color='red', marker='v', s=100)
    ax.set_title("Historique des signaux")
    ax.legend()
    st.pyplot(fig)

    st.subheader("📥 Exporter")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Télécharger les données CSV", csv, f"{ticker}_signals.csv", "text/csv")

except Exception as e:
    st.error(f"❌ Erreur lors de l'analyse : {str(e)}")






