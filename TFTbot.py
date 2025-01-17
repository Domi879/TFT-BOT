import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
from flask import Flask

# Inserisci il tuo token qui
TELEGRAM_BOT_TOKEN = "7473377342:AAGbCvzSMxAhCeb_m9wuF9VSsLC4BmzOPT0"  # Sostituisci con il tuo token
# URL della pagina di news di TFT in italiano
TFT_URL = "https://euw.leagueoflegends.com/it-it/news/tags/teamfight-tactics/"
# URL di una foto che vuoi inviare insieme alla patch
IMAGE_URL = "https://i.imgur.com/KyA7abw.jpeg"  # Cambia con l'URL dell'immagine
# File dove salviamo i chat_id dei gruppi
CHAT_ID_FILE = "chat_ids.txt"

# Funzione per ottenere l'URL dell'ultima patch
def get_latest_patch_url():
    try:
        response = requests.get(TFT_URL)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Cerca tutti gli articoli con il link
            articles = soup.find_all("a", href=True)
            
            # Cerca l'articolo che contiene "Note sulla patch" (in italiano)
            for article in articles:
                if "Note sulla patch" in article.text:  # Controlla se il titolo contiene la stringa in italiano
                    patch_url = article['href']
                    # Se il link è relativo, aggiungiamo il prefisso corretto
                    if not patch_url.startswith("http"):
                        patch_url = "https://teamfighttactics.leagueoflegends.com" + patch_url
                    return patch_url
        return None
    except Exception as e:
        print(f"Errore durante il recupero della patch: {e}")
        return None

# Funzione per salvare il chat_id in un file
def save_chat_id(chat_id):
    with open(CHAT_ID_FILE, "a") as file:
        file.write(f"{chat_id}\n")

# Funzione che gestisce il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    save_chat_id(chat_id)  # Salva il chat_id ogni volta che qualcuno usa /start
    await update.message.reply_text("Ciao! Sono il tuo bot di TFT. Usa /patch per vedere la patch attuale.")

# Funzione che invia il link della patch e una foto come allegato
async def patch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    patch_url = get_latest_patch_url()
    if patch_url:
        # Invia la foto come allegato
        await update.message.reply_photo(photo=IMAGE_URL, caption=f"📢 Nuova patch appena uscita!\nNon perdetevi tutti i cambiamenti del meta!\n📍 @TFTitalia {patch_url}")
    else:
        await update.message.reply_text("Non sono riuscito a trovare le informazioni sulla patch. Riprova più tardi.")

# Funzione per inviare la patch a tutti i gruppi salvati
async def send_patch(application: Application):
    patch_url = get_latest_patch_url()
    if patch_url:
        with open(CHAT_ID_FILE, "r") as file:
            chat_ids = file.readlines()
        # Rimuovi eventuali righe vuote
        chat_ids = [chat_id.strip() for chat_id in chat_ids]
        # Invia il messaggio con la foto come allegato e il link della patch a ogni chat_id
        for chat_id in chat_ids:
            try:
                # Invia la foto come allegato
                await application.bot.send_photo(chat_id, photo=IMAGE_URL, caption=f"📢 Nuova patch appena uscita!\nNon perdetevi tutti i cambiamenti del meta!\n📍 @TFTitalia {patch_url}")
                # Invia anche il messaggio con il link
                await application.bot.send_message(chat_id, f"📢 Nuova patch appena uscita!\nNon perdetevi tutti i cambiamenti del meta!\n📍 @TFTitalia {patch_url}")
            except Exception as e:
                print(f"Errore durante l'invio al gruppo {chat_id}: {e}")

# Crea un'app Flask per il controllo di salute
app = Flask(__name__)

# Endpoint di salute per il controllo su Koyeb
@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

# Funzione per avviare il server Flask in un thread separato
def run_flask():
    app.run(host="0.0.0.0", port=8000)
# Funzione principale che avvia il bot
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
    job_queue.run_repeating(lambda context: send_patch(application), interval=1800, first=0)  # Controlla ogni 30 minuti

    # Avvia il bot in modalità polling
    application.run_polling()

# Avvia il bot
if __name__ == "__main__":
    main()