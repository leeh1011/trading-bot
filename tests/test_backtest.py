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
    print("최종 자본:", round(result["final_cash"], 2))
    print("총 수익률:", round(result["total_return"] * 100, 2), "%")
    print("완료 거래 수:", result["completed_trades"])
    print("승률:", round(result["win_rate"] * 100, 2), "%")
    print("MDD:", round(result["mdd"] * 100, 2), "%")
    print("평균 수익:", round(result["avg_win"] * 100, 2), "%")
    print("평균 손실:", round(result["avg_loss"] * 100, 2), "%")

    print("\n거래 내역:")
    for trade in result["trades"]:
        print(trade)


if __name__ == "__main__":
    test_backtest()