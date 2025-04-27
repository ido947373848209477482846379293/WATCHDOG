from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import constants
import os


BOT_TOKEN = constants.TELEGRAM_BOT_TOKEN
bot = Bot(BOT_TOKEN)

async def send_alert_message(chat_id):
    await bot.send_message(chat_id=chat_id, text="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor")

def generate_six_digit_code():
    return random.randint(100000, 999999)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    verif_code = generate_six_digit_code()

    await context.bot.send_message(chat_id=chat_id, text=f"Your verification code is: {verif_code}")

    f = open("chat_id_to_code.txt", "a")
    f.write(f"{verif_code} {chat_id}\n")
    f.close()

def main():
    if os.path.exists("chat_id_to_code.txt"):
        os.remove("chat_id_to_code.txt")
    f = open("chat_id_to_code.txt", "x")
    f.close()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()
