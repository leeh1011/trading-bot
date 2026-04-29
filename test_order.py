from utils.kis_api import KISAPI


def test_order():
    api = KISAPI()
    api.get_token()

    # 매우 중요: 모의투자 테스트용 1주 시장가 매수
    result = api.place_order(
        symbol="005930",
        qty=1,
        side="BUY",
        price=0
    )

    print(result)


if __name__ == "__main__":
    confirm = input("삼성전자 1주 모의 매수 주문을 보낼까요? YES 입력: ")

    if confirm == "YES":
        test_order()
    else:
        print("취소됨")