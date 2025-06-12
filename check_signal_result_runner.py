import os
import requests
import pandas as pd
from signal_logger import get_recent_signals
from check_trade_result import check_trade_result
from telegram import Bot
from datetime import datetime

TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
CHAT_ID = 5398864436
bot = Bot(token=TELEGRAM_TOKEN)

def check_recent_signal_results():
    print("📊 Checking recent signal results...")

    recent_signals = get_recent_signals(minutes=60)

    if not recent_signals:
        msg = "📭 No recent signals to check."
        print(msg)
        bot.send_message(chat_id=CHAT_ID, text=msg)
        return

    for signal in recent_signals:
        try:
            # Compute signal_time_ms from saved timestamp
            dt = datetime.strptime(signal['timestamp'], '%Y-%m-%d %H:%M:%S')
            signal_time_ms = int(dt.timestamp() * 1000)

            result = check_trade_result(
                symbol=signal['symbol'],
                signal_type=signal['type'],
                entry=signal['entry'],
                tp1=signal['tp1'],
                tp2=signal['tp2'],
                sl=signal['sl'],
                signal_time_ms=signal_time_ms
            )

            msg = f"🧪 {signal['symbol']} ({signal['type']}): {result}"
            print(msg)
            bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print(f"❌ Error checking signal for {signal['symbol']}: {e}")
            bot.send_message(chat_id=CHAT_ID, text=f"❌ Error for {signal['symbol']}")
