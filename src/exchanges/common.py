from typing import Dict, Optional, Callable, Awaitable
import asyncio, time
import httpx
from ..config import settings
from ..utils.retry import backoff

# Map normalized 'BTC/USDT' -> per-exchange symbols if needed
NOBITEX_SYMBOL_MAP: Dict[str, str] = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "USDT/IRT": "USDTIRT",
}

WALLEX_SYMBOL_MAP: Dict[str, str] = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "USDT/IRT": "USDTIRT",
}

class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int):
        self.rate = float(rate_per_sec)
        self.capacity = int(capacity)
        self.tokens = float(capacity)
        self.updated_at = time.perf_counter()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.perf_counter()
            elapsed = now - self.updated_at
            self.updated_at = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            if self.tokens < 1:
                # wait until 1 token is available
                wait_time = (1 - self.tokens) / self.rate if self.rate > 0 else 0.05
                await asyncio.sleep(wait_time)
                self.tokens = min(self.capacity, self.tokens + wait_time * self.rate)
            self.tokens -= 1

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, open_seconds: float = 2.0):
        self.failure_threshold = int(failure_threshold)
        self.open_seconds = float(open_seconds)
        self.failures = 0
        self.open_until: float = 0.0
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            if now < self.open_until:
                return False
            return True

    async def on_success(self) -> None:
        async with self._lock:
            self.failures = 0
            self.open_until = 0.0

    async def on_failure(self) -> None:
        async with self._lock:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.open_until = time.monotonic() + self.open_seconds
                self.failures = 0

async def resilient_get(
    client: httpx.AsyncClient,
    url: str,
    exchange_name: str,
    limiter: Optional[TokenBucket] = None,
    breaker: Optional[CircuitBreaker] = None,
    max_tries: int = None,
) -> Optional[httpx.Response]:
    tries = max_tries or settings.RETRY_MAX_TRIES
    for attempt in range(tries):
        if limiter:
            await limiter.acquire()
        if breaker and not await breaker.allow():
            await asyncio.sleep(0.1)
            continue
        try:
            resp = await client.get(url)
            # backoff on 429/5xx
            if resp.status_code in (429, 500, 502, 503, 504):
                if breaker:
                    await breaker.on_failure()
                await backoff(
                    attempt,
                    settings.RETRY_BASE_DELAY,
                    settings.RETRY_MAX_DELAY,
                )
                continue
            if breaker:
                await breaker.on_success()
            return resp
        except httpx.RequestError:
            if breaker:
                await breaker.on_failure()
            await backoff(
                attempt,
                settings.RETRY_BASE_DELAY,
                settings.RETRY_MAX_DELAY,
            )
            continue
    return None
