import pandas as pd
import random

from utils.indicators import calculate_rsi, moving_average


def generate_fake_data():
    return pd.DataFrame({
        "close": [random.randint(100, 200) for _ in range(50)]
    })


def test_indicators():
    data = generate_fake_data()

    rsi = calculate_rsi(data)
    ma = moving_average(data)

    print("RSI 마지막 값:", rsi.iloc[-1])
    print("MA 마지막 값:", ma.iloc[-1])


if __name__ == "__main__":
    test_indicators()
