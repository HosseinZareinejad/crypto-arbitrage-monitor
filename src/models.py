from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from datetime import datetime, timezone

@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    exchange: Literal["nobitex", "wallex"]
    symbol: str           # normalized like "BTC/USDT"
    bid: float            # best buy (what we can sell at)
    ask: float            # best sell (what we can buy at)
    ts: datetime

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True, slots=True)
class ArbOpportunity:
    symbol: str
    buy_from: Literal["nobitex","wallex"]
    buy_price: float
    sell_to: Literal["nobitex","wallex"]
    sell_price: float
    diff_abs: float
    diff_pct: float
    ts: datetime
