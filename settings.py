import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))

MODE = "paper"       #테스트 할 때는 "paper"로 변경.

SYMBOLS = [
    "005930",
    "000660",
    "035420",
]

TRADE_RATIO = 0.2
APPROVAL_TIMEOUT = 120
LOOP_INTERVAL = 300
SIGNAL_COOLDOWN_SECONDS = 300

RISK = {
    "stop_loss": -0.03,
    "take_profit": 0.05,
    "daily_loss_limit": -0.05,
}

KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_ACCOUNT = os.getenv("KIS_ACCOUNT")
KIS_ACCOUNT_PRODUCT = os.getenv("KIS_ACCOUNT_PRODUCT", "01")
KIS_URL = os.getenv("KIS_URL")