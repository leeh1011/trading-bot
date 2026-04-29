from settings import MODE, TRADE_RATIO


class ExecutionEngine:

    def __init__(self, portfolio, kis_api=None):
        self.portfolio = portfolio
        self.kis_api = kis_api

    def execute(self, signal):
        if MODE == "paper":
            return self._paper_execute(signal)

        if MODE == "kis_mock":
            return self._kis_mock_execute(signal)

        raise ValueError(f"Unknown MODE: {MODE}")

    def _paper_execute(self, signal):
        if signal["action"] == "BUY":
            return self.portfolio.buy(
                signal["symbol"],
                signal["price"],
                TRADE_RATIO
            )

        if signal["action"] == "SELL":
            return self.portfolio.sell(
                signal["symbol"],
                signal["price"]
            )

    def _kis_mock_execute(self, signal):
        if self.kis_api is None:
            raise ValueError("KIS API client is required for kis_mock mode")

        action = signal["action"]
        symbol = signal["symbol"]
        price = float(signal["price"])

        if action == "BUY":
            amount = self.portfolio.cash * TRADE_RATIO
            qty = int(amount // price)

            if qty <= 0:
                return {"error": "매수 가능 수량 없음"}

            result = self.kis_api.place_order(
                symbol=symbol,
                qty=qty,
                side="BUY",
                price=0
            )

            balance = self.kis_api.get_balance()
            self.portfolio.sync_from_kis_balance(balance)

            return result

        if action == "SELL":
            position = self.portfolio.positions.get(symbol)

            if not position:
                return {"error": "보유 수량 없음"}

            result = self.kis_api.place_order(
                symbol=symbol,
                qty=position["qty"],
                side="SELL",
                price=0
            )

            balance = self.kis_api.get_balance()
            self.portfolio.sync_from_kis_balance(balance)

            return result