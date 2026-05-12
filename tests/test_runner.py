import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from runner import is_market_time, should_skip_signal
from core.portfolio import Portfolio


def test_should_skip_none_signal():
    portfolio = Portfolio()
    skip, reason = should_skip_signal(None, portfolio)

    assert skip is True
    assert reason == "신호 없음"


def test_should_skip_buy_when_already_has_position():
    portfolio = Portfolio()
    portfolio.positions["005930"] = {
        "qty": 10,
        "avg_price": 70000,
    }

    signal = {
        "action": "BUY",
        "symbol": "005930",
        "price": 70000,
        "reason": "test",
    }

    skip, reason = should_skip_signal(signal, portfolio)

    assert skip is True
    assert "이미 보유" in reason


def test_should_skip_sell_when_no_position():
    portfolio = Portfolio()

    signal = {
        "action": "SELL",
        "symbol": "005930",
        "price": 70000,
        "reason": "test",
    }

    skip, reason = should_skip_signal(signal, portfolio)

    assert skip is True
    assert "보유 수량 없음" in reason


def test_should_not_skip_valid_buy():
    portfolio = Portfolio()

    signal = {
        "action": "BUY",
        "symbol": "005930",
        "price": 70000,
        "reason": "test",
    }

    skip, reason = should_skip_signal(signal, portfolio)

    assert skip is False
    assert reason == ""