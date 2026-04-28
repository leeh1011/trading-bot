from config import MODE, TRADE_RATIO


class ExecutionEngine:

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def execute(self, signal):
        """
        매매 실행
        """
        if MODE == "paper":
            return self._paper_execute(signal)
        else:
            raise NotImplementedError("Real trading not implemented yet")

    def _paper_execute(self, signal):
        action = signal["action"]

        if action == "BUY":
            return self.portfolio.buy(
                signal["symbol"],
                signal["price"],
                TRADE_RATIO
            )

        elif action == "SELL":
            return self.portfolio.sell(
                signal["symbol"],
                signal["price"]
            )
