from utils.kis_api import KISAPI


def test_order():
    api = KISAPI()

    result = api.place_order(
        symbol="005930",
        qty=1,
        side="BUY",
        price=0
    )

    print("ORDER IS NONE?", result is None)
    print("ORDER RESULT:", result)


if __name__ == "__main__":
    confirm = input("삼성전자 1주 모의 매수 주문을 보낼까요? YES 입력: ")

    if confirm == "YES":
        test_order()
    else:
        print("취소됨")