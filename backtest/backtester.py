class Backtester:
    def __init__(
        self,
        strategy,
        initial_cash=1_000_000,
        trade_ratio=0.2,
        fee_rate=0.00015,
        slippage_rate=0.0005,
        stop_loss_rate=None,
        take_profit_rate=None,
        max_hold_bars=None,
    ):
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.trade_ratio = trade_ratio

        # 거래 비용
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate

        # 선택 옵션
        self.stop_loss_rate = stop_loss_rate
        self.take_profit_rate = take_profit_rate
        self.max_hold_bars = max_hold_bars

        self.reset()

    def reset(self):
        self.cash = self.initial_cash
        self.position = None
        self.trades = []
        self.equity_curve = []
        self.signal_logs = []

    def run(self, data, symbol, investor_flow=None):
        self.reset()

        if data is None or data.empty:
            return self._result(symbol)

        data = data.copy()

        # strategy.py에서 최소 30개 미만이면 None 반환하므로 30부터 시작
        start_index = 30

        for i in range(start_index, len(data)):
            window = data.iloc[:i + 1].copy()

            flow_window = None
            if investor_flow is not None and not investor_flow.empty:
                flow_window = investor_flow.iloc[:i + 1].copy()

            current_bar = window.iloc[-1]
            price = float(current_bar["close"])

            # 1. 현재 평가금액 기록
            equity = self._calculate_equity(price)
            self.equity_curve.append(equity)

            # 2. 보유 중이면 손절/익절/최대보유기간 체크
            exit_signal = self._check_exit_conditions(price, i)

            if exit_signal is not None and self.position is not None:
                print(f"BACKTEST {exit_signal}: {symbol} @ {price:.0f}")
                self._sell(price, i, reason=exit_signal)
                continue

            # 3. 전략 신호 생성
            signal = self.strategy.generate_signal(window, symbol, flow_window)

            if signal is None:
                continue

            action = signal.get("action")
            score = signal.get("score", 0)
            reason = signal.get("reason", "")
            reasons = signal.get("reasons", [])

            # 4. 신호 로그 저장
            signal_log = {
                "index": i,
                "symbol": symbol,
                "action": action,
                "price": price,
                "score": score,
                "reason": reason,
                "reasons": reasons,
                "rsi": signal.get("rsi"),
                "ma20": signal.get("ma20"),
                "volume": signal.get("volume"),
                "volume_avg": signal.get("volume_avg"),
                "foreign_net": signal.get("foreign_net"),
                "institution_net": signal.get("institution_net"),
            }

            # BUY/WATCH 신호 이후 n봉 뒤 수익률 분석용
            signal_log.update(self._forward_returns(data, i, price))

            self.signal_logs.append(signal_log)

            print(
                f"[BACKTEST SIGNAL] {symbol} "
                f"action={action}, score={score}, price={price:.0f}, "
                f"reason={reason}"
            )

            # 5. 실제 매매 처리
            if action == "BUY" and self.position is None:
                print(f"BACKTEST BUY: {symbol} @ {price:.0f}")
                self._buy(price, i, reason=reason)

            elif action == "SELL" and self.position is not None:
                print(f"BACKTEST SELL: {symbol} @ {price:.0f}")
                self._sell(price, i, reason=reason)

            # WATCH는 매매하지 않고 신호 로그만 남김
            elif action == "WATCH":
                pass

        # 마지막 봉에서 보유 중이면 강제 청산
        final_price = float(data.iloc[-1]["close"])

        if self.position is not None:
            self._sell(final_price, len(data) - 1, reason="FINAL_EXIT")

        return self._result(symbol)

    def _buy(self, price, index, reason=""):
        # 슬리피지 반영: 매수는 조금 비싸게 산다고 가정
        buy_price = price * (1 + self.slippage_rate)

        amount = self.cash * self.trade_ratio
        qty = int(amount // buy_price)

        if qty <= 0:
            return

        trade_value = qty * buy_price
        fee = trade_value * self.fee_rate

        total_cost = trade_value + fee

        if total_cost > self.cash:
            return

        self.cash -= total_cost

        self.position = {
            "qty": qty,
            "avg_price": buy_price,
            "entry_index": index,
            "entry_reason": reason,
        }

        self.trades.append({
            "type": "BUY",
            "index": index,
            "price": buy_price,
            "qty": qty,
            "trade_value": trade_value,
            "fee": fee,
            "cash": self.cash,
            "reason": reason,
        })

    def _sell(self, price, index, reason=""):
        if self.position is None:
            return

        # 슬리피지 반영: 매도는 조금 싸게 판다고 가정
        sell_price = price * (1 - self.slippage_rate)

        qty = self.position["qty"]
        avg_price = self.position["avg_price"]
        entry_index = self.position["entry_index"]

        trade_value = qty * sell_price
        fee = trade_value * self.fee_rate

        pnl = (sell_price - avg_price) * qty - fee
        pnl_rate = (sell_price - avg_price) / avg_price

        self.cash += trade_value - fee

        self.trades.append({
            "type": "SELL",
            "index": index,
            "price": sell_price,
            "qty": qty,
            "trade_value": trade_value,
            "fee": fee,
            "cash": self.cash,
            "pnl": pnl,
            "pnl_rate": pnl_rate,
            "hold_bars": index - entry_index,
            "reason": reason,
        })

        self.position = None

    def _check_exit_conditions(self, current_price, current_index):
        if self.position is None:
            return None

        avg_price = self.position["avg_price"]
        entry_index = self.position["entry_index"]

        pnl_rate = (current_price - avg_price) / avg_price
        hold_bars = current_index - entry_index

        if self.stop_loss_rate is not None and pnl_rate <= -self.stop_loss_rate:
            return "STOP_LOSS"

        if self.take_profit_rate is not None and pnl_rate >= self.take_profit_rate:
            return "TAKE_PROFIT"

        if self.max_hold_bars is not None and hold_bars >= self.max_hold_bars:
            return "MAX_HOLD_EXIT"

        return None

    def _calculate_equity(self, current_price):
        equity = self.cash

        if self.position is not None:
            equity += self.position["qty"] * current_price

        return equity

    def _calculate_mdd(self):
        if not self.equity_curve:
            return 0

        peak = self.equity_curve[0]
        max_drawdown = 0

        for equity in self.equity_curve:
            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak

            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def _forward_returns(self, data, index, entry_price):
        result = {}

        horizons = {
            "return_3bars": 3,
            "return_6bars": 6,
            "return_12bars": 12,
            "return_24bars": 24,
        }

        for name, bars in horizons.items():
            target_index = index + bars

            if target_index < len(data):
                future_price = float(data.iloc[target_index]["close"])
                result[name] = (future_price - entry_price) / entry_price
            else:
                result[name] = None

        return result

    def _signal_summary(self):
        summary = {
            "BUY": 0,
            "WATCH": 0,
            "SELL": 0,
        }

        for log in self.signal_logs:
            action = log.get("action")

            if action in summary:
                summary[action] += 1

        return summary

    def _forward_return_summary(self):
        summary = {}

        for action in ["BUY", "WATCH", "SELL"]:
            action_logs = [
                log for log in self.signal_logs
                if log.get("action") == action
            ]

            summary[action] = {}

            for key in ["return_3bars", "return_6bars", "return_12bars", "return_24bars"]:
                values = [
                    log[key] for log in action_logs
                    if log.get(key) is not None
                ]

                if values:
                    avg_return = sum(values) / len(values)
                    win_rate = len([v for v in values if v > 0]) / len(values)

                    summary[action][key] = {
                        "count": len(values),
                        "avg_return": avg_return,
                        "win_rate": win_rate,
                    }
                else:
                    summary[action][key] = {
                        "count": 0,
                        "avg_return": 0,
                        "win_rate": 0,
                    }

        return summary

    def _result(self, symbol):
        sells = [t for t in self.trades if t["type"] == "SELL"]

        wins = [t for t in sells if t["pnl"] > 0]
        losses = [t for t in sells if t["pnl"] <= 0]

        total_return = (self.cash - self.initial_cash) / self.initial_cash
        win_rate = len(wins) / len(sells) if sells else 0

        avg_win = sum(t["pnl_rate"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pnl_rate"] for t in losses) / len(losses) if losses else 0

        gross_profit = sum(t["pnl"] for t in wins) if wins else 0
        gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        avg_hold_bars = (
            sum(t["hold_bars"] for t in sells) / len(sells)
            if sells else 0
        )

        return {
            "symbol": symbol,
            "initial_cash": self.initial_cash,
            "final_cash": self.cash,
            "total_return": total_return,
            "trade_count": len(self.trades),
            "completed_trades": len(sells),
            "win_rate": win_rate,
            "mdd": self._calculate_mdd(),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "avg_hold_bars": avg_hold_bars,
            "signal_summary": self._signal_summary(),
            "forward_return_summary": self._forward_return_summary(),
            "trades": self.trades,
            "signal_logs": self.signal_logs,
            "equity_curve": self.equity_curve,
        }