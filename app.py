import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
from datetime import datetime
from PIL import Image
import io

# CONFIG
st.set_page_config(page_title="Crypto Signal App", layout="wide")

crypto_options = {
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum (ETH)': 'ETH-USD',
    'Solana (SOL)': 'SOL-USD',
    'Cardano (ADA)': 'ADA-USD',
    'Dogecoin (DOGE)': 'DOGE-USD'
}

# SIDEBAR
st.sidebar.header("Paramètres")
crypto_name = st.sidebar.selectbox("Choisir une crypto", list(crypto_options.keys()))
ticker = crypto_options[crypto_name]
start_date = st.sidebar.date_input("Date de début", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("Date de fin", datetime(2025, 6, 2))
signal_filter = st.sidebar.radio("Filtrer les signaux", ["Tous", "Buy", "Sell"])

# SMART SIGNAL
def smart_signal(row):
    if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['ema_12'] > row['ema_26']:
        return 'Buy'
    elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['ema_12'] < row['ema_26']:
        return 'Sell'
    return 'Hold'

# ACTUALISATION
if st.sidebar.button("🔄 Actualiser les signaux"):
    df = yf.download(ticker, start=start_date, end=end_date)[['Close']].copy()
    if df.empty:
        st.error("Aucune donnée disponible pour cette période.")
        st.stop()

    close_series = df['Close']
    df['rsi'] = ta.momentum.RSIIndicator(close=close_series).rsi()
    macd_indicator = ta.trend.MACD(close=close_series)
    df['macd'] = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()
    df['sma'] = ta.trend.SMAIndicator(close=close_series, window=14).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=close_series, window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(close=close_series, window=26).ema_indicator()

    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['pct_change_3d'] = df['Close'].pct_change(periods=3) * 100
    df.dropna(inplace=True)

    df['signal'] = df.apply(smart_signal, axis=1)

    # MINI-CHARTS
    st.title("📊 Vue d'ensemble – Mini-charts, Signaux & Horaires")
    st.markdown("Aperçu des signaux récents avec horodatage pour chaque crypto surveillée.")
    cols = st.columns(3)

    for idx, (symbol, name) in enumerate(crypto_options.items()):
        try:
            df_temp = yf.download(crypto_options[name], start=start_date, end=end_date)[['Close']].copy()
            if df_temp.empty or len(df_temp) < 30:
                continue

            df_temp['rsi'] = ta.momentum.RSIIndicator(close=df_temp['Close']).rsi()
            df_temp['macd'] = ta.trend.MACD(close=df_temp['Close']).macd()
            df_temp['macd_signal'] = ta.trend.MACD(close=df_temp['Close']).macd_signal()
            df_temp['ema_12'] = ta.trend.EMAIndicator(close=df_temp['Close'], window=12).ema_indicator()
            df_temp['ema_26'] = ta.trend.EMAIndicator(close=df_temp['Close'], window=26).ema_indicator()
            df_temp.dropna(inplace=True)
            df_temp['signal'] = df_temp.apply(smart_signal, axis=1)

            last_row = df_temp[df_temp['signal'].isin(['Buy', 'Sell'])].iloc[-1]
            last_signal = last_row['signal']
            last_time = last_row.name.strftime("%Y-%m-%d %H:%M")

            fig, ax = plt.subplots(figsize=(2.5, 0.8))
            ax.plot(df_temp.index, df_temp['Close'], color='green' if last_signal == 'Buy' else 'red', linewidth=1)
            ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
            ax.set_title(name, fontsize=8)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.01)
            buf.seek(0)

            with cols[idx % 3]:
                st.image(buf, use_column_width=True)
                st.markdown(f"**Signal :** :{'green_circle' if last_signal == 'Buy' else 'red_circle'}: **{last_signal}**")
                st.caption(f"🕒 {last_time}")

        except Exception:
            with cols[idx % 3]:
                st.warning(f"Erreur chargement {name}")

    # DÉTAILS
    st.title(f"📉 Détails Techniques – {crypto_name}")
    df_filtered = df[df['signal'] == signal_filter] if signal_filter != "Tous" else df

    st.dataframe(df_filtered[['Close', 'rsi', 'macd', 'macd_signal', 'sma', 'ema_12', 'ema_26', 'bb_upper', 'bb_lower', 'pct_change_3d', 'signal']].tail(10))

    # GRAPHIQUE
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Clôture', color='blue')
    ax.plot(df.index, df['ema_12'], label='EMA 12', linestyle='--', color='orange')
    ax.plot(df.index, df['ema_26'], label='EMA 26', linestyle='--', color='red')
    ax.plot(df.index, df['bb_upper'], label='Bollinger Haut', linestyle=':', color='gray')
    ax.plot(df.index, df['bb_lower'], label='Bollinger Bas', linestyle=':', color='gray')
    ax.scatter(df[df['signal'] == 'Buy'].index, df[df['signal'] == 'Buy']['Close'], label='Buy', marker='^', color='green')
    ax.scatter(df[df['signal'] == 'Sell'].index, df[df['signal'] == 'Sell']['Close'], label='Sell', marker='v', color='red')
    ax.set_title(f"Graphique – {crypto_name}")
    ax.set_xlabel("Date"); ax.set_ylabel("Prix ($)")
    ax.legend(); ax.grid(True)
    st.pyplot(fig)

    # GAINS / PERTES
    st.subheader("💰 Résumé des gains/pertes théoriques")
    buy_prices = df[df['signal'] == 'Buy']['Close'].tolist()
    sell_prices = df[df['signal'] == 'Sell']['Close'].tolist()
    pairs = zip(buy_prices[:len(sell_prices)], sell_prices)
    profits = [sell - buy for buy, sell in pairs]
    if profits:
        st.write(f"Nombre de trades : {len(profits)}")
        st.write(f"Gains/Pertes cumulés : {sum(profits):.2f} $")
        st.write(f"Rendement moyen : {sum(profits)/len(profits):.2f} $")
    else:
        st.info("Pas assez de signaux pour calculer un rendement.")

    # DOWNLOAD
    csv = df.to_csv().encode('utf-8')
    st.download_button("📥 Télécharger les données", csv, f"{ticker}_signaux.csv", "text/csv")

