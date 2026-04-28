import time
import pandas as pd
import random

from core.strategy import Strategy
from core.portfolio import Portfolio
from core.execution import ExecutionEngine
from notification.approval_manager import ApprovalManager
from notification.telegram_bot import TelegramBot


def generate_fake_data():
    return pd.DataFrame({
        "close": [random.randint(100, 200) for _ in range(50)]
    })


def main():
    print("🚀 Auto Trading Bot Started")

    strategy = Strategy()
    portfolio = Portfolio()
    execution = ExecutionEngine(portfolio)
    approval = ApprovalManager()
    bot = TelegramBot(approval, execution)

    symbols = ["005930", "000660", "AAPL", "NVDA"]

    while True:
        print("\n📊 시장 스캔 중...")

        for symbol in symbols:
            data = generate_fake_data()

            signal = strategy.generate_signal(data, symbol)

            if signal:
                print(f"📈 신호 발생: {signal}")
                bot.send_signal(signal)

        approval.cleanup()

        time.sleep(10)  # 테스트용 (실전은 300초 = 5분)


if __name__ == "__main__":
    main()
