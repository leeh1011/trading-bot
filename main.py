import time
from datetime import datetime

from settings import SYMBOLS, LOOP_INTERVAL, RISK
from utils.kis_api import KISAPI
from core.strategy import Strategy
from core.portfolio import Portfolio
from core.execution import ExecutionEngine
from notification.approval_manager import ApprovalManager
from notification.telegram_bot import TelegramBot
from database.db import init_db, log_signal, log_error

init_db()

def is_market_open():
    now = datetime.now()
    current = now.strftime("%H:%M")

    # 국내장 기준
    return "09:00" <= current <= "15:30"


def check_auto_exit(symbol, current_price, portfolio, execution):
    positions = portfolio.positions

    if symbol not in positions:
        return

    avg_price = positions[symbol]["avg_price"]
    pnl_rate = (current_price - avg_price) / avg_price

    if pnl_rate <= RISK["stop_loss"]:
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "price": current_price,
            "reason": f"자동 손절 {pnl_rate:.2%}"
        }
        print(f"🚨 자동 손절 실행: {signal}")
        execution.execute(signal)

    elif pnl_rate >= RISK["take_profit"]:
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "price": current_price,
            "reason": f"자동 익절 {pnl_rate:.2%}"
        }
        print(f"💰 자동 익절 실행: {signal}")
        execution.execute(signal)


def main():
    print("🚀 KIS Auto Trading Bot Started")

    api = KISAPI()
    api.get_token()

    strategy = Strategy()
    portfolio = Portfolio()

    balance = api.get_balance()
    synced = portfolio.sync_from_kis_balance(balance)
    print("🔄 계좌 동기화 완료:", synced)

    execution = ExecutionEngine(portfolio,api)
    approval = ApprovalManager()
    bot = TelegramBot(approval, execution)

    while True:
        if not is_market_open():
            print("⏸ 장중 아님 - 대기 중")
            time.sleep(60)
            continue

        print("\n📊 5분봉 시장 스캔 중...")

        for symbol in SYMBOLS:
            df = api.get_minute_chart(symbol)

            if df.empty or len(df) < 20:
                print(f"❌ 데이터 부족: {symbol}")
                continue

            current_price = float(df.iloc[-1]["close"])

            # 손절/익절은 자동 매도
            check_auto_exit(symbol, current_price, portfolio, execution)

            # 전략 신호 생성
            signal = strategy.generate_signal(df, symbol)

            if signal and signal["action"] == "BUY" and symbol in portfolio.positions:
                print(f"⚠️ 이미 보유 중이라 BUY 무시: {symbol}")
                continue

            if not signal:
                print(f"신호 없음: {symbol}")
                continue

            print(f"📈 신호 발생: {signal}")
            log_signal(signal)

            if signal["action"] == "BUY":
                bot.send_signal(signal)

            elif signal["action"] == "SELL":
                # RSI 같은 전략 매도는 사용자 승인
                bot.send_signal(signal)

        approval.cleanup(bot.updater.bot)

        print("⏳ 다음 5분 대기...")
        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    main()