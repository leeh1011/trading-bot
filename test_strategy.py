import pandas as pd
import random

from core.strategy import Strategy
strategy = Strategy()

def generate_fake_data():
    return pd.DataFrame({
        "close": [random.randint(100, 200) for _ in range(50)]
    })


def test_strategy():
    strategy = Strategy()
    data = generate_fake_data()

    signal = strategy.generate_signal(data, "TEST")

    if signal:
        print("신호 발생:", signal)
    else:
        print("신호 없음")


if __name__ == "__main__":
    test_strategy()
