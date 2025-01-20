import os
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# Variabili di configurazione
TELEGRAM_BOT_TOKEN = "7473377342:AAGbCvzSMxAhCeb_m9wuF9VSsLC4BmzOPT0"
TFT_URL = "https://teamfighttactics.leagueoflegends.com/it-it/news/"
IMAGE_URL = "https://i.imgur.com/KyA7abw.jpeg"
CHAT_ID_FILE = "chat_ids.txt"
LAST_PATCH_FILE = "last_patch.txt"

# Crea l'app Flask per il controllo di salute
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=8000)

def get_patch_url():
    """Recupera l'URL della patch dalla pagina web specificata."""
    try:
        response = requests.get(TFT_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cerca tutti i link nella pagina e filtra quelli con "note sulla patch"
        patch_links = soup.find_all('a', href=True)
        for link in patch_links:
            if "note sulla patch" in link.text.lower():  # Cerca "note sulla patch" nel testo del link
                # Restituisci l'URL completo
                patch_url = link['href']
                if not patch_url.startswith("http"):  # Se l'URL non è completo, aggiungilo
                    patch_url = "https://teamfighttactics.leagueoflegends.com" + patch_url
                return patch_url  # Ritorna il link completo

    except Exception as e:
        print(f"Errore durante il recupero dell'URL della patch: {e}")
    return None

def save_chat_id(chat_id):
    """Salva l'ID della chat se non è già presente."""
    if not os.path.exists(CHAT_ID_FILE):
        with open(CHAT_ID_FILE, "w") as file:
            pass

    with open(CHAT_ID_FILE, "r") as file:
        chat_ids = file.read().splitlines()

    if str(chat_id) not in chat_ids:
        with open(CHAT_ID_FILE, "a") as file:
            file.write(f"{chat_id}\n")
        print(f"Salvato chat_id: {chat_id}")

async def send_patch(application: Application, patch_url: str, pin_message: bool = False):
    """Invia la patch a tutte le chat salvate e la fissa se richiesto."""
    try:
        if not os.path.exists(CHAT_ID_FILE):
            print(f"Il file {CHAT_ID_FILE} non esiste!")
            return

        with open(CHAT_ID_FILE, "r") as file:
            chat_ids = file.readlines()

        chat_ids = [chat_id.strip() for chat_id in chat_ids]
        for chat_id in chat_ids:
            # Invia il messaggio con il link della patch e l'immagine allegata
            message = await application.bot.send_photo(
                chat_id=chat_id,
                photo=IMAGE_URL,
                caption=f"Nuova patch disponibile: {patch_url}",
            )
            
            # Fissa il messaggio solo quando rileviamo la nuova patch e quando `pin_message` è True
            if pin_message:
                await application.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message.message_id
                )
    except Exception as e:
        print(f"Errore durante l'invio al gruppo: {e}")

async def check_for_new_patch(application: Application):
    """Controlla se c'è una nuova patch e la invia se necessario."""
    patch_url = get_patch_url()
    if patch_url:
        last_patch_url = None
        if os.path.exists(LAST_PATCH_FILE):
            with open(LAST_PATCH_FILE, "r") as file:
                last_patch_url = file.read().strip()

        if patch_url != last_patch_url:
            # Invio patch con fissaggio
            await send_patch(application, patch_url, pin_message=True)
            with open(LAST_PATCH_FILE, "w") as file:
                file.write(patch_url)
        else:
            print("Nessuna nuova patch disponibile.")
    else:
        print("Errore nel recupero dell'URL della patch.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start: registra l'utente e invia un messaggio di benvenuto."""
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await update.message.reply_text("Ciao! Ora riceverai aggiornamenti sulle patch di TFT!")

async def added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra l'ID del gruppo quando il bot viene aggiunto."""
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="Ciao gruppo! Ora riceverete aggiornamenti sulle patch di TFT!")

async def patch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Invia manualmente la patch corrente senza fissarla."""
    patch_url = get_patch_url()
    
    if patch_url:
        # Usa l'ID della chat in cui il comando è stato inviato (che è un gruppo)
        chat_id = update.effective_chat.id
        
        # Invia il messaggio con il link della patch e l'immagine allegata insieme (senza fissarlo)
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=IMAGE_URL,  # L'immagine della patch
            caption=f"Nuova patch disponibile: {patch_url}",  # Testo con link della patch
        )
    else:
        await update.message.reply_text("Non sono riuscito a recuperare la patch.")


def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handler dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, added_to_group))
    application.add_handler(CommandHandler("patch", patch))

    # Job per verificare le patch ogni 30 minuti
    job_queue = application.job_queue
    job_queue.run_repeating(lambda context: check_for_new_patch(application), interval=1800, first=0)

    print("Bot avviato!")
    application.run_polling()

# Avvia il server Flask in un thread separato
threading.Thread(target=run_flask).start()

if __name__ == "__main__":
    main()



