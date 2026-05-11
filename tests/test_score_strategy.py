import pandas as pd

from core.strategy import Strategy


def make_market_data():
    rows = []

    price = 100_000

    for i in range(60):
        price += 300

        rows.append({
            "open": price - 100,
            "high": price + 500,
            "low": price - 500,
            "close": price,
            "volume": 10000 + i * 200,
        })

    return pd.DataFrame(rows)


def make_investor_flow():
    rows = []

    for i in range(60):
        rows.append({
            "datetime": f"test-{i}",
            "foreign_buy": 0,
            "foreign_sell": 0,
            "foreign_net": 500000,
            "institution_buy": 0,
            "institution_sell": 0,
            "institution_net": 300000,
        })

    return pd.DataFrame(rows)


def test_score_strategy():
    data = make_market_data()
    flow = make_investor_flow()

    strategy = Strategy()

    signal = strategy.generate_signal(data, "005930", flow)

    print("SIGNAL:", signal)


if __name__ == "__main__":
    test_score_strategy()