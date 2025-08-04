import threading
import time
import requests
import numpy as np
import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BINANCE_SYMBOL, CAPITAL

# CONFIG
RSI_PERIOD = 14
INTERVAL = "5m"
API_BASE = "https://api.binance.com"
SYMBOL = BINANCE_SYMBOL
capital = CAPITAL
position = None
entry_price = 0

def get_price_data():
    url = f"{API_BASE}/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=100"
    response = requests.get(url)
    data = response.json()
    closes = [float(candle[4]) for candle in data]
    return closes

def calculate_rsi(closes):
    deltas = np.diff(closes)
    seed = deltas[:RSI_PERIOD]
    up = seed[seed >= 0].sum() / RSI_PERIOD
    down = -seed[seed < 0].sum() / RSI_PERIOD
    rs = up / down if down != 0 else 0
    rsi = [100 - (100 / (1 + rs))]

    for delta in deltas[RSI_PERIOD:]:
        gain = max(delta, 0)
        loss = -min(delta, 0)
        up = (up * (RSI_PERIOD - 1) + gain) / RSI_PERIOD
        down = (down * (RSI_PERIOD - 1) + loss) / RSI_PERIOD
        rs = up / down if down != 0 else 0
        rsi.append(100 - (100 / (1 + rs)))

    return rsi[-1]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=data)

def log(msg):
    print(msg)
    send_telegram(msg)
    with open("trades.log", "a") as f:
        f.write(f"{datetime.datetime.now()} - {msg}\n")

def trading_loop():
    global capital, position, entry_price

    while True:
        try:
            closes = get_price_data()
            current_price = closes[-1]
            rsi = calculate_rsi(closes)
            log(f"RSI: {rsi:.2f} | Price: {current_price:.2f} | Capital: {capital:.2f} | Position: {position}")

            if rsi < 30 and position is None:
                position = "LONG"
                entry_price = current_price
                log(f"📈 Achat simulé à {entry_price:.2f}")

            elif rsi > 70 and position == "LONG":
                profit_pct = (current_price - entry_price) / entry_price
                gain = capital * profit_pct
                capital += gain
                log(f"📉 Vente simulée à {current_price:.2f} | Gain: {gain:.2f} €")
                position = None
                entry_price = 0

        except Exception as e:
            log(f"Erreur : {e}")

        time.sleep(300)  # 5 min

# Démarrer le trading dans un thread
t = threading.Thread(target=trading_loop)
t.daemon = True
t.start()

# === FLASK WEB SERVER (nécessaire pour Render gratuit) ===
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot de trading actif et connecté à Telegram ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
