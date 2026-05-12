import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))

MODE = "kismock"       #테스트 할 때는 "paper"로 변경."kismock"

SYMBOLS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
    "035720",  # 카카오
    "005380",  # 현대차
    "012330",  # 현대모비스
    "105560",  # KB금융
    "055550",  # 신한지주
    "051910",  # LG화학
    "066570",  # LG전자
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
KIS_REAL_URL=os.getenv("KIS_REAL_URL")

SYMBOL_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "005380": "현대차",
    "012330": "현대모비스",
    "105560": "KB금융",
    "055550": "신한지주",
    "051910": "LG화학",
    "066570": "LG전자",
}