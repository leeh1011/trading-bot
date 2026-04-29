from utils.kis_api import KISAPI


def test_balance():
    api = KISAPI()
    api.get_token()

    data = api.get_balance()

    print(data)


if __name__ == "__main__":
    test_balance()