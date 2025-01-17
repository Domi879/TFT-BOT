import logging
import os
import threading
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import requests

# Inserisci il tuo token qui
TELEGRAM_BOT_TOKEN = "7473377342:AAGbCvzSMxAhCeb_m9wuF9VSsLC4BmzOPT0"
TFT_URL = "https://euw.leagueoflegends.com/it-it/news/tags/teamfight-tactics/"
IMAGE_URL = "https://i.imgur.com/KyA7abw.jpeg"  # Cambia con l'URL dell'immagine
CHAT_ID_FILE = "chat_ids.txt"

# Crea un'app Flask per il controllo di salute
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

# Funzione per avviare il server Flask in un thread separato
def run_flask():
    print("Avviando il server Flask...")
    app.run(host="0.0.0.0", port=8000)

# Funzione per estrarre l'URL della patch da TFT
def get_patch_url():
    try:
        response = requests.get(TFT_URL)
        soup = BeautifulSoup(response.content, "html.parser")
        article = soup.find("article")
        link = article.find("a")["href"]
        return link
    except Exception as e:
        print(f"Errore durante l'estrazione dell'URL della patch: {e}")
        return None

# Funzione per inviare la patch ai gruppi
async def send_patch(application: Application):
    patch_url = get_patch_url()
    if patch_url:
        print(f"URL della patch trovato: {patch_url}")
        with open(CHAT_ID_FILE, "r") as file:
            chat_ids = file.readlines()
        # Rimuovi eventuali righe vuote
        chat_ids = [chat_id.strip() for chat_id in chat_ids]
        # Invia il messaggio con la foto come allegato e il link della patch a ogni chat_id
        for chat_id in chat_ids:
            try:
                await application.bot.send_photo(
                    chat_id=chat_id,
                    photo=IMAGE_URL,
                    caption=f"Nuova patch di TFT! Dettagli: {patch_url}"
                )
                print(f"Patch inviata a {chat_id}")
            except Exception as e:
                print(f"Errore durante l'invio al gruppo {chat_id}: {e}")

# Funzione per il comando /start del bot Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot.")

# Funzione per il comando /patch del bot Telegram
async def patch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sto cercando la patch!")

# Funzione principale che avvia il bot Telegram
def main():
    # Crea l'applicazione Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Aggiungi gli handler per i comandi
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('patch', patch))

    # Esegui il monitoraggio della patch ogni 30 minuti
    job_queue = application.job_queue
    job_queue.run_repeating(lambda context: send_patch(application), interval=1800, first=0)  # Controlla ogni 30 minuti

    # Avvia il server Flask in un thread separato per il controllo di salute
    thread = threading.Thread(target=run_flask)
    thread.daemon = True
    thread.start()

    # Avvia il bot in modalità polling
    application.run_polling()

if __name__ == "__main__":
    # Imposta il livello di log per il bot Telegram
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()

