from utils.indicators import calculate_rsi, moving_average


class Strategy:
    def __init__(self):
        self.rsi_buy_threshold = 45
        self.rsi_sell_threshold = 70
        self.volume_window = 20

    def generate_signal(self, data, symbol):
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
        foreign_net=float(latest["foreign_net"])
        institution_net=float(latest["institution_net"])

        buy_condition = (
            rsi < self.rsi_buy_threshold
            and price > ma20
            and volume > volume_avg
            and (foreign_net>0
            or institution_net>0)
        )

        sell_condition = (
            rsi > self.rsi_sell_threshold
        )

        if buy_condition:
            return {
                "action": "BUY",
                "symbol": symbol,
                "price": price,
                "reason": (
                    f"BUY: RSI={rsi:.2f}, price>MA20, "
                    f"volume>{self.volume_window}avg"
                )
            }

        if sell_condition:
            return {
                "action": "SELL",
                "symbol": symbol,
                "price": price,
                "reason": f"SELL: RSI={rsi:.2f}"
            }

        return None