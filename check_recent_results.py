from signal_logger import get_recent_signals
from check_trade_result import check_trade_result

def check_recent_signal_results():
    print("📊 Checking recent signal results...")
    recent_signals = get_recent_signals(minutes=60)

    if not recent_signals:
        print("No recent signals found.")
        return

    for signal in recent_signals:
        result = check_trade_result(
            symbol=signal["symbol"],
            signal_type=signal["type"],
            entry=signal["entry"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            sl=signal["sl"]
        )
        print(f"{signal['symbol']} ({signal['type']}): Result = {result}")
