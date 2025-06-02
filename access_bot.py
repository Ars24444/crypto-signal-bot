from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
VIP_GROUP_LINK = "https://t.me/+vAr3ecIJJLs0NTdi"

def load_whitelist():
    with open("whitelist.json", "r") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    whitelist = load_whitelist()

    if user_id in whitelist and whitelist[user_id]:
        await context.bot.send_message(chat_id=update.effective_chat.id,
            text=f"✅ Access granted!\nHere is your VIP link:\n{VIP_GROUP_LINK}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
            text="🚫 Access denied. Please subscribe to get access.\n💳 Contact @YourUsername to pay.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
