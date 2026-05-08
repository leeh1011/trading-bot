class Backtester:
    def __init__(self, strategy, initial_cash=1_000_000, trade_ratio=0.2):
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.trade_ratio = trade_ratio
        self.position = None
        self.trades = []
        self.equity_curve = []

    def run(self, data, symbol):
        for i in range(50, len(data)):
            window = data.iloc[:i + 1].copy()
            signal = self.strategy.generate_signal(window, symbol)
            price = float(window.iloc[-1]["close"])

            equity = self._calculate_equity(price)
            self.equity_curve.append(equity)

            if signal is None:
                continue

            if signal["action"] == "BUY" and self.position is None:
                self._buy(price)

            elif signal["action"] == "SELL" and self.position is not None:
                self._sell(price)

        final_price = float(data.iloc[-1]["close"])

        if self.position is not None:
            self._sell(final_price)

        return self._result()

    def _buy(self, price):
        amount = self.cash * self.trade_ratio
        qty = int(amount // price)

        if qty <= 0:
            return

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

    def _sell(self, price):
        qty = self.position["qty"]
        avg_price = self.position["avg_price"]

        pnl = (price - avg_price) * qty
        pnl_rate = (price - avg_price) / avg_price

        self.cash += qty * price

        self.trades.append({
            "type": "SELL",
            "price": price,
            "qty": qty,
            "cash": self.cash,
            "pnl": pnl,
            "pnl_rate": pnl_rate
        })

        self.position = None

    def _calculate_equity(self, current_price):
        equity = self.cash

        if self.position is not None:
            equity += self.position["qty"] * current_price

        return equity

    def _calculate_mdd(self):
        if not self.equity_curve:
            return 0

        peak = self.equity_curve[0]
        max_drawdown = 0

        for equity in self.equity_curve:
            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak

            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def _result(self):
        sells = [t for t in self.trades if t["type"] == "SELL"]

        wins = [t for t in sells if t["pnl"] > 0]
        losses = [t for t in sells if t["pnl"] <= 0]

        total_return = (self.cash - self.initial_cash) / self.initial_cash
        win_rate = len(wins) / len(sells) if sells else 0

        avg_win = sum(t["pnl_rate"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pnl_rate"] for t in losses) / len(losses) if losses else 0

        return {
            "initial_cash": self.initial_cash,
            "final_cash": self.cash,
            "total_return": total_return,
            "trade_count": len(self.trades),
            "completed_trades": len(sells),
            "win_rate": win_rate,
            "mdd": self._calculate_mdd(),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }