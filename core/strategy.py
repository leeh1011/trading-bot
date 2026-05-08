from utils.indicators import calculate_rsi, moving_average


class Strategy:
    def __init__(self):
        self.rsi_buy_threshold = 45
        self.rsi_sell_threshold = 70
        self.volume_window = 20

    def generate_signal(self, data, symbol, investor_flow=None):
        if data is None or len(data) < 30:
            return None

        data = data.copy()

        data["rsi"] = calculate_rsi(data, period=14)
        data["ma20"] = moving_average(data, window=20)
        data["volume_avg"] = data["volume"].rolling(self.volume_window).mean()

        latest = data.iloc[-1]

        print(
            f"RSI={rsi:.2f} "
            f"MA20={ma20:.2f}"
        )

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

        investor_buy_filter = (
            foreign_net > 0 or institution_net > 0
        )

        investor_sell_warning = (
            foreign_net < 0 and institution_net < 0
        )

        buy_condition = (
            rsi < self.rsi_buy_threshold
            and price > ma20
            and volume > volume_avg
            and investor_buy_filter
        )

        sell_condition = (
            rsi > self.rsi_sell_threshold
            or investor_sell_warning
        )

        if buy_condition:
            return {
                "action": "BUY",
                "symbol": symbol,
                "price": price,
                "reason": (
                    f"BUY: RSI={rsi:.2f}, price>MA20, "
                    f"volume>{self.volume_window}avg, "
                    f"foreign_net={foreign_net:.0f}, "
                    f"institution_net={institution_net:.0f}"
                )
            }

        if sell_condition:
            return {
                "action": "SELL",
                "symbol": symbol,
                "price": price,
                "reason": (
                    f"SELL: RSI={rsi:.2f}, "
                    f"foreign_net={foreign_net:.0f}, "
                    f"institution_net={institution_net:.0f}"
                )
            }

        return None