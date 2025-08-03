import time
import requests
import json
from datetime import datetime

# Ton token Telegram
TOKEN = '8022993558:AAHKRheQTEp-UjBzYxn7FiiETp2WDXvUXKI'
URL = f'https://api.telegram.org/bot{TOKEN}/'

# URL pour récupérer le prix de l'or en EUR
GOLD_API = 'https://api.metals.live/v1/spot'  # Gratuit, pas besoin de clé API

# Mémorise les alertes utilisateur : {chat_id: seuil}
alertes = {}

def get_gold_price():
    try:
        r = requests.get(GOLD_API)
        data = r.json()
        for item in data:
            if item[0] == 'gold':
                return float(item[1])  # prix en USD
    except:
        return None

def get_updates(offset=None):
    r = requests.get(URL + 'getUpdates', params={'timeout': 100, 'offset': offset})
    return r.json()

def send_message(chat_id, text):
    requests.post(URL + 'sendMessage', data={'chat_id': chat_id, 'text': text})

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")

                    if text == "/start":
                        send_message(chat_id, "👋 Bienvenue ! Envoie /gold pour le prix actuel de l'or ou /alert 2800 pour recevoir une alerte.")
                    elif text == "/gold":
                        price = get_gold_price()
                        if price:
                            send_message(chat_id, f"💰 Prix actuel de l'or : {price:.2f} $/oz")
                        else:
                            send_message(chat_id, "Erreur lors de la récupération du prix de l'or.")
                    elif text.startswith("/alert"):
                        try:
                            seuil = float(text.split(" ")[1])
                            alertes[chat_id] = seuil
                            send_message(chat_id, f"🔔 Alerte enregistrée : tu seras prévenu si l'or dépasse {seuil} $/oz.")
                        except:
                            send_message(chat_id, "Utilise : /alert 2800")
        
        # Vérifie les alertes toutes les 60 sec
        price = get_gold_price()
        if price:
            for chat_id, seuil in alertes.items():
                if price >= seuil:
                    send_message(chat_id, f"🚨 L'or a atteint {price:.2f} $/oz (seuil {seuil})")
                    alertes.pop(chat_id)
                    break

        time.sleep(10)

if __name__ == '__main__':
    main()
