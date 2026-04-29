import time
import uuid
from settings import APPROVAL_TIMEOUT, SIGNAL_COOLDOWN_SECONDS


class ApprovalManager:

    def __init__(self):
        self.pending = {}
        self.last_signal_time = {}

    def has_pending_symbol(self, symbol):
        for item in self.pending.values():
            if item["signal"]["symbol"] == symbol:
                return True
        return False

    def is_in_cooldown(self, symbol):
        last_time = self.last_signal_time.get(symbol)

        if last_time is None:
            return False

        return time.time() - last_time < SIGNAL_COOLDOWN_SECONDS

    def create(self, signal):
        symbol = signal["symbol"]

        if self.has_pending_symbol(symbol):
            return None

        if self.is_in_cooldown(symbol):
            return None

        order_id = str(uuid.uuid4())

        self.pending[order_id] = {
            "signal": signal,
            "expires": time.time() + APPROVAL_TIMEOUT
        }

        self.last_signal_time[symbol] = time.time()

        return order_id

    def approve(self, order_id):
        return self.pending.pop(order_id, None)

    def reject(self, order_id):
        return self.pending.pop(order_id, None)

    def cleanup(self):
        now = time.time()

        expired = [
            oid for oid, data in self.pending.items()
            if data["expires"] < now
        ]

        for oid in expired:
            print(f"⏰ 만료됨: {oid}")
            self.pending.pop(oid)