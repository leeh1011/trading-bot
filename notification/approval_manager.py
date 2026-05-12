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

    def cleanup(self, bot):
        now = time.time()

        expired_ids = []

        for order_id, order in self.pending.items():
            if now - order["created_at"] > APPROVAL_TIMEOUT:
                expired_ids.append(order_id)

        for order_id in expired_ids:
            order = self.pending.pop(order_id)

            chat_id = order.get("chat_id")
            message_id = order.get("message_id")
            signal = order.get("signal", {})

            if chat_id and message_id:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=(
                            "신호 만료됨\n\n"
                            f"종목: {signal.get('symbol')}\n"
                            f"구분: {signal.get('action')}\n"
                            f"가격: {signal.get('price')}\n"
                            f"이유: {signal.get('reason')}"
                        )
                    )
                except Exception:
                    pass