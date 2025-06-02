from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import json
import os

# Տեղադրիր քո TOKEN–ը այստեղ
TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"

# VIP խմբի հղումը (invite link)
VIP_GROUP_LINK = "https://t.me/+YourGroupInvite"

# Բեռնենք whitelist
def load_whitelist():
    with open("whitelist.json", "r") as f:
        return json.load(f)

# /start հրաման
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    whitelist = load_whitelist()

    if user_id in whitelist and whitelist[user_id]:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text=f"✅ Access granted!\nHere is your VIP link:\n{VIP_GROUP_LINK}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="🚫 Access denied. Please subscribe to get access.\n💳 Contact @YourUsername to pay.")

# Run բոտը
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
