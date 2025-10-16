from datetime import datetime, timezone, timedelta
from src.arb.engine import ArbEngine
from src.models import PriceSnapshot

def ts():
    return datetime.now(timezone.utc)

def snap(ex, sym, bid, ask, t=None):
    return PriceSnapshot(exchange=ex, symbol=sym, bid=bid, ask=ask, ts=t or ts())

def test_no_opportunity_below_threshold():
    engine = ArbEngine(threshold_pct=1.0, cooldown_seconds=10, hysteresis_delta_pct=0.5)
    a = snap("nobitex", "BTC/USDT", bid=100, ask=100)
    b = snap("wallex", "BTC/USDT", bid=100.5, ask=101)
    assert engine.evaluate(a, b) is None

def test_opportunity_at_threshold():
    engine = ArbEngine(threshold_pct=0.5, cooldown_seconds=10, hysteresis_delta_pct=0.1)
    a = snap("nobitex", "BTC/USDT", bid=100, ask=100)
    b = snap("wallex", "BTC/USDT", bid=101, ask=101)
    opp = engine.evaluate(a, b)
    assert opp is not None
    assert opp.diff_pct >= 0.5

def test_cooldown_blocks_duplicate():
    engine = ArbEngine(threshold_pct=0.1, cooldown_seconds=60, hysteresis_delta_pct=0.2)
    t0 = ts()
    a = snap("nobitex", "BTC/USDT", bid=100, ask=100, t=t0)
    b = snap("wallex", "BTC/USDT", bid=102, ask=102, t=t0)
    assert engine.evaluate(a, b) is not None
    # within cooldown with small improvement less than hysteresis
    a2 = snap("nobitex", "BTC/USDT", bid=100, ask=100, t=t0 + timedelta(seconds=10))
    b2 = snap("wallex", "BTC/USDT", bid=102.1, ask=102.1, t=t0 + timedelta(seconds=10))
    assert engine.evaluate(a2, b2) is None

def test_hysteresis_allows_resend_if_improved_enough():
    engine = ArbEngine(threshold_pct=0.1, cooldown_seconds=60, hysteresis_delta_pct=0.5)
    t0 = ts()
    a = snap("nobitex", "BTC/USDT", bid=100, ask=100, t=t0)
    b = snap("wallex", "BTC/USDT", bid=110, ask=110, t=t0)
    first = engine.evaluate(a, b)
    assert first is not None
    # big improvement in diff triggers despite cooldown
    a2 = snap("nobitex", "BTC/USDT", bid=100, ask=100, t=t0 + timedelta(seconds=5))
    b2 = snap("wallex", "BTC/USDT", bid=120, ask=120, t=t0 + timedelta(seconds=5))
    assert engine.evaluate(a2, b2) is not None
