import time
import uuid
from settings import APPROVAL_TIMEOUT, SIGNAL_COOLDOWN_SECONDS


class ApprovalManager:
    def __init__(self):
        self.pending = {}
        self.last_signal_time = {}

    def has_pending_symbol(self, symbol):
        return any(item["signal"]["symbol"] == symbol for item in self.pending.values())

    def is_in_cooldown(self, symbol):
        last_time = self.last_signal_time.get(symbol)
        if last_time is None:
            return False
        return time.time() - last_time < SIGNAL_COOLDOWN_SECONDS

    def create(self, signal):
        symbol = signal["symbol"]

        if self.has_pending_symbol(symbol) or self.is_in_cooldown(symbol):
            return None

        order_id = str(uuid.uuid4())

        self.pending[order_id] = {
            "signal": signal,
            "expires": time.time() + APPROVAL_TIMEOUT,
            "chat_id": None,
            "message_id": None,
        }

        self.last_signal_time[symbol] = time.time()
        return order_id

    def attach_message(self, order_id, chat_id, message_id):
        if order_id in self.pending:
            self.pending[order_id]["chat_id"] = chat_id
            self.pending[order_id]["message_id"] = message_id

    def approve(self, order_id):
        return self.pending.pop(order_id, None)

    def reject(self, order_id):
        return self.pending.pop(order_id, None)

    def cleanup(self, bot=None):
        now = time.time()

        expired = [
            (oid, data)
            for oid, data in self.pending.items()
            if data["expires"] < now
        ]

        for order_id, data in expired:
            signal = data["signal"]

            if bot and data["chat_id"] and data["message_id"]:
                try:
                    bot.edit_message_text(
                        chat_id=data["chat_id"],
                        message_id=data["message_id"],
                        text=(
                            "승인 시간 만료\n\n"
                            f"종목: {signal['symbol']}\n"
                            f"액션: {signal['action']}\n"
                            f"가격: {signal['price']}\n"
                            f"사유: {signal['reason']}"
                        )
                    )
                except Exception as e:
                    print(f"만료 메시지 수정 실패: {e}")

            print(f"만료됨: {order_id}")
            self.pending.pop(order_id, None)