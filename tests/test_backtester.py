import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

import pandas as pd

from core.strategy import Strategy
from backtest.backtester import Backtester


def make_test_data():
    return pd.DataFrame({
        "close": [
            10000, 9900, 9800, 9700, 9600,
            9500, 9400, 9300, 9200, 9100,
            9000, 8900, 8800, 8700, 8600,
            8500, 8400, 8300, 8200, 8100,
            8000, 8050, 8100, 8200, 8300,
            8400, 8500, 8600, 8700, 8800,
            8900, 9000, 9100, 9200, 9300,
            9400, 9500, 9600, 9700, 9800,
            9900, 10000, 10100, 10200, 10300,
            10400, 10500, 10600, 10700, 10800,
            10900, 11000, 11100, 11200, 11300,
            11400, 11500, 11600, 11700, 11800,
        ],
        "volume": [1000] * 20 + [2000] * 20 + [3000] * 20
    })


def make_test_investor_flow():
    return pd.DataFrame({
        "foreign_net": [1_000_000] * 60,
        "institution_net": [1_000_000] * 60
    })


def test_backtester_runs():
    data = make_test_data()
    investor_flow = make_test_investor_flow()

    strategy = Strategy()
    backtester = Backtester(
        strategy=strategy,
        initial_cash=1_000_000,
        trade_ratio=0.2
    )

    result = backtester.run(
        data=data,
        symbol="005930",
        investor_flow=investor_flow
    )

    backtester.print_summary(result)
    backtester.plot_result(data, result)

    assert "initial_cash" in result
    assert "final_cash" in result
    assert "trades" in result
    assert "equity_curve" in result
    assert result["initial_cash"] == 1_000_000
    assert isinstance(result["trades"], list)
    assert isinstance(result["equity_curve"], list)