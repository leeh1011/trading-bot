from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
from settings import TELEGRAM_TOKEN, CHAT_ID


class TelegramBot:

    def __init__(self, approval_manager, execution_engine):
        self.approval_manager = approval_manager
        self.execution_engine = execution_engine

        self.updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dp = self.updater.dispatcher

        dp.add_handler(CallbackQueryHandler(self.button_handler))

        self.updater.start_polling()
        print("🤖 Telegram Bot 실행됨")

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

        self.updater.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            reply_markup=reply_markup
        )

    def button_handler(self, update, context):
        query = update.callback_query
        data = query.data

        action, order_id = data.split("_")

        if action == "approve":
            order = self.approval_manager.approve(order_id)

            if order:
                result = self.execution_engine.execute(order["signal"])
                query.edit_message_text(f"✅ 실행됨: {result}")
            else:
                query.edit_message_text("❌ 만료된 주문")

        elif action == "reject":
            self.approval_manager.reject(order_id)
            query.edit_message_text("❌ 거절됨")

        query.answer()
 