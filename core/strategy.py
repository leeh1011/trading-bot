from utils.indicators import calculate_rsi, moving_average


class Strategy:

    def generate_signal(self, data, symbol):
        """
        매매 신호 생성
        """

        data["rsi"] = calculate_rsi(data)
        data["ma"] = moving_average(data)

        latest = data.iloc[-1]

        # BUY 조건
        if latest["rsi"] < 30 and latest["close"] > latest["ma"]:
            return {
                "action": "BUY",
                "symbol": symbol,
                "price": float(latest["close"]),
                "reason": "RSI < 30 & price > MA"
            }

        # SELL 조건
        elif latest["rsi"] > 70:
            return {
                "action": "SELL",
                "symbol": symbol,
                "price": float(latest["close"]),
                "reason": "RSI > 70"
            }

        return None
