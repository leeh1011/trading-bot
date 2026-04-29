class Backtester:
    def __init__(self, strategy, initial_cash=1_000_000, trade_ratio=0.2):
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.trade_ratio = trade_ratio
        self.position = None
        self.trades = []

    def run(self, data, symbol):
        for i in range(50, len(data)):
            window = data.iloc[:i + 1].copy()
            signal = self.strategy.generate_signal(window, symbol)

            price = float(window.iloc[-1]["close"])

            if signal is None:
                continue

            if signal["action"] == "BUY" and self.position is None:
                amount = self.cash * self.trade_ratio
                qty = int(amount // price)

                if qty <= 0:
                    continue

                self.cash -= qty * price
                self.position = {
                    "qty": qty,
                    "avg_price": price
                }

                self.trades.append({
                    "type": "BUY",
                    "price": price,
                    "qty": qty,
                    "cash": self.cash
                })

            elif signal["action"] == "SELL" and self.position is not None:
                qty = self.position["qty"]
                self.cash += qty * price

                self.trades.append({
                    "type": "SELL",
                    "price": price,
                    "qty": qty,
                    "cash": self.cash
                })

                self.position = None

        final_price = float(data.iloc[-1]["close"])

        if self.position is not None:
            self.cash += self.position["qty"] * final_price
            self.position = None

        total_return = (self.cash - self.initial_cash) / self.initial_cash

        return {
            "initial_cash": self.initial_cash,
            "final_cash": self.cash,
            "total_return": total_return,
            "trade_count": len(self.trades),
            "trades": self.trades
        }