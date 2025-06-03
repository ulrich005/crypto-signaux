import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime

st.set_page_config(page_title="Crypto Signal App", layout="wide")

# 🔁 Fonction pour récupérer les données
def load_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
    df.dropna(inplace=True)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df.dropna(inplace=True)
    return df

# 🧠 Fonction pour générer des signaux
def get_smart_signal(row):
    try:
        if (
            row['rsi'] < 30
            and row['macd'] > row['macd_signal']
            and row['ema_12'] > row['ema_26']
        ):
            return 'Buy'
        elif (
            row['rsi'] > 70
            and row['macd'] < row['macd_signal']
            and row['ema_12'] < row['ema_26']
        ):
            return 'Sell'
        else:
            return 'Hold'
    except:
        return 'Hold'

# 📈 Liste des cryptos
crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

# 🎛️ Paramètres
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# 🔄 Rafraîchir les données
if st.sidebar.button("🔄 Actualiser les signaux"):
    df = load_data(ticker, start_date, end_date)

    # 🔢 Indicateurs
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

    # 🚦 Signaux
    df['signal'] = df.apply(get_smart_signal, axis=1)

    st.title(f"📊 {crypto_name} – Analyse Technique")

    if signal_filter != "Tous":
        df = df[df['signal'] == signal_filter]

    st.subheader("📋 Derniers signaux")
    st.dataframe(df[['Close', 'rsi', 'macd', 'macd_signal', 'ema_12', 'ema_26', 'sma', 'bb_upper', 'bb_lower', 'pct_change_3d', 'signal']].tail(10))

    # 📈 Graphique
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Clôture', color='blue')
    ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--', color='orange')
    ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--', color='red')
    ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':', color='gray')
    ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':', color='gray')
    ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
    ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
    ax.set_title(f"Graphique indicateurs – {crypto_name}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix ($)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # 💰 Performance théorique
    buy_prices = df[df['signal'] == 'Buy']['Close'].values
    sell_prices = df[df['signal'] == 'Sell']['Close'].values
    paired_trades = list(zip(buy_prices[:len(sell_prices)], sell_prices))
    profits = [sell - buy for buy, sell in paired_trades]

    if profits:
        total_profit = sum(profits)
        average_profit = total_profit / len(profits)
        st.subheader("💸 Résumé théorique des trades")
        st.write(f"Nombre de trades : {len(profits)}")
        st.write(f"Gains/Pertes cumulés : {total_profit:.2f} $")
        st.write(f"Rendement moyen par trade : {average_profit:.2f} $")
    else:
        st.info("Pas assez de signaux Buy/Sell pour afficher les gains/pertes.")

    # 📤 Export CSV
    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")




