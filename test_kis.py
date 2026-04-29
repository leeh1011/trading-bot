from utils.kis_api import KISAPI


def test_kis():
    print("🔑 토큰 발급 시도...")

    api = KISAPI()

    token = api.get_token()

    if not token:
        print("❌ 토큰 발급 실패")
        return

    print("✅ 토큰 발급 성공")

    print("📊 삼성전자 가격 조회...")

    data = api.get_price("005930")  # 삼성전자

    print("📦 API 응답:")
    print(data)


if __name__ == "__main__":
    test_kis()
