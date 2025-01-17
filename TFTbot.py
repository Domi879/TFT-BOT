from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import threading
from flask import Flask

# Inserisci il tuo token qui
TELEGRAM_BOT_TOKEN = "7473377342:AAGbCvzSMxAhCeb_m9wuF9VSsLC4BmzOPT0"
TFT_URL = "https://euw.leagueoflegends.com/it-it/news/tags/teamfight-tactics/"
IMAGE_URL = "https://i.imgur.com/KyA7abw.jpeg"
CHAT_ID_FILE = "chat_ids.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot.")

async def patch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sto cercando la patch!")

async def send_patch():
    # Codice per inviare la patch

# Crea un'app Flask per il controllo di salute
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

def run_flask():
    print("Avviando il server Flask per il controllo di salute...")
    app.run(host="0.0.0.0", port=8000)

def main():
    # Avvia il server Flask in un thread separato per il controllo di salute
    thread = threading.Thread(target=run_flask)
    thread.daemon = True
    thread.start()

    # Crea l'applicazione Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Aggiungi gli handler per i comandi
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('patch', patch))

    # Esegui il monitoraggio della patch ogni 30 minuti
    job_queue = application.job_queue
    job_queue.run_repeating(lambda context: send_patch(), interval=1800, first=0)

    # Avvia il bot in modalità polling
    application.run_polling()

if __name__ == "__main__":
    main()
