from core.portfolio import Portfolio
from core.execution import ExecutionEngine
from notification.approval_manager import ApprovalManager
from notification.telegram_bot import TelegramBot


def test_telegram():
    portfolio = Portfolio()
    execution = ExecutionEngine(portfolio)
    approval = ApprovalManager()

    bot = TelegramBot(approval, execution)

    # 테스트 신호
    signal = {
        "action": "BUY",
        "symbol": "TEST",
        "price": 100,
        "reason": "test signal"
    }

    bot.send_signal(signal)

    print("신호 전송 완료 - Telegram 확인")


if __name__ == "__main__":
    test_telegram()
