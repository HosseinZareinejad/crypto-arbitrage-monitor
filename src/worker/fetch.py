import asyncio
from typing import Dict, List
from ..exchanges.nobitex import NobitexClient
from ..exchanges.wallex import WallexClient
from ..models import PriceSnapshot

async def fetch_all(symbols: List[str]) -> Dict[str, Dict[str, PriceSnapshot]]:
    """فچ همزمان قیمت‌ها از هر دو صرافی"""
    nobi = NobitexClient()
    wall = WallexClient()
    try:
        n = await nobi.fetch_ticker(symbols)
        w = await wall.fetch_ticker(symbols)
        return {"nobitex": n, "wallex": w}
    finally:
        await nobi.close()
        await wall.close()
