import asyncio, random

async def backoff(attempt: int, base: float, max_delay: float) -> None:
    # exponential backoff with jitter
    delay = min(max_delay, base * (2 ** attempt))
    delay = delay * (0.5 + random.random()/2)
    await asyncio.sleep(delay)
