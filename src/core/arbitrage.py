from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple

@dataclass
class Quote:
    bid: float  # بهترین قیمت خرید شما از مارکت
    ask: float  # بهترین قیمت فروش به شما
    ts: datetime

@dataclass
class ArbOpportunity:
    symbol: str
    buy_from: str
    buy_price: float
    sell_to: str
    sell_price: float
    diff_abs: float
    diff_pct: float
    ts: datetime

class ArbState:
    def __init__(self, threshold_pct: float, hysteresis_delta_pct: float, cooldown_seconds: float):
        self.th = threshold_pct
        self.hys = hysteresis_delta_pct
        self.cool = timedelta(seconds=cooldown_seconds)
        self.last_alert: Dict[Tuple[str, str, str], datetime] = {}  # key: (symbol, buy, sell) -> datetime
        self.latched: Set[Tuple[str, str, str]] = set()  # key set when above th until falls below (th - hys)

    def should_alert(self, opp: ArbOpportunity) -> bool:
        key = (opp.symbol, opp.buy_from, opp.sell_to)
        now = opp.ts
        
        # گیتِ هیسترزیس
        if key in self.latched:
            if opp.diff_pct < (self.th - self.hys):
                self.latched.remove(key)
            else:
                # هنوز لَچ است، اجازه می‌دهد خنک‌سازی مسئول باشد
                pass
        else:
            if opp.diff_pct >= self.th:
                self.latched.add(key)
            else:
                return False
                
        # خنک‌سازی
        last = self.last_alert.get(key)
        if last and (now - last) < self.cool:
            return False
            
        self.last_alert[key] = now
        return True
