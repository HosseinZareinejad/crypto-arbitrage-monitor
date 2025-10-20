from typing import Protocol
from ..domain.models import ArbOpportunity

class NotifierPort(Protocol):
    async def send(self, opp: ArbOpportunity) -> None:
        ...

    async def send_text(self, text: str) -> None:
        ...
