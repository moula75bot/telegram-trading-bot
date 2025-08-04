# 🤖 Bot de trading automatique crypto (RSI)

Ce bot surveille le RSI d'une crypto sur Binance et simule des achats/ventes selon les signaux.

## Fonctionnement
- Achat si RSI < 30
- Vente si RSI > 70
- Capital simulé au départ : 5 €
- Alerte Telegram à chaque trade

## Fichiers
- `bot.py` : logique principale
- `config.py` : config (Telegram, capital, symbole)
- `start.sh` : script de lancement
- `render.yaml` : déploiement Render
