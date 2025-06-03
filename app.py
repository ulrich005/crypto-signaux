import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
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
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

if st.sidebar.button("🔄 Actualiser les signaux"):
    df = yf.download(ticker, start=start_date, end=end_date, interval='1d')[['Close']].copy()
    if df.empty:
        st.error("Aucune donnée disponible pour cette période.")
        st.stop()

    close_series = pd.Series(df['Close'].values.flatten(), index=df.index)

    df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
    macd = ta.trend.MACD(close=close_series)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=close_series, window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=close_series, window=26).ema_indicator()

    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mavg'] = bb.bollinger_mavg()
    df['pct_change_3d'] = df['Close'].pct_change(periods=3) * 100
    df.dropna(inplace=True)

    df['signal'] = 'Hold'
    buy_prices = []
    sell_prices = []

    for i in range(2, len(df)):
        if close_series.iloc[i] > close_series.iloc[i-1] and close_series.iloc[i-1] > close_series.iloc[i-2]:
            df.iloc[i, df.columns.get_loc('signal')] = 'Buy'
            buy_prices.append(df['Close'].iloc[i])
        elif close_series.iloc[i] < close_series.iloc[i-1] and close_series.iloc[i-1] < close_series.iloc[i-2]:
            df.iloc[i, df.columns.get_loc('signal')] = 'Sell'
            sell_prices.append(df['Close'].iloc[i])

    st.title(f"📊 {crypto_name} – Analyse Technique")

    st.subheader("📋 Données techniques récentes")
    if signal_filter != "Tous":
        df = df[df['signal'] == signal_filter]

    st.dataframe(df[['Close', 'rsi', 'macd', 'macd_signal', 'sma', 'ema_12', 'ema_26', 'bb_upper', 'bb_lower', 'pct_change_3d', 'signal']].tail(20))

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

    if buy_prices and sell_prices:
        paired = zip(buy_prices[:len(sell_prices)], sell_prices)
        profits = [sell - buy for buy, sell in paired]
        total_profit = sum(profits)
        st.subheader("💰 Résumé des gains/pertes théoriques")
        st.write(f"Nombre de trades : {len(profits)}")
        st.write(f"Gains/Pertes cumulés : {total_profit:.2f} $")
        average_profit = total_profit / len(profits) if profits else 0
        st.write(f"Rendement moyen par trade : {average_profit:.2f} $")
    else:
        st.info("Pas assez de signaux Buy/Sell pour calculer les gains/pertes.")

    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")


