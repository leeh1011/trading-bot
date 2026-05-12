import time
import traceback
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
    load_investor_flow,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


def is_market_open():
    now = datetime.now()

    # 주말 제외: 월=0, 일=6
    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")
    return "09:00" <= current <= "15:30"


def sync_balance_safe(api, portfolio):
    try:
        balance = api.get_balance()
        synced = portfolio.sync_from_kis_balance(balance)
        logger.info("계좌 동기화 완료:", synced)
        return synced

    except Exception as e:
        log_error("runner.sync_balance_safe", str(e))
        logger.exception("계좌 동기화 실패:", e)
        return None


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
            "reason": f"자동 손절 {pnl_rate:.2%}",
        }

        logger.info(f"자동 손절 실행: {signal}")
        log_signal(signal)

        result = execution.execute(signal)
        logger.info("자동 손절 결과:", result)

    elif pnl_rate >= RISK["take_profit"]:
        signal = {
            "action": "SELL",
            "symbol": symbol,
            "price": current_price,
            "reason": f"자동 익절 {pnl_rate:.2%}",
        }

        logger.info(f"자동 익절 실행: {signal}")
        log_signal(signal)

        result = execution.execute(signal)
        logger.info("자동 익절 결과:", result)


def should_skip_signal(signal, portfolio):
    if not signal:
        return True, "신호 없음"

    action = signal.get("action")
    symbol = signal.get("symbol")

    if action == "BUY" and symbol in portfolio.positions:
        return True, "이미 보유 중이라 BUY 무시"

    if action == "SELL" and symbol not in portfolio.positions:
        return True, "보유 없어서 SELL 무시"

    if action == "BUY":
        price = float(signal["price"])
        cash = float(portfolio.cash)
        amount = cash * TRADE_RATIO
        qty = int(amount // price)

        if qty <= 0:
            return True, "매수 가능 수량 없음 - BUY 알림 차단"

    if action not in ["BUY", "SELL"]:
        return True, f"지원하지 않는 action: {action}"

    return False, ""


def process_symbol(symbol, api, strategy, portfolio, execution, bot):
    logger.info(f"\n[{datetime.now().strftime('%H:%M:%S')}] {symbol} 처리 시작")

    time.sleep(2.0)  # KIS 요청 제한 완화

    df = api.get_minute_chart(symbol)
    flow = api.get_investor_flow(symbol)

    if flow is not None:
        save_investor_flow(symbol, flow)
        logger.info(f"FLOW SAVED: {symbol}")
    else:
        logger.warning(f"외인/기관 데이터 없음: {symbol}")

    if df is None or df.empty or len(df) < 20:
        logger.warning(f"데이터 부족: {symbol}")
        return

    for _, row in df.iterrows():
        save_market_data(symbol, row)

    logger.info(f"MARKET SAVED: {symbol}, rows={len(df)}")

    current_price = float(df.iloc[-1]["close"])

    # 손절/익절 자동 매도
    check_auto_exit(symbol, current_price, portfolio, execution)

    flow_df = load_investor_flow(symbol, limit=20)

    signal = strategy.generate_signal(
        data=df,
        symbol=symbol,
        investor_flow=flow_df,
    )

    skip, reason = should_skip_signal(signal, portfolio)

    if skip:
        logger.info(f"{symbol}: {reason}")
        return

    logger.info(f"신호 발생: {signal}")
    log_signal(signal)

    # 여기서 바로 주문하지 않고 텔레그램 승인 요청
    bot.send_signal(signal)


def run_once(api, strategy, portfolio, execution, approval, bot):
    logger.info("\n5분봉 시장 스캔 중...")

    for symbol in SYMBOLS:
        try:
            process_symbol(
                symbol=symbol,
                api=api,
                strategy=strategy,
                portfolio=portfolio,
                execution=execution,
                bot=bot,
            )

        except Exception:
            error_message = traceback.format_exc()
            log_error("runner.process_symbol", f"{symbol}: {error_message}")
            logger.exception(f"{symbol} 처리 중 오류")
            continue

    approval.cleanup(bot.updater.bot)


def main():
    init_db()

    logger.info("KIS Auto Trading Runner Started")

    api = KISAPI()
    api.get_token()

    strategy = Strategy()
    portfolio = Portfolio()

    sync_balance_safe(api, portfolio)

    execution = ExecutionEngine(portfolio, api)
    approval = ApprovalManager()
    bot = TelegramBot(approval, execution)

    bot.send_message(
        "자동매매 runner 시작\n\n"
        f"감시 종목: {', '.join(SYMBOLS)}\n"
        f"반복 주기: {LOOP_INTERVAL}초"
    )

    last_balance_sync = time.time()

    while True:
        try:
            if not is_market_open():
                logger.info("장중 아님 - 대기 중")
                approval.cleanup(bot.updater.bot)
                time.sleep(60)
                continue

            # 10분마다 잔고 재동기화
            if time.time() - last_balance_sync > 600:
                sync_balance_safe(api, portfolio)
                last_balance_sync = time.time()

            run_once(
                api=api,
                strategy=strategy,
                portfolio=portfolio,
                execution=execution,
                approval=approval,
                bot=bot,
            )

            logger.info("다음 5분 대기...")
            time.sleep(LOOP_INTERVAL)

        except Exception:
            error_message = traceback.format_exc()
            log_error("runner.main_loop", error_message)
            logger.exception("runner 메인 루프 오류")

            try:
                bot.send_message(
                    "runner 메인 루프 오류 발생\n\n"
                    f"{error_message[:1000]}"
                )
            except Exception:
                logger.exception("runner 에러 알림 전송 실패")

            time.sleep(10)

if __name__ == "__main__":
    main()