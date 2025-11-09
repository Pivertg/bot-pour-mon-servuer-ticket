from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Le thread s'arrête quand le bot s'arrête
    t.start()
    print("✅ Flask (keep_alive) démarré en arrière-plan")