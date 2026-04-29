from utils.kis_api import KISAPI
from core.portfolio import Portfolio


def test_sync_balance():
    api = KISAPI()
    api.get_token()

    balance = api.get_balance()

    portfolio = Portfolio()
    synced = portfolio.sync_from_kis_balance(balance)

    print("동기화 결과:")
    print(synced)


if __name__ == "__main__":
    test_sync_balance()