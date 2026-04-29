from utils.kis_api import KISAPI


def test_minute_chart():
    api = KISAPI()
    api.get_token()

    df = api.get_minute_chart("005930")

    print(df.tail())
    print("데이터 개수:", len(df))


if __name__ == "__main__":
    test_minute_chart()