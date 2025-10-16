import httpx, time, asyncio
from typing import Dict, List, Optional
from ..models import PriceSnapshot, utcnow
from ..config import settings
from .common import WALLEX_SYMBOL_MAP, TokenBucket, CircuitBreaker, resilient_get
from ..metrics import requests_total, fetch_errors_total, http_client_latency_seconds, last_bid, last_ask

class WallexClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.base = settings.WALLEX_BASE_URL.rstrip('/')
        self._client = client or httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._limiter = TokenBucket(rate_per_sec=5, capacity=5)
        self._breaker = CircuitBreaker(failure_threshold=3, open_seconds=1.5)

    async def close(self):
        await self._client.aclose()

    async def fetch_ticker(self, symbols: List[str]) -> Dict[str, PriceSnapshot]:
        result: Dict[str, PriceSnapshot] = {}
        for sym in symbols:
            mapped = WALLEX_SYMBOL_MAP.get(sym, sym.replace('/',''))
            url = f"{self.base}/orderbooks?symbol={mapped}"
            start = time.perf_counter()
            try:
                r = await resilient_get(self._client, url, "wallex", self._limiter, self._breaker)
                latency = time.perf_counter() - start
                http_client_latency_seconds.labels(exchange="wallex").observe(latency)
                if r and r.status_code == 200:
                    data = r.json()
                    ob = (data.get("result") or {}).get(mapped) or {}
                    asks = ob.get("asks") or []
                    bids = ob.get("bids") or []
                    ask = float(asks[0][0]) if asks else float('nan')
                    bid = float(bids[0][0]) if bids else float('nan')
                    snap = PriceSnapshot(
                        exchange="wallex", symbol=sym, bid=bid, ask=ask, ts=utcnow()
                    )
                    result[sym] = snap
                    requests_total.labels(exchange="wallex", outcome="success").inc()
                    if bid == bid:
                        last_bid.labels(exchange="wallex", symbol=sym).set(bid)
                    if ask == ask:
                        last_ask.labels(exchange="wallex", symbol=sym).set(ask)
                elif r is not None:
                    requests_total.labels(exchange="wallex", outcome="http_error").inc()
                    fetch_errors_total.labels(exchange="wallex").inc()
            except Exception:
                requests_total.labels(exchange="wallex", outcome="exception").inc()
                fetch_errors_total.labels(exchange="wallex").inc()
                await asyncio.sleep(0.2)
        return result
