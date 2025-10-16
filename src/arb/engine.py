from __future__ import annotations
from ..models import PriceSnapshot, ArbOpportunity
from ..metrics import last_diff_pct
from typing import Dict, Optional
from datetime import datetime, timedelta

class ArbEngine:
    def __init__(self, threshold_pct: float, cooldown_seconds: float, hysteresis_delta_pct: float):
        self.threshold_pct = float(threshold_pct)
        self.cooldown = timedelta(seconds=float(cooldown_seconds))
        self.hysteresis = float(hysteresis_delta_pct)
        self._last_alert: dict[tuple[str,str], dict] = {}  # key: (symbol, direction)

    def evaluate(self, a: PriceSnapshot, b: PriceSnapshot) -> Optional[ArbOpportunity]:
        # consider buy on A ask, sell on B bid
        if not (a and b):
            return None
        buy_price = a.ask
        sell_price = b.bid
        if buy_price != buy_price or sell_price != sell_price:  # NaN checks
            return None
        diff_abs = sell_price - buy_price
        diff_pct = (diff_abs / buy_price) * 100
        direction = f"{a.exchange}_to_{b.exchange}"
        last_diff_pct.labels(symbol=a.symbol, direction=direction).set(diff_pct)

        if diff_pct < self.threshold_pct:
            return None

        key = (a.symbol, direction)
        now = a.ts
        last = self._last_alert.get(key)
        if last:
            # Cooldown
            if now - last["ts"] < self.cooldown and diff_pct < last["pct"] + self.hysteresis:
                return None

        opp = ArbOpportunity(
            symbol=a.symbol, buy_from=a.exchange, buy_price=buy_price,
            sell_to=b.exchange, sell_price=sell_price, diff_abs=diff_abs,
            diff_pct=diff_pct, ts=now
        )
        self._last_alert[key] = {"ts": now, "pct": diff_pct}
        return opp
