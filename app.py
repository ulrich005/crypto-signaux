import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime

st.set_page_config(page_title="📈 Crypto Signal App", layout="wide")

# --- Fonction de chargement des données ---
def load_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date)
    if 'Close' not in df.columns or df.empty:
        raise ValueError("Données introuvables ou colonne 'Close' absente.")
    df = df[['Close']].copy()
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df.dropna(inplace=True)
    return df

# --- Fonction de calcul des indicateurs techniques ---
def compute_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
    macd = ta.trend.MACD(close=df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator()
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['pct_change_3d'] = df['Close'].pct_change(periods=3) * 100
    df.dropna(inplace=True)
    return df

# --- Fonction de génération des signaux ---
def get_smart_signal(row):
    if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
        return 'Buy'
    elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
        return 'Sell'
    return 'Hold'

# Liste des cryptos
crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

# --- Sidebar ---
st.sidebar.title("🛠 Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])
actualiser = st.sidebar.button("🔄 Actualiser les signaux")

# --- Corps principal ---
if actualiser:
    try:
        df = load_data(ticker, start_date, end_date)
        df = compute_indicators(df)

        df['signal'] = df.apply(get_smart_signal, axis=1)
        df['signal_time'] = df.index.strftime("%Y-%m-%d %H:%M")

        df_valid = df.dropna(subset=['ema_12', 'ema_26', 'rsi', 'macd', 'macd_signal'])
        alert_log = df_valid[df_valid['signal'].isin(['Buy', 'Sell'])][['signal', 'signal_time', 'Close']]

        st.title(f"📊 Signaux sur {crypto_name}")
        if signal_filter != "Tous":
            df = df[df['signal'] == signal_filter]

        st.subheader("📋 Aperçu des derniers signaux")
        st.dataframe(df[['Close', 'rsi', 'macd', 'macd_signal', 'ema_12', 'ema_26', 'signal', 'signal_time']].tail(10))

        # --- Graphique principal ---
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df.index, df['Close'], label='Clôture', color='blue')
        ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--', color='orange')
        ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--', color='red')
        ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':', color='gray')
        ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':', color='gray')
        ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
        ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
        ax.set_title(f"Graphique avec indicateurs – {crypto_name}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Prix ($)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # --- Historique des alertes ---
        st.subheader("🕒 Historique des alertes Buy/Sell")
        st.dataframe(alert_log.tail(20))

        # --- Téléchargement CSV ---
        csv = df.to_csv().encode('utf-8')
        st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse : {str(e)}")





