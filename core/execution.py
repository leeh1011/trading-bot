from settings import MODE, TRADE_RATIO
from database.db import log_order, log_error


class ExecutionEngine:
    def __init__(self, portfolio, kis_api=None):
        self.portfolio = portfolio
        self.kis_api = kis_api

    def execute(self, signal):
        try:
            if MODE == "paper":
                return self._paper_execute(signal)

            if MODE == "kis_mock":
                return self._kis_mock_execute(signal)

            return {"error": f"Unknown MODE: {MODE}"}

        except Exception as e:
            log_error("ExecutionEngine.execute", str(e))
            return {"error": str(e)}

    def _paper_execute(self, signal):
        action = signal["action"]
        symbol = signal["symbol"]
        price = float(signal["price"])

        if action == "BUY":
            result = self.portfolio.buy(symbol, price, TRADE_RATIO)

            if result:
                log_order(symbol, action, result["qty"], price, "PAPER_SUCCESS", result)

            return result or {"error": "paper buy failed"}

        if action == "SELL":
            result = self.portfolio.sell(symbol, price)

            if result:
                log_order(symbol, action, result["qty"], price, "PAPER_SUCCESS", result)

            return result or {"error": "paper sell failed"}

        return {"error": f"Unknown action: {action}"}

    def _kis_mock_execute(self, signal):
        if self.kis_api is None:
            return {"error": "KIS API client is required"}

        action = signal["action"]
        symbol = signal["symbol"]
        price = float(signal["price"])

        if action == "BUY":
            return self._kis_buy(symbol, price)

        if action == "SELL":
            return self._kis_sell(symbol, price)

        return {"error": f"Unknown action: {action}"}

    def _kis_buy(self, symbol, price):
        cash = float(self.portfolio.cash)
        amount = cash * TRADE_RATIO
        qty = int(amount // price)

        if qty <= 0:
            return {"error": "매수 가능 수량 없음"}

        result = self.kis_api.place_order(
            symbol=symbol,
            qty=qty,
            side="BUY",
            price=0
        )

        success = result.get("rt_cd") == "0"
        status = "KIS_BUY_SUCCESS" if success else "KIS_BUY_FAILED"

        log_order(symbol, "BUY", qty, price, status, result)

        if success:
            self._sync_balance()

        return result

    def _kis_sell(self, symbol, price):
        if symbol not in self.portfolio.positions:
            return {"error": "보유수량 없음"}

        qty = int(self.portfolio.positions[symbol]["qty"])

        if qty <= 0:
            return {"error": "매도 가능 수량 없음"}

        result = self.kis_api.place_order(
            symbol=symbol,
            qty=qty,
            side="SELL",
            price=0
        )

        success = result.get("rt_cd") == "0"
        status = "KIS_SELL_SUCCESS" if success else "KIS_SELL_FAILED"

        log_order(symbol, "SELL", qty, price, status, result)

        if success:
            self._sync_balance()

        return result

    def _sync_balance(self):
        try:
            balance = self.kis_api.get_balance()
            self.portfolio.sync_from_kis_balance(balance)
        except Exception as e:
            log_error("ExecutionEngine._sync_balance", str(e))