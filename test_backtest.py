import pandas as pd
import random

from core.strategy import Strategy
from backtest.backtester import Backtester


def generate_fake_data():
    price = 100_000
    rows = []

    for _ in range(200):
        price += random.randint(-1500, 1500)

        rows.append({
            "open": price,
            "high": price + random.randint(0, 1000),
            "low": price - random.randint(0, 1000),
            "close": price,
            "volume": random.randint(10000, 100000),
        })

    return pd.DataFrame(rows)


def test_backtest():
    data = generate_fake_data()

    strategy = Strategy()
    backtester = Backtester(strategy)

    result = backtester.run(data, "005930")

    print("초기 자본:", result["initial_cash"])
    print("최종 자본:", result["final_cash"])
    print("수익률:", round(result["total_return"] * 100, 2), "%")
    print("거래 횟수:", result["trade_count"])

    print("\n거래 내역:")
    for trade in result["trades"]:
        print(trade)


if __name__ == "__main__":
    test_backtest()