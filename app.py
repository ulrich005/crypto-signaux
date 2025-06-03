import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Crypto Signal App", layout="wide")

crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime.today())
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

st.title(f"📊 {crypto_name} – Analyse Technique et Signaux de Trading")

@st.cache_data
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)[['Close']].copy()
    return df

df = load_data(ticker, start_date, end_date)

if df.empty:
    st.error("Aucune donnée disponible pour cette période.")
    st.stop()

df['rsi'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
macd = ta.trend.MACD(close=df['Close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['ema_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator()
df['ema_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator()
df['sma'] = ta.trend.SMAIndicator(close=df['Close'], window=14).sma_indicator()
bb = ta.volatility.BollingerBands(close=df['Close'])
df['bb_upper'] = bb.bollinger_hband()
df['bb_lower'] = bb.bollinger_lband()
df['pct_change_3d'] = df['Close'].pct_change(periods=3) * 100

df.dropna(inplace=True)

def get_smart_signal(row):
    try:
        if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
            return 'Buy'
        elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
            return 'Sell'
    except:
        return 'Hold'
    return 'Hold'

required_cols = ['rsi', 'macd', 'macd_signal', 'ema_12', 'ema_26']
df['signal'] = 'Hold'
df_valid = df.dropna(subset=required_cols)
df.loc[df_valid.index, 'signal'] = df_valid.apply(get_smart_signal, axis=1)

# Historique des signaux
alerts = df[df['signal'].isin(['Buy', 'Sell'])][['signal', 'Close']]
alerts['datetime'] = alerts.index
st.subheader("🕒 Historique des Signaux")
st.dataframe(alerts.sort_values(by="datetime", ascending=False).head(10))

# Mini-chart
st.subheader("📈 Sparkline (Mini-Graphique)")
spark_fig, ax = plt.subplots(figsize=(6, 2))
ax.plot(df['Close'], color='blue')
ax.set_title(f"{crypto_name} – Sparkline")
ax.axis('off')
st.pyplot(spark_fig)

# Affichage conditionnel
if signal_filter != "Tous":
    df = df[df['signal'] == signal_filter]

# Tableau
st.subheader("📋 Données Techniques")
st.dataframe(df[['Close', 'rsi', 'macd', 'macd_signal', 'ema_12', 'ema_26', 'sma', 'bb_upper', 'bb_lower', 'pct_change_3d', 'signal']].tail(15))

# Graphique avec signaux
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df.index, df['Close'], label='Clôture')
ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--')
ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--')
ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':')
ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':')
ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
ax.legend()
ax.set_title(f"Graphique avec Signaux – {crypto_name}")
ax.grid(True)
st.pyplot(fig)

# Export
csv = df.to_csv().encode('utf-8')
st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")



