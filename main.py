import time
from datetime import datetime

from settings import SYMBOLS, LOOP_INTERVAL, RISK, TRADE_RATIO
from utils.kis_api import KISAPI
from core.strategy import Strategy
from core.portfolio import Portfolio
from core.execution import ExecutionEngine
from notification.approval_manager import ApprovalManager
from notification.telegram_bot import TelegramBot
from database.db import (
    init_db,
    log_signal,
    log_error,
    save_market_data,
    save_investor_flow,
    load_investor_flow
)


def is_market_open():
    now = datetime.now()

    # 주말 제외: 월=0, 일=6
    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")
    return "09:00" <= current <= "15:30"


def check_auto_exit(symbol, current_price, portfolio, execution):
    if symbol not in portfolio.positions:
        return

    avg_price = float(portfolio.positions[symbol]["avg_price"])
    pnl_rate = (current_price - avg_price) / avg_price

    if pnl_rate <= RISK["stop_loss"]:
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "price": current_price,
            "reason": f"자동 손절 {pnl_rate:.2%}"
        }
        print(f"자동 손절 실행: {signal}")
        result = execution.execute(signal)
        print("자동 손절 결과:", result)

    elif pnl_rate >= RISK["take_profit"]:
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "price": current_price,
            "reason": f"자동 익절 {pnl_rate:.2%}"
        }
        print(f"자동 익절 실행: {signal}")
        result = execution.execute(signal)
        print("자동 익절 결과:", result)


def sync_balance_safe(api, portfolio):
    try:
        balance = api.get_balance()
        synced = portfolio.sync_from_kis_balance(balance)
        print("계좌 동기화 완료:", synced)
        return synced
    except Exception as e:
        log_error("main.sync_balance_safe", str(e))
        print("계좌 동기화 실패:", e)
        return None


def main():
    init_db()

    print("KIS Auto Trading Bot Started")

    api = KISAPI()
    api.get_token()

    strategy = Strategy()
    portfolio = Portfolio()

    sync_balance_safe(api, portfolio)

    execution = ExecutionEngine(portfolio, api)
    approval = ApprovalManager()
    bot = TelegramBot(approval, execution)

    last_balance_sync = time.time()

    while True:
        try:
            # if not is_market_open():
            #     print("장중 아님 - 대기 중")
            #     approval.cleanup(bot.updater.bot)
            #     time.sleep(60)
            #     continue

            print("\n5분봉 시장 스캔 중...")

            # 10분마다 잔고 재동기화
            if time.time() - last_balance_sync > 600:
                sync_balance_safe(api, portfolio)
                last_balance_sync = time.time()

            for symbol in SYMBOLS:
                try:
                    time.sleep(2.0)  # KIS 초당 요청 제한 완화

                    df = api.get_minute_chart(symbol)

                    flow = api.get_investor_flow(symbol)

                    if flow is not None:
                        print("FLOW FETCHED:", symbol, flow)
                        save_investor_flow(symbol, flow)
                        print("FLOW SAVED:", symbol)
                    else:
                        print(f"외인/기관 데이터 없음: {symbol}")

                    if df.empty or len(df) < 20:
                        print(f"데이터 부족: {symbol}")
                        continue

                    for _, row in df.iterrows():
                        save_market_data(symbol, row)

                    print(f"MARKET SAVED: {symbol}, rows={len(df)}")

                    current_price = float(df.iloc[-1]["close"])

                    # 손절/익절 자동 매도
                    check_auto_exit(symbol, current_price, portfolio, execution)

                    flow_df = load_investor_flow(symbol, limit=20)
                    signal = strategy.generate_signal(df, symbol, flow_df)

                    if not signal:
                        print(f"신호 없음: {symbol}")
                        continue

                    if signal["action"] == "BUY" and symbol in portfolio.positions:
                        print(f"이미 보유 중이라 BUY 무시: {symbol}")
                        continue

                    if signal["action"] == "SELL" and symbol not in portfolio.positions:
                        print(f"보유 없어서 SELL 무시: {symbol}")
                        continue

                    if signal["action"] == "BUY":
                        cash = float(portfolio.cash)
                        amount = cash * TRADE_RATIO
                        price = float(signal["price"])
                        qty = int(amount // price)

                        if qty <= 0:
                            print(f"매수 가능 수량 없음 - BUY 알림 차단: {symbol}")
                            continue

                    print(f"신호 발생: {signal}")
                    log_signal(signal)

                    bot.send_signal(signal)

                except Exception as e:
                    log_error("main.symbol_loop", f"{symbol}: {e}")
                    print(f"{symbol} 처리 중 오류:", e)
                    continue

            approval.cleanup(bot.updater.bot)

            print("다음 5분 대기...")
            time.sleep(LOOP_INTERVAL)

        except Exception as e:
            log_error("main.loop", str(e))
            print("메인 루프 오류:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()