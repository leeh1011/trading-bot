from core.strategy import Strategy
from backtest.backtester import Backtester
from database.db import load_market_data, load_investor_flow


def test_backtest_v3():
    symbol = "005930"

    market_df = load_market_data(symbol, limit=500)
    flow_df = load_investor_flow(symbol, limit=500)

    if market_df.empty:
        print("시장 데이터 없음")
        return

    if flow_df.empty:
        print("외인/기관 데이터 없음")
        flow_df = None

    strategy = Strategy()
    backtester = Backtester(strategy, initial_cash=10_000_000, trade_ratio=0.2)

    result = backtester.run(
        data=market_df,
        symbol=symbol,
        investor_flow=flow_df
    )

    print("market rows:", len(market_df))
    print("flow rows:", 0 if flow_df is None else len(flow_df))

    print("초기 자본:", result["initial_cash"])
    print("최종 자본:", round(result["final_cash"], 2))
    print("총 수익률:", round(result["total_return"] * 100, 2), "%")
    print("완료 거래 수:", result["completed_trades"])
    print("승률:", round(result["win_rate"] * 100, 2), "%")
    print("MDD:", round(result["mdd"] * 100, 2), "%")
    print("평균 수익:", round(result["avg_win"] * 100, 2), "%")
    print("평균 손실:", round(result["avg_loss"] * 100, 2), "%")


if __name__ == "__main__":
    test_backtest_v3()