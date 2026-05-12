from utils.logger import setup_logger

logger = setup_logger(__name__)


class Portfolio:
    def __init__(self, initial_cash=1_000_000):
        self.cash = initial_cash
        self.positions = {}

    def buy(self, symbol, price, ratio):
        amount = self.cash * ratio
        qty = int(amount // price)

        if qty <= 0:
            ("매수 실패: 금액 부족")
            return None

        cost = qty * price
        self.cash -= cost

        self.positions[symbol] = {
            "qty": qty,
            "avg_price": price
        }

        logger.info(f"매수: {symbol} | 수량: {qty} | 가격: {price}")

        return {
            "symbol": symbol,
            "qty": qty,
            "price": price
        }

    def sell(self, symbol, price):
        if symbol not in self.positions:
            logger.info("매도 실패: 보유 없음")
            return None

        pos = self.positions.pop(symbol)

        revenue = pos["qty"] * price
        self.cash += revenue

        logger.info(f"매도: {symbol} | 수량: {pos['qty']} | 가격: {price}")

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
        self.positions = {}

        stocks = balance_data.get("output1", [])
        summary = balance_data.get("output2", [])

        for item in stocks:
            symbol = item.get("pdno") or item.get("prdt_code")
            qty = int(float(item.get("hldg_qty", 0) or 0))
            avg_price = float(item.get("pchs_avg_pric", 0) or 0)

            if qty > 0 and symbol:
                self.positions[symbol] = {
                    "qty": qty,
                    "avg_price": avg_price
                }

        if summary:
            cash = (
                summary[0].get("dnca_tot_amt")
                or summary[0].get("nass_amt")
                or self.cash
            )
            self.cash = float(cash)

        return self.status()