from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from signal_logger import send_winrate_to_telegram
from check_signal_result_runner import check_recent_signal_results

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Available commands:\n/winrate – show win rate\n/checkresult – check recent signal results")

def winrate_command(update: Update, context: CallbackContext):
    send_winrate_to_telegram(last_n=50)
    update.message.reply_text("📊 Win rate report sent.")

def checkresult_command(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Checking signal results...")
    check_recent_signal_results()

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("winrate", winrate_command))
    dp.add_handler(CommandHandler("checkresult", checkresult_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
