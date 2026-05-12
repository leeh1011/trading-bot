import os
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
from settings import TELEGRAM_TOKEN, CHAT_ID, SYMBOL_NAMES
from database.db import log_approval,DB_NAME
from telegram.ext import CommandHandler
from telegram.error import BadRequest
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TelegramBot:

    def __init__(self, approval_manager, execution_engine):
        self.approval_manager = approval_manager
        self.execution_engine = execution_engine
        self.paused=False

        self.updater = Updater(
            token=TELEGRAM_TOKEN,
            request_kwargs={
                "connect_timeout": 30,
                "read_timeout": 30,
            },
            use_context=True
        )
        
        dp = self.updater.dispatcher

        dp.add_handler(CommandHandler("stop", self.stop_handler))
        dp.add_handler(CommandHandler("status", self.status_handler))
        dp.add_handler(CommandHandler("pnl", self.pnl_handler))
        dp.add_handler(CommandHandler("errors", self.errors_handler))
        dp.add_handler(CommandHandler("sync", self.sync_handler))
        dp.add_handler(CommandHandler("help", self.help_handler))
        dp.add_handler(CommandHandler("pause",self.pause_handler))
        dp.add_handler(CommandHandler("resume",self.resume_handler))

        dp.add_handler(CallbackQueryHandler(self.button_handler))

        try:
            self.updater.start_polling(
                timeout=10,
                read_latency=2,
                bootstrap_retries=3
            )
            logger.info("Telegram Bot 실행됨")
        except Exception as e:
            logger.exception(f"Telegram Bot 연결 실패: {e}")
            raise

    def send_signal(self, signal):
        order_id = self.approval_manager.create(signal)

        if order_id is None:
            logger.warning(f"중복/쿨다운으로 신호 무시: {signal['symbol']}")
            return
        if self.paused:
            logger.info(f"봇 일시정지 상태 - 신호 알림 차단: {signal['symbol']}")
            return

        keyboard = [
            [
                InlineKeyboardButton("승인", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton("거절", callback_data=f"reject_{order_id}")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        portfolio = self.execution_engine.portfolio
        symbol = signal["symbol"]

        if symbol in portfolio.positions:
            position = portfolio.positions[symbol]
            holding_text = (
                f"보유 중\n"
                f"보유 수량: {position['qty']}주\n"
                f"평균 단가: {position['avg_price']:,.0f}원"
            )
        else:
            holding_text = "미보유"

        name = SYMBOL_NAMES.get(symbol, symbol)

        text = f"""
        신호 발생

        종목: {name}({symbol})
        구분: {signal['action']}
        가격: {signal['price']:,.0f}원
        보유 상태: {holding_text}

        이유:
        {signal['reason']}
        """

        message = self.updater.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            reply_markup=reply_markup
        )

        self.approval_manager.attach_message(
            order_id=order_id,
            chat_id=CHAT_ID,
            message_id=message.message_id
        )

    def safe_edit_message(self, query, text):
        try:
            query.edit_message_text(text)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                return
            raise

    def button_handler(self, update, context):
        query = update.callback_query
        data = query.data

        action, order_id = data.split("_")

        if action == "approve":
            order = self.approval_manager.approve(order_id)

            if order:
                signal = order["signal"]
                log_approval(order_id, signal["symbol"], signal["action"], "APPROVE")
                try:
                    result = self.execution_engine.execute(signal)
                    self.safe_edit_message(query,f"실행됨: {result}")
                except Exception as e:
                    self.safe_edit_message(query,f"실행 오류: {e}")
            else:
                self.safe_edit_message(query,"만료된 주문")

        elif action == "reject":
            order = self.approval_manager.reject(order_id)

            if order:
                signal = order["signal"]
                log_approval(order_id, signal["symbol"], signal["action"], "REJECT")

            self.safe_edit_message(query, "거절됨")

        query.answer()
 
    def status_handler(self, update, context):
        positions = self.execution_engine.portfolio.positions
        cash = self.execution_engine.portfolio.cash

        if positions:
            pos_text = "\n".join(
                 [
                    f"{SYMBOL_NAMES.get(code, code)}({code}): {info['qty']}주 @ {info['avg_price']:,.0f}원"
                    for code, info in positions.items()
                ]
            )
        else:
            pos_text = "없음"

        text = f"""
        Bot Status

        실행중: 정상
        일시정지: {'예' if self.paused else '아니오'}
        현금: {cash:,.0f}원

        보유 종목:
        {pos_text}
        """

        update.message.reply_text(text)

    def pnl_handler(self, update, context):
        portfolio = self.execution_engine.portfolio
        kis_api = self.execution_engine.kis_api

        cash = float(portfolio.cash)
        positions = portfolio.positions

        target_symbol = None

        if context.args:
            target_symbol = context.args[0].strip()

            if target_symbol not in positions:
                update.message.reply_text(f"{target_symbol} 보유 중이 아닙니다.")
                return

            positions = {
                target_symbol: positions[target_symbol]
            }

        total_stock_value = 0
        total_profit = 0
        lines = []

        if not positions:
            text = f"""
        손익 현황

        현금: {cash:,.0f}원
        보유 종목: 없음

        총 자산: {cash:,.0f}원
        """
            update.message.reply_text(text)
            return

        for code, info in positions.items():
            qty = int(info["qty"])
            avg = float(info["avg_price"])

            price_data = kis_api.get_price(code)
            output = price_data.get("output", {})
            current_price = float(output.get("stck_prpr", avg))

            value = qty * current_price
            profit = (current_price - avg) * qty
            profit_rate = ((current_price - avg) / avg) * 100 if avg > 0 else 0

            total_stock_value += value
            total_profit += profit
            
            name = SYMBOL_NAMES.get(code, code)

            lines.append(
                f"{name}({code}): {qty}주\n"
                f"평균가: {avg:,.0f}원\n"
                f"현재가: {current_price:,.0f}원\n"
                f"평가금액: {value:,.0f}원\n"
                f"손익: {profit:,.0f}원 ({profit_rate:.2f}%)"
            )

        total_value = cash + total_stock_value


        title = "손익 현황"
        if target_symbol:
            title = f"손익 현황 - {target_symbol}"

        text = f"""
        {title}

        현금: {cash:,.0f}원

        보유 종목:
        {chr(10).join(lines)}

        주식 평가금액: {total_stock_value:,.0f}원
        총 평가손익: {total_profit:,.0f}원
        총 자산: {total_value:,.0f}원
        """

        update.message.reply_text(text)
    
    def stop_handler(self, update, context):
        update.message.reply_text("봇 종료합니다.")
        self.send_message("자동매매 runner 종료")
        os._exit(0)

    def errors_handler(self, update, context):
        try:
            limit = 5

            if context.args:
                try:
                    limit = int(context.args[0])
                    limit = max(1, min(limit, 20))
                except ValueError:
                    update.message.reply_text("사용법: /errors 5")
                    return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            cur.execute("""
            SELECT created_at, location, message
            FROM errors
            ORDER BY id DESC
            LIMIT ?
            """, (limit,))

            rows = cur.fetchall()
            conn.close()

            if not rows:
                update.message.reply_text("최근 에러 없음")
                return

            lines = []

            for created_at, location, message in rows:
                msg = str(message)
                if len(msg) > 300:
                    msg = msg[:300] + "..."

                lines.append(
                    f"[{created_at}]\n"
                    f"{location}\n"
                    f"{msg}"
                )

            text = "\n\n".join(lines)

            update.message.reply_text(
                f"최근 에러 로그 {len(rows)}개\n\n{text}"
            )

        except Exception as e:
            update.message.reply_text(f"errors 조회 실패: {e}")


    def sync_handler(self, update, context):
        try:
            balance = self.execution_engine.kis_api.get_balance()

            synced = self.execution_engine.portfolio.sync_from_kis_balance(
                balance
            )

            update.message.reply_text(
                f"잔고 동기화 완료\n\n{synced}"
            )

        except Exception as e:
            update.message.reply_text(f"sync 실패: {e}")


    def help_handler(self, update, context):
        text = """
        사용 가능한 명령어

    /status
    → 현재 봇 상태

    /pnl
    → 전체 손익 현황

    /pnl 005930
    → 특정 종목 손익 현황

    /errors
    → 최근 에러 로그 5개

    /errors 10
    → 최근 에러 로그 10개

    /sync
    → KIS 잔고 강제 동기화

    /pause
    → 신규 신호 알림 일시정지

    /resume
    → 신규 신호 알림 재개

    /stop
    → 봇 종료
        """

        update.message.reply_text(text)

    def pause_handler(self,update,context):
        self.paused=True
        update.message.reply_text(
        "봇 일시정지 완료\n\n"
        "신규 신호 알림과 승인 요청을 중단합니다.\n"
        "이미 실행 중인 루프와 상태 조회는 계속 동작합니다."
    )
        
    def resume_handler(self,update,context):
        self.paused = False
        update.message.reply_text(
            "봇 재개 완료\n\n"
            "신규 신호 알림과 승인 요청을 다시 허용합니다."
    )
    
    def send_message(self, text):
        try:
            self.updater.bot.send_message(
                chat_id=CHAT_ID,
                text=text
            )
        except Exception as e:
            logger.exception(f"텔레그램 메시지 전송 실패: {e}")