import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from core.strategies.score_v1 import ScoreV1Strategy
from backtest.backtester import Backtester
from database.db import load_market_data, load_investor_flow, save_backtest_result

def test_db_backtester_runs():
    symbol = "005930"

    data = load_market_data(symbol, limit=200)
    investor_flow = load_investor_flow(symbol, limit=200)

    if(len(data)<50):
        print("market rows:", len(data))
        print("flow rows:", len(investor_flow))

    assert len(data) >= 10

    strategy = ScoreV1Strategy()

    backtester = Backtester(
        strategy=strategy,
        initial_cash=1_000_000,
        trade_ratio=0.2
    )

    result = backtester.run(
        data=data,
        symbol=symbol,
        investor_flow=investor_flow
    )

    print("strategy:", result["strategy"])
    backtester.print_summary(result)

    save_backtest_result(result, symbol)