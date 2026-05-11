import  matplotlib.pyplot as plt

class Backtester:
    def __init__(self, strategy, initial_cash=1_000_000, trade_ratio=0.2):
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.trade_ratio = trade_ratio
        self.position = None
        self.trades = []
        self.equity_curve = []

    def run(self, data, symbol, investor_flow=None):
        for i in range(50, len(data)):
            window = data.iloc[:i + 1].copy()

            flow_window = None
            if investor_flow is not None:
                flow_window = investor_flow.iloc[:i + 1].copy()

            latest = window.iloc[-1]
            close = float(latest.get("close"))

            if close is None:
                continue

            signal = self.strategy.generate_signal(
                window,
                symbol=symbol,
                investor_flow=flow_window
            )

            action = "HOLD"
            reason = ""

            if signal is not None:
                action = signal.get("action", "HOLD")
                reason = signal.get("reason", "")

            position_value = 0
            if self.position is not None:
                position_value = self.position["quantity"] * close

            total_value = self.cash + position_value

            if action == "BUY" and self.position is not None:
                action = "HOLD"
                reason = "이미 보유 중이라 추가 매수 안 함"

            if action == "SELL" and self.position is None:
                action = "HOLD"
                reason = "보유 수량이 없어 매도 안 함"

            self.equity_curve.append({
                "time": latest.name,
                "symbol": symbol,
                "close": close,
                "cash": self.cash,
                "position_value": position_value,
                "total_value": total_value,
                "action": action,
                "reason": reason
            })

            # 매수
            if action == "BUY" and self.position is None:
                buy_amount = self.cash * self.trade_ratio
                quantity = int(buy_amount // close)

                if quantity <= 0:
                    continue

                cost = quantity * close
                self.cash -= cost

                self.position = {
                    "symbol": symbol,
                    "entry_price": close,
                    "quantity": quantity,
                    "entry_time": latest.name,
                    "entry_reason": reason
                }

                self.trades.append({
                    "type": "BUY",
                    "time": latest.name,
                    "symbol": symbol,
                    "price": close,
                    "quantity": quantity,
                    "amount": cost,
                    "reason": reason,
                    "cash_after": self.cash
                })

            # 매도
            elif action == "SELL" and self.position is not None:
                quantity = self.position["quantity"]
                entry_price = self.position["entry_price"]
                entry_time = self.position["entry_time"]

                sell_amount = quantity * close
                self.cash += sell_amount

                profit = (close - entry_price) * quantity
                profit_rate = ((close - entry_price) / entry_price) * 100

                self.trades.append({
                    "type": "SELL",
                    "time": latest.name,
                    "symbol": symbol,
                    "price": close,
                    "quantity": quantity,
                    "amount": sell_amount,
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "profit": profit,
                    "profit_rate": profit_rate,
                    "buy_reason": self.position["entry_reason"],
                    "sell_reason": reason,
                    "cash_after": self.cash
                })

                self.position = None

        # 마지막까지 보유 중이면 마지막 종가로 강제 청산
        if self.position is not None:
            last = data.iloc[-1]
            close = last.get("close")

            quantity = self.position["quantity"]
            entry_price = self.position["entry_price"]

            sell_amount = quantity * close
            self.cash += sell_amount

            profit = (close - entry_price) * quantity
            profit_rate = ((close - entry_price) / entry_price) * 100

            self.trades.append({
                "type": "FORCED_SELL",
                "time": last.name,
                "symbol": symbol,
                "price": close,
                "quantity": quantity,
                "amount": sell_amount,
                "entry_price": entry_price,
                "profit": profit,
                "profit_rate": profit_rate,
                "buy_reason": self.position["entry_reason"],
                "sell_reason": "백테스트 종료로 강제 청산",
                "cash_after": self.cash
            })

            self.position = None

        return self.result()

    def result(self):
        final_value = self.cash
        total_return = ((final_value - self.initial_cash) / self.initial_cash) * 100

        sell_trades = [
            trade for trade in self.trades
            if trade["type"] in ["SELL", "FORCED_SELL"]
        ]

        win_trades = [
            trade for trade in sell_trades
            if trade.get("profit", 0) > 0
        ]

        win_rate = 0
        if len(sell_trades) > 0:
            win_rate = len(win_trades) / len(sell_trades) * 100

        total_profit = sum(trade.get("profit", 0) for trade in sell_trades)

        return {
            "strategy": self.strategy.__class__.__name__,
            "initial_cash": self.initial_cash,
            "final_cash": self.cash,
            "total_profit": total_profit,
            "total_return": total_return,
            "trade_count": len(self.trades),
            "completed_trade_count": len(sell_trades),
            "win_count": len(win_trades),
            "win_rate": win_rate,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }
    
    def print_summary(self, result):
        print("========== 백테스트 결과 ==========")
        print(f"초기 자금: {result['initial_cash']:,.0f}원")
        print(f"최종 자금: {result['final_cash']:,.0f}원")
        print(f"총 수익: {result['total_profit']:,.0f}원")
        print(f"총 수익률: {result['total_return']:.2f}%")
        print(f"전체 거래 수: {result['trade_count']}")
        print(f"완료 거래 수: {result['completed_trade_count']}")
        print(f"승리 거래 수: {result['win_count']}")
        print(f"승률: {result['win_rate']:.2f}%")

        print("\n========== 거래 내역 ==========")
        for trade in result["trades"]:
            print(trade)

    def plot_result(self, data, result):
        plt.figure(figsize=(14, 7))

        plt.plot(data.index, data["close"], label="Close Price")

        for trade in result["trades"]:
            if trade["type"] == "BUY":
                plt.scatter(
                    trade["time"],
                    trade["price"],
                    marker="^",
                    s=120,
                    label="BUY"
                )

            elif trade["type"] in ["SELL", "FORCED_SELL"]:
                plt.scatter(
                    trade["time"],
                    trade["price"],
                    marker="v",
                    s=120,
                    label=trade["type"]
                )

        plt.title("Backtest Result")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.show()