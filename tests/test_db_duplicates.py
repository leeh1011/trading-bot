import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import pandas as pd

from database.db import (
    init_db,
    save_market_data,
    load_market_data,
)


def test_market_data_duplicate_ignore():
    init_db()

    symbol = "005930"

    row = pd.Series({
        "open": 10000,
        "high": 10100,
        "low": 9900,
        "close": 10050,
        "volume": 12345,
    }, name="2026-05-12 09:00:00")

    save_market_data(symbol, row)
    save_market_data(symbol, row)

    df = load_market_data(symbol, limit=1000)

    duplicated = df[df["datetime"] == "2026-05-12 09:00:00"]

    assert len(duplicated) == 1