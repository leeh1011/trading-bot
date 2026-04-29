from database.db import init_db, log_signal, log_order, log_approval, log_error


def test_db():
    init_db()

    signal = {
        "symbol": "005930",
        "action": "BUY",
        "price": 70000,
        "reason": "test signal"
    }

    log_signal(signal)
    log_order("005930", "BUY", 1, 70000, "SUCCESS", {"rt_cd": "0"})
    log_approval("test-order-id", "005930", "BUY", "APPROVE")
    log_error("test", "test error message")

    print("DB 테스트 완료")


if __name__ == "__main__":
    test_db()