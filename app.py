import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta

# Configuration de la page Streamlit
st.set_page_config(page_title="Crypto Signal App", layout="wide")

# Liste des cryptomonnaies disponibles
crypto_options = {
    'Bitcoin': 'BTC-USD',
    'Ethereum': 'ETH-USD',
    'Solana': 'SOL-USD',
    'Cardano': 'ADA-USD',
    'Dogecoin': 'DOGE-USD',
    'XRP': 'XRP-USD'
}

# Barre latérale pour les paramètres
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", pd.to_datetime("2025-01-01"))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# Télécharger les données de Yahoo Finance
df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
if df.empty:
    st.error("Aucune donnée disponible pour cette période.")
    st.stop()

# Forcer la conversion en Series 1D pour les indicateurs (anti-bug total)
close_series = pd.Series(df['Close'].values.flatten(), index=df.index)

# Ajouter les indicateurs techniques
df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
df['macd'] = ta.trend.MACD(close=close_series).macd()
df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
df.dropna(inplace=True)

# Génération des signaux simples
df['signal'] = 'Hold'
for i in range(2, len(df)):
    if close_series.iloc[i] > close_series.iloc[i-1] and close_series.iloc[i-1] > close_series.iloc[i-2]:
        df.iloc[i, df.columns.get_loc('signal')] = 'Buy'
    elif close_series.iloc[i] < close_series.iloc[i-1] and close_series.iloc[i-1] < close_series.iloc[i-2]:
        df.iloc[i, df.columns.get_loc('signal')] = 'Sell'

# Appliquer le filtre de signaux
if signal_filter != "Tous":
    df = df[df['signal'] == signal_filter]

# Affichage du tableau
st.title(f"📈 Signaux de trading : {crypto_name} ({ticker})")
st.write(f"Période sélectionnée : {start_date} → {end_date}")
st.dataframe(df[['Close', 'rsi', 'macd', 'sma', 'signal']].tail(10))

# Graphique avec les signaux
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

# Téléchargement des données en CSV
csv = df.to_csv().encode('utf-8')
st.download_button("📥 Télécharger CSV", csv, f"{ticker}_signaux.csv", "text/csv")
