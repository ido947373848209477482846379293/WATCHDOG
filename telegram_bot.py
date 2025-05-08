from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import constants
import db
import requests


BOT_TOKEN = constants.TELEGRAM_BOT_TOKEN

def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Failed to send message: {e}")
        return False

def generate_six_digit_code():
    return random.randint(100000, 999999)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    verif_code = generate_six_digit_code()

    await context.bot.send_message(chat_id=chat_id, text=f"Your verification code is: {verif_code}")

    db.create_new_chat_id_verif_code(str(chat_id), str(verif_code))

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()
