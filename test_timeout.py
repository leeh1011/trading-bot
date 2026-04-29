import time

from core.portfolio import Portfolio
from core.execution import ExecutionEngine
from notification.approval_manager import ApprovalManager
from notification.telegram_bot import TelegramBot


portfolio = Portfolio()
execution = ExecutionEngine(portfolio)
approval = ApprovalManager()
bot = TelegramBot(approval, execution)

signal = {
    "action": "BUY",
    "symbol": "005930",
    "price": 70000,
    "reason": "timeout test"
}

bot.send_signal(signal)

while True:
    approval.cleanup(bot.updater.bot)
    time.sleep(1)