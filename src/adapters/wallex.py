import httpx, time, asyncio
from typing import Dict, List, Optional
from ..domain.models import PriceSnapshot, utcnow
from ..config import settings
from ..exchanges.common import WALLEX_SYMBOL_MAP, TokenBucket, CircuitBreaker, resilient_get
from ..metrics import requests_total, fetch_errors_total, http_client_latency_seconds, last_bid, last_ask


class WallexClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.base = settings.WALLEX_BASE_URL.rstrip('/')
        headers = {}
        if settings.WALLEX_API_KEY:
            headers["x-api-key"] = settings.WALLEX_API_KEY
        self._client = client or httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS, headers=headers)
        # Keep headers available for the resilient_get helper
        setattr(self._client, "_extra_headers", headers)
        # Basic rate limiting and circuit breaker setup
        self._limiter = TokenBucket(rate_per_sec=5, capacity=5)
        self._breaker = CircuitBreaker(failure_threshold=3, open_seconds=1.5)

    async def close(self):
        await self._client.aclose()

    async def fetch_ticker(self, symbols: List[str]) -> Dict[str, PriceSnapshot]:
        result: Dict[str, PriceSnapshot] = {}
        for sym in symbols:
            mapped = WALLEX_SYMBOL_MAP.get(sym, sym.replace('/', ''))
            # Using the /v1/trades endpoint to pull recent trades
            url = f"{self.base}/trades?symbol={mapped}"
            start = time.perf_counter()
            try:
                r = await resilient_get(self._client, url, "wallex", self._limiter, self._breaker)
                latency = time.perf_counter() - start
                http_client_latency_seconds.labels(exchange="wallex").observe(latency)

                if r and r.status_code == 200:
                    data = r.json()
                    if data.get("success") and "result" in data:
                        trades = data["result"].get("latestTrades", [])
                        if trades:
                            # Split trades by side (buy vs sell)
                            buy_trades = [t for t in trades if t.get("isBuyOrder", False)]
                            sell_trades = [t for t in trades if not t.get("isBuyOrder", True)]

                            # Highest buy price → best bid
                            bid = max([float(t["price"]) for t in buy_trades], default=float('nan'))
                            # Lowest sell price → best ask
                            ask = min([float(t["price"]) for t in sell_trades], default=float('nan'))

                            snap = PriceSnapshot(
                                exchange="wallex", symbol=sym, bid=bid, ask=ask, ts=utcnow()
                            )
                            result[sym] = snap
                            requests_total.labels(exchange="wallex", outcome="success").inc()
                            if bid == bid:
                                last_bid.labels(exchange="wallex", symbol=sym).set(bid)
                            if ask == ask:
                                last_ask.labels(exchange="wallex", symbol=sym).set(ask)
                        else:
                            # No trades found — return NaN values
                            snap = PriceSnapshot(
                                exchange="wallex", symbol=sym, bid=float('nan'), ask=float('nan'), ts=utcnow()
                            )
                            result[sym] = snap
                            requests_total.labels(exchange="wallex", outcome="success").inc()
                    else:
                        requests_total.labels(exchange="wallex", outcome="http_error").inc()
                        fetch_errors_total.labels(exchange="wallex").inc()
                elif r is not None:
                    requests_total.labels(exchange="wallex", outcome="http_error").inc()
                    fetch_errors_total.labels(exchange="wallex").inc()
            except Exception:
                requests_total.labels(exchange="wallex", outcome="exception").inc()
                fetch_errors_total.labels(exchange="wallex").inc()
                await asyncio.sleep(0.2)
        return result
