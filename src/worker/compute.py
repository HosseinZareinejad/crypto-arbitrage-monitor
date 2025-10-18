from typing import List, Dict
from ..core.arbitrage import ArbOpportunity
from ..models import PriceSnapshot, utcnow

def compute_opps(quotes: Dict[str, Dict[str, PriceSnapshot]], symbol: str) -> List[ArbOpportunity]:
    """محاسبه فرصت‌های آربیتراژ برای یک نماد"""
    out = []
    qn = quotes["nobitex"].get(symbol)
    qw = quotes["wallex"].get(symbol)
    if not (qn and qw): 
        return out
        
    now = utcnow()

    # دو جهت: Nobitex -> Wallex و Wallex -> Nobitex
    pairs = [
        ("nobitex", qn.ask, "wallex", qw.bid),
        ("wallex", qw.ask, "nobitex", qn.bid),
    ]
    
    for buy_ex, buy_price, sell_ex, sell_price in pairs:
        if not (buy_price == buy_price and sell_price == sell_price):  # NaN check
            continue
            
        diff_abs = sell_price - buy_price
        diff_pct = (diff_abs / buy_price) * 100 if buy_price > 0 else float("nan")
        
        out.append(ArbOpportunity(
            symbol=symbol, 
            buy_from=buy_ex, 
            buy_price=buy_price,
            sell_to=sell_ex, 
            sell_price=sell_price,
            diff_abs=diff_abs, 
            diff_pct=diff_pct, 
            ts=now
        ))
    return out
