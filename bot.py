import time
import requests
from postgrest import PostgrestClient
import os

# ⚙️ Configuration Supabase via postgrest-py
SUPABASE_URL = os.getenv("https://nvikogksjvssqphfultt.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52aWtvZ2tzanZzc3FwaGZ1bHR0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjM3NTMsImV4cCI6MjA2OTM5OTc1M30.Nv1n4OdKpb8MJfdUX9AUQCtuHtrc-NsLNWBZXtjUiho")
client = PostgrestClient(f"{SUPABASE_URL}/rest/v1/")
client.auth(SUPABASE_KEY)

# ⚙️ Configuration Telegram
TOKEN = os.getenv("8022993558:AAHKRheQTEp-UjBzYxn7FiiETp2WDXvUXKI")
URL = f"https://api.telegram.org/bot{TOKEN}"

# 🔑 Ton ID Telegram
ADMIN_ID = int(os.getenv("8118437300"))  # Ajoute-le dans Render

def get_updates(offset=None):
    params = {"timeout": 100, "offset": offset}
    response = requests.get(URL + "/getUpdates", params=params)
    return response.json()

def send_message(chat_id, text):
    requests.post(URL + "/sendMessage", data={
        "chat_id": chat_id,
        "text": text
    })

def insert_user_supabase(chat_id):
    try:
        exists = client.from_("users").select("id").eq("id", chat_id).execute().data
        if not exists:
            client.from_("users").insert({
                "id": chat_id,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }).execute()
    except Exception as e:
        print("Erreur Supabase:", e)

def get_binance_close_prices(symbol="BTCUSDT", interval="1h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    close_prices = [float(candle[4]) for candle in data]
    return close_prices

def calculate_rsi(prices, period=14):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(prices)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_ema(prices, period):
    ema = []
    k = 2 / (period + 1)
    for i, price in enumerate(prices):
        if i == 0:
            ema.append(price)
        else:
            ema.append(price * k + ema[-1] * (1 - k))
    return ema

def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = calculate_ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line[-1], signal_line[-1], histogram[-1]

def main():
    last_update_id = None
    user_crypto = {}

    while True:
        updates = get_updates(offset=last_update_id)
        if "result" in updates and updates["result"]:
            for update in updates["result"]:
                if "message" not in update:
                    continue

                chat_id = update["message"]["chat"]["id"]
                message = update["message"].get("text", "")

                last_update_id = update["update_id"] + 1

                # 🔐 Enregistrer l'utilisateur dans Supabase
                insert_user_supabase(chat_id)

                # 🔀 Commandes
                if chat_id not in user_crypto:
                    user_crypto[chat_id] = "BTCUSDT"

                if message.startswith("/setcrypto"):
                    parts = message.split()
                    if len(parts) == 2:
                        new_crypto = parts[1].upper()
                        if new_crypto.isalnum() and 5 <= len(new_crypto) <= 12:
                            user_crypto[chat_id] = new_crypto
                            send_message(chat_id, f"✅ Crypto définie sur {new_crypto}")
                        else:
                            send_message(chat_id, "❌ Crypto invalide. Exemple : /setcrypto ETHUSDT")
                    else:
                        send_message(chat_id, "Usage : /setcrypto SYMBOL")

                elif message == "/rsi":
                    try:
                        prices = get_binance_close_prices(user_crypto[chat_id])
                        rsi = calculate_rsi(prices)
                        send_message(chat_id, f"📊 RSI {user_crypto[chat_id]} : {rsi}")
                    except Exception as e:
                        send_message(chat_id, f"Erreur RSI : {e}")

                elif message == "/macd":
                    try:
                        prices = get_binance_close_prices(user_crypto[chat_id])
                        macd, signal, hist = calculate_macd(prices)
                        send_message(chat_id, f"📈 MACD {user_crypto[chat_id]}:\nMACD: {macd:.4f}\nSignal: {signal:.4f}\nHistogram: {hist:.4f}")
                    except Exception as e:
                        send_message(chat_id, f"Erreur MACD : {e}")

                elif message == "/users":
                    try:
                        if chat_id != ADMIN_ID:
                            send_message(chat_id, "❌ Tu n'as pas l'autorisation.")
                            continue
                        
                        users = client.from_("users").select("id").execute().data
                        if not users:
                            send_message(chat_id, "Aucun utilisateur enregistré.")
                        else:
                            user_list = "\n".join([str(u["id"]) for u in users])
                            send_message(chat_id, f"👥 Utilisateurs enregistrés :\n{user_list}")
                    except Exception as e:
                        send_message(chat_id, f"Erreur Supabase : {e}")

                else:
                    send_message(chat_id, "Commande non reconnue. Essaie /rsi, /macd, /setcrypto ETHUSDT ou /users")

        time.sleep(60)

main()
