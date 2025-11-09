import os
import json
from dotenv import load_dotenv
from keep_alive import keep_alive
import bot
import asyncio

# Charger le .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_TYPE = os.getenv("BOT_TYPE", "bot_discord")

# Charger BOTS_JSON si présent (pour multi-bots)
BOTS_JSON = os.getenv("BOTS_JSON")
if BOTS_JSON:
    try:
        BOTS_JSON = json.loads(BOTS_JSON)
    except Exception as e:
        print(f"⚠️ Erreur parsing BOTS_JSON : {e}")
        BOTS_JSON = []

print(f"🚀 Lancement du bot {BOT_TYPE}...")
print(f"🔑 Token présent : {'Oui' if DISCORD_TOKEN else 'Non'}")

# Vérifier que le token existe
if not DISCORD_TOKEN:
    print("❌ ERREUR : DISCORD_TOKEN n'est pas défini dans le .env")
    exit(1)

# Lancer Flask dans un thread séparé
keep_alive()

# Attendre que Flask démarre
import time
time.sleep(1)

# Lancer le bot Discord
print("🤖 Connexion à Discord...")
try:
    asyncio.run(bot.start_bot(DISCORD_TOKEN))
except KeyboardInterrupt:
    print("\n⛔ Bot arrêté par l'utilisateur")
except Exception as e:
    print(f"❌ Erreur fatale : {e}")
    import traceback
    traceback.print_exc()