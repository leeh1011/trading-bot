from utils.indicators import calculate_rsi, moving_average


class ScoreV1Strategy:
    def __init__(self):
        self.buy_score_threshold = 70
        self.sell_score_threshold = 70
        self.volume_window = 20

    def generate_signal(self, data, symbol, investor_flow=None):
        if data is None or len(data) < 30:
            return None

        data = data.copy()

        data["rsi"] = calculate_rsi(data, period=14)
        data["ma20"] = moving_average(data, window=20)
        data["volume_avg"] = data["volume"].rolling(self.volume_window).mean()

        latest = data.iloc[-1]

        if latest[["rsi", "ma20", "volume_avg"]].isnull().any():
            return None

        price = float(latest["close"])
        rsi = float(latest["rsi"])
        ma20 = float(latest["ma20"])
        volume = float(latest["volume"])
        volume_avg = float(latest["volume_avg"])

        foreign_net = 0
        institution_net = 0

        if investor_flow is not None and not investor_flow.empty:
            latest_flow = investor_flow.iloc[-1]
            foreign_net = float(latest_flow.get("foreign_net", 0))
            institution_net = float(latest_flow.get("institution_net", 0))

        buy_score = 0
        sell_score = 0
        reasons = []

        # BUY 점수
        if rsi < 45:
            buy_score += 30
            reasons.append(f"RSI 낮음({rsi:.2f})")
        elif rsi < 55:
            buy_score += 15
            reasons.append(f"RSI 중립 이하({rsi:.2f})")

        if price > ma20:
            buy_score += 25
            reasons.append("가격이 MA20 위")

        if volume > volume_avg:
            buy_score += 20
            reasons.append("거래량 평균 이상")

        if foreign_net > 0:
            buy_score += 15
            reasons.append(f"외인 순매수({foreign_net:.0f})")

        if institution_net > 0:
            buy_score += 15
            reasons.append(f"기관 순매수({institution_net:.0f})")

        # SELL 점수
        sell_reasons = []

        if rsi > 70:
            sell_score += 35
            sell_reasons.append(f"RSI 과열({rsi:.2f})")

        if price < ma20:
            sell_score += 20
            sell_reasons.append("가격이 MA20 아래")

        if foreign_net < 0:
            sell_score += 20
            sell_reasons.append(f"외인 순매도({foreign_net:.0f})")

        if institution_net < 0:
            sell_score += 20
            sell_reasons.append(f"기관 순매도({institution_net:.0f})")

        if buy_score >= self.buy_score_threshold:
            return {
                "action": "BUY",
                "symbol": symbol,
                "price": price,
                "reason": f"BUY SCORE={buy_score}: " + ", ".join(reasons)
            }

        if sell_score >= self.sell_score_threshold:
            return {
                "action": "SELL",
                "symbol": symbol,
                "price": price,
                "reason": f"SELL SCORE={sell_score}: " + ", ".join(sell_reasons)
            }

        return None