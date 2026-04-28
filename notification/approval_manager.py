import time
import uuid
from config import APPROVAL_TIMEOUT


class ApprovalManager:

    def __init__(self):
        self.pending = {}

    def create(self, signal):
        order_id = str(uuid.uuid4())

        self.pending[order_id] = {
            "signal": signal,
            "expires": time.time() + APPROVAL_TIMEOUT
        }

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
 