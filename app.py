import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime

st.set_page_config(page_title="Crypto Signal App", layout="wide")

# --- Sélection des cryptos ---
crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

# --- Barre latérale ---
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# --- Lancement de l’analyse ---
if st.sidebar.button("🔄 Actualiser les signaux"):
    df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
    if df.empty:
        st.error("Aucune donnée disponible pour cette période.")
        st.stop()

    # Calcul des indicateurs techniques
    close_series = pd.Series(df['Close'].values.flatten(), index=df.index)
    df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
    df['macd'] = ta.trend.MACD(close=close_series).macd()
    df['macd_signal'] = ta.trend.MACD(close=close_series).macd_signal()
    df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=close_series, window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=close_series, window=26).ema_indicator()

    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mavg'] = bb.bollinger_mavg()
    df['pct_change_3d'] = df['Close'].pct_change(periods=3) * 100
    df.dropna(inplace=True)

    # --- Génération des signaux automatiques ---
    def get_smart_signal(row):
        if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
            return 'Buy'
        elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
            return 'Sell'
        return 'Hold'

    df['signal'] = df.apply(get_smart_signal, axis=1)

    # --- Historique des alertes ---
    alert_history = df[df['signal'].isin(['Buy', 'Sell'])].copy()
    alert_history = alert_history.reset_index()
    alert_history = alert_history.rename(columns={
        'Date': 'Horodatage',
        'Close': 'Prix (USD)',
        'signal': 'Signal'
    })
    alert_history['Crypto'] = crypto_name

    # --- Interface principale ---
    st.title(f"📊 {crypto_name} – Analyse technique & Signaux de trading")

    st.subheader("📋 Données techniques récentes")
    df_display = df if signal_filter == "Tous" else df[df['signal'] == signal_filter]
    st.dataframe(df_display[['Close', 'rsi', 'macd', 'macd_signal', 'sma', 'ema_12', 'ema_26', 'bb_upper', 'bb_lower', 'pct_change_3d', 'signal']].tail(15))

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Prix clôture', color='blue')
    ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--', color='orange')
    ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--', color='red')
    ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':', color='gray')
    ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':', color='gray')
    ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
    ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
    ax.set_title(f"📈 Graphique – {crypto_name}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix ($)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # --- Historique des signaux ---
    st.subheader("📚 Historique des alertes Buy/Sell")
    st.dataframe(alert_history[['Date', 'Prix (USD)', 'Signal', 'Crypto']].tail(20))

    # --- Export CSV ---
    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Télécharger les données complètes", csv, f"{ticker}_signaux.csv", "text/csv")


