from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
from settings import TELEGRAM_TOKEN, CHAT_ID
from database.db import log_approval
from telegram.utils.request import Request

class TelegramBot:

    def __init__(self, approval_manager, execution_engine):
        self.approval_manager = approval_manager
        self.execution_engine = execution_engine

        request = Request(
            connect_timeout=30,
            read_timeout=30,
            con_pool_size=8
        )

        self.updater = Updater(
            token=TELEGRAM_TOKEN,
            request_kwargs={
                "connect_timeout": 30,
                "read_timeout": 30,
            },
            use_context=True
        )
        
        dp = self.updater.dispatcher

        dp.add_handler(CallbackQueryHandler(self.button_handler))

        try:
            self.updater.start_polling(
                timeout=10,
                read_latency=2,
                bootstrap_retries=3
            )
            print("🤖 Telegram Bot 실행됨")
        except Exception as e:
            print(f"❌ Telegram Bot 연결 실패: {e}")
            raise

    def send_signal(self, signal):
        order_id = self.approval_manager.create(signal)

        if order_id is None:
            print(f"⚠️ 중복/쿨다운으로 신호 무시: {signal['symbol']}")
            return

        keyboard = [
            [
                InlineKeyboardButton("✅ 승인", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton("❌ 거절", callback_data=f"reject_{order_id}")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        text = f"""
                📈 신호 발생

                종목: {signal['symbol']}
                가격: {signal['price']}
                이유: {signal['reason']}
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

    def button_handler(self, update, context):
        query = update.callback_query
        data = query.data

        action, order_id = data.split("_")

        if action == "approve":
            order = self.approval_manager.approve(order_id)

            if order:
                signal = order["signal"]
                log_approval(order_id, signal["symbol"], signal["action"], "APPROVE")
                result = self.execution_engine.execute(signal)
                query.edit_message_text(f"✅ 실행됨: {result}")
            else:
                query.edit_message_text("❌ 만료된 주문")

        elif action == "reject":
            order = self.approval_manager.reject(order_id)

            if order:
                signal = order["signal"]
                log_approval(order_id, signal["symbol"], signal["action"], "REJECT")

            query.edit_message_text("❌ 거절됨")

        query.answer()
 