class Portfolio:
    def __init__(self, initial_cash=1_000_000):
        self.cash = initial_cash
        self.positions = {}

    def buy(self, symbol, price, ratio):
        amount = self.cash * ratio
        qty = int(amount // price)

        if qty <= 0:
            print("❌ 매수 실패: 금액 부족")
            return None

        cost = qty * price
        self.cash -= cost

        self.positions[symbol] = {
            "qty": qty,
            "avg_price": price
        }

        print(f"✅ 매수: {symbol} | 수량: {qty} | 가격: {price}")

        return {
            "symbol": symbol,
            "qty": qty,
            "price": price
        }

    def sell(self, symbol, price):
        if symbol not in self.positions:
            print("❌ 매도 실패: 보유 없음")
            return None

        pos = self.positions.pop(symbol)

        revenue = pos["qty"] * price
        self.cash += revenue

        print(f"✅ 매도: {symbol} | 수량: {pos['qty']} | 가격: {price}")

        return {
            "symbol": symbol,
            "qty": pos["qty"],
            "price": price
        }

    def status(self):
        return {
            "cash": self.cash,
            "positions": self.positions
        }
