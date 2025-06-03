import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from io import StringIO

# Config
st.set_page_config(page_title="Crypto Signal App", layout="wide")

# Liste des cryptos disponibles
crypto_options = {
    'Bitcoin': 'BTC-USD',
    'Ethereum': 'ETH-USD',
    'Solana': 'SOL-USD',
    'Cardano': 'ADA-USD',
    'Dogecoin': 'DOGE-USD',
    'XRP': 'XRP-USD'
}

# Sidebar : sélection
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", pd.to_datetime("2025-01-01"))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# Télécharger les données
df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
if df.empty:
    st.error("Aucune donnée disponible pour cette période.")
    st.stop()

# Calculs
df[['Close']].squeeze()
df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
df['macd'] = ta.trend.MACD(close=close_series).macd()
df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
df.dropna(inplace=True)

# Signaux
df['signal'] = 'Hold'
for i in range(2, len(df)):
    if df['Close'].iloc[i] > df['Close'].iloc[i-1] > df['Close'].iloc[i-2]:
        df.iloc[i, df.columns.get_loc('signal')] = 'Buy'
    elif df['Close'].iloc[i] < df['Close'].iloc[i-1] < df['Close'].iloc[i-2]:
        df.iloc[i, df.columns.get_loc('signal')] = 'Sell'

# Appliquer le filtre
if signal_filter != "Tous":
    df = df[df['signal'] == signal_filter]

# Affichage
st.title(f"📈 Signaux de trading : {crypto_name} ({ticker})")
st.write(f"Période sélectionnée : {start_date} → {end_date}")
st.dataframe(df[['Close', 'rsi', 'macd', 'sma', 'signal']].tail(10))

# Graphique
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df.index, df['Close'], label='Prix de clôture', color='blue')
ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
ax.set_title(f"Signaux de trading pour {ticker}")
ax.set_xlabel("Date")
ax.set_ylabel("Prix ($)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Export CSV
csv = df.to_csv().encode('utf-8')
st.download_button("📥 Télécharger CSV", csv, f"{ticker}_signaux.csv", "text/csv")
