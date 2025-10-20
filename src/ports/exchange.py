from typing import Protocol, Dict, List
from ..domain.models import PriceSnapshot

class ExchangePort(Protocol):
    async def fetch_ticker(self, symbols: List[str]) -> Dict[str, PriceSnapshot]:
        ...
