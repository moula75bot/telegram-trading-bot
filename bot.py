import time
import threading
import requests
from flask import Flask

# --- CONFIG ---
TOKEN = '8022993558:AAHKRheQTEp-UjBzYxn7FiiETp2WDXvUXKI'  # ← remplace par ton token Telegram
URL = f'https://api.telegram.org/bot{TOKEN}/'
GOLD_API = 'https://api.metals.live/v1/spot'

alertes = {}

# --- Serveur Flask pour le site web ---
app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>Bot Or - Alertes Gold</title></head>
    <body>
    <h1>Bienvenue sur le Bot Or 🪙</h1>
    <p>Ce bot Telegram vous aide à suivre le prix de l'or et à recevoir des alertes personnalisées.</p>
    <p><a href="https://t.me/TON_BOT_USERNAME">Clique ici pour lancer le bot Telegram</a></p>
    <p>Merci de votre visite !</p>
    </body>
    </html>
    '''

# --- Fonction pour récupérer le prix de l'or ---
def get_gold_price():
    try:
        r = requests.get(GOLD_API)
        data = r.json()
        for item in data:
            if item[0] == 'gold':
                return float(item[1])
    except:
        return None

# --- Fonction pour envoyer un message Telegram ---
def send(chat_id, text):
    requests.post(URL + 'sendMessage', data={'chat_id': chat_id, 'text': text})

# --- Boucle principale du bot Telegram ---
def bot_loop():
    offset = None
    while True:
        updates = requests.get(URL + 'getUpdates', params={'offset': offset}).json()
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")

                if text == "/start":
                    send(chat_id, "Bienvenue 🪙\nUtilise /gold pour voir le prix de l’or ou /alert 2800 pour recevoir une alerte.")
                elif text == "/gold":
                    price = get_gold_price()
                    if price:
                        send(chat_id, f"💰 L’or vaut actuellement {price:.2f} $/oz")
                    else:
                        send(chat_id, "Erreur de récupération du prix.")
                elif text.startswith("/alert"):
                    try:
                        seuil = float(text.split()[1])
                        alertes[chat_id] = seuil
                        send(chat_id, f"🔔 Tu seras alerté quand l’or dépassera {seuil} $/oz")
                    except:
                        send(chat_id, "Utilise : /alert 2800")

        # Vérifie les alertes toutes les 10 sec
        price = get_gold_price()
        if price:
            for chat_id, seuil in list(alertes.items()):
                if price >= seuil:
                    send(chat_id, f"🚨 L’or a atteint {price:.2f} $/oz (seuil : {seuil})")
                    alertes.pop(chat_id)
        time.sleep(10)

# --- Lancer bot et serveur web en parallèle ---
if __name__ == "__main__":
    threading.Thread(target=bot_loop).start()
    app.run(host='0.0.0.0', port=10000)
