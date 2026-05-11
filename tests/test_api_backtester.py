import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from core.strategy import Strategy
from backtest.backtester import Backtester
from utils.kis_api import KISAPI


def test_api_backtester_runs():
    symbol = "005930"

    api = KISAPI()

    data = api.get_minute_chart(symbol)

    assert data is not None
    assert not data.empty
    assert len(data) >= 50

    strategy = Strategy()
    backtester = Backtester(
        strategy=strategy,
        initial_cash=1_000_000,
        trade_ratio=0.2
    )

    result = backtester.run(
        data=data,
        symbol=symbol,
        investor_flow=None
    )

    backtester.print_summary(result)
    backtester.plot_result(data, result)
    backtester.plot_equity_curve(result)

    assert "total_return" in result
    assert "trades" in result
    assert "equity_curve" in result