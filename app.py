import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime

# =================== CONFIGURATION ===================
st.set_page_config(page_title="📈 Crypto Signal App", layout="wide")

crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

# =================== FONCTION DE TÉLÉCHARGEMENT ===================
def load_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date)
    if 'Close' not in df.columns or df['Close'].isnull().all():
        raise ValueError("Données 'Close' non disponibles.")
    close = df['Close'].astype(float)
    df = pd.DataFrame({'Close': close})
    df.dropna(inplace=True)
    return df

# =================== DÉTECTION DES SIGNAUX ===================
def detect_signals(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
    macd_obj = ta.trend.MACD(close=df['Close'])
    df['macd'] = macd_obj.macd()
    df['macd_signal'] = macd_obj.macd_signal()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator()

    df.dropna(inplace=True)

    def smart_signal(row):
        if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
            return 'Buy'
        elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
            return 'Sell'
        else:
            return 'Hold'

    df['signal'] = df.apply(smart_signal, axis=1)
    return df

# =================== UI ===================
st.sidebar.header("🔧 Paramètres")
crypto_name = st.sidebar.selectbox("Cryptomonnaie", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])
actualiser = st.sidebar.button("🔄 Actualiser les signaux")

if actualiser:
    try:
        df = load_data(ticker, start_date, end_date)
        df = detect_signals(df)

        # Historique
        st.title(f"📊 {crypto_name} – Analyse & Signaux")
        df_filtered = df if signal_filter == "Tous" else df[df['signal'] == signal_filter]

        st.subheader("📝 Données récentes")
        st.dataframe(df_filtered[['Close', 'rsi', 'macd', 'macd_signal', 'ema_12', 'ema_26', 'signal']].tail(20))

        # Graphique
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df.index, df['Close'], label='Prix clôture', color='blue')
        ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--')
        ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--')
        ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
        ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
        ax.legend()
        ax.set_title(f"Graphique des signaux – {crypto_name}")
        st.pyplot(fig)

        # Historique de signaux
        st.subheader("📌 Historique des alertes")
        alerts = df[df['signal'].isin(['Buy', 'Sell'])][['Close', 'signal']]
        alerts['Heure'] = alerts.index.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(alerts[['Heure', 'Close', 'signal']].sort_index(ascending=False))

        # Export CSV
        csv = df.to_csv().encode('utf-8')
        st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Erreur lors de l’analyse : {e}")





