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
    
    def sync_from_kis_balance(self, balance_data):
        """
        한국투자 잔고 조회 결과로 내부 포트폴리오 동기화
        """
        self.positions = {}

        stocks = balance_data.get("output1", [])
        summary = balance_data.get("output2", [])

        for item in stocks:
            symbol = item.get("pdno")
            qty = int(item.get("hldg_qty", 0))
            avg_price = float(item.get("pchs_avg_pric", 0))

            if qty > 0:
                self.positions[symbol] = {
                    "qty": qty,
                    "avg_price": avg_price
                }

        if summary:
            cash = summary[0].get("dnca_tot_amt")
            if cash is not None:
                self.cash = float(cash)

        return self.status()