from core.portfolio import Portfolio
from core.execution import ExecutionEngine


def test_execution():
    portfolio = Portfolio()
    execution = ExecutionEngine(portfolio)

    # 테스트 BUY
    buy_signal = {
        "action": "BUY",
        "symbol": "TEST",
        "price": 100
    }

    execution.execute(buy_signal)

    # 테스트 SELL
    sell_signal = {
        "action": "SELL",
        "symbol": "TEST",
        "price": 110
    }

    execution.execute(sell_signal)

    print("현재 상태:", portfolio.status())


if __name__ == "__main__":
    test_execution()
