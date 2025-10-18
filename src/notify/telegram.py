from __future__ import annotations
from typing import Optional, Iterable, List, Union
from ..models import ArbOpportunity
from ..metrics import alerts_sent_total
from ..config import settings
import os
import asyncio
from telegram import Bot

def _normalize_chat_ids(raw: Union[str, int, Iterable[Union[str, int]], None]) -> List[Union[int, str]]:
    """Normalize different chat_id formats (string, int, or list) into a list of IDs."""
    if raw is None:
        return []
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")] if "," in raw else [raw.strip()]
        ids: List[Union[int, str]] = []
        for p in parts:
            try:
                ids.append(int(p))
            except ValueError:
                ids.append(p)
        return ids
    try:
        return [
            int(x) if not isinstance(x, str) else (int(x) if x.lstrip("-").isdigit() else x)
            for x in raw  # type: ignore
        ]
    except Exception:
        return [str(x) for x in raw]


class TelegramNotifier:
    """Handles sending messages and arbitrage alerts via Telegram bot."""

    def __init__(self):
        # Load token and chat IDs from environment
        self.token = os.getenv("TELEGRAM_TOKEN") or "7721647721:AAHsAt0N0gQ9IEmKYuUarlTRI2Js8tE9Nfc"
        env_ids = os.getenv("TELEGRAM_CHAT_IDS") or os.getenv("TELEGRAM_CHAT_ID") or "337988042"
        self.chat_ids: List[Union[int, str]] = _normalize_chat_ids(env_ids)
        self._bot: Optional[Bot] = Bot(token=self.token) if self.token else None

    async def _send_one(self, chat_id: Union[int, str], text: str) -> None:
        """Send a single message to a specific chat."""
        if not self._bot:
            return
        await self._bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)

    async def send(self, opp: ArbOpportunity) -> None:
        """Send a formatted arbitrage alert message."""
        if not (self._bot and self.chat_ids):
            return

        text = (
            "⚡️ Arbitrage Opportunity\n"
            f"Pair: {opp.symbol}\n"
            f"Buy from: {opp.buy_from} @ {opp.buy_price:.4f}\n"
            f"Sell to: {opp.sell_to} @ {opp.sell_price:.4f}\n"
            f"Spread: {opp.diff_abs:.4f} ({opp.diff_pct:.2f}%)\n"
            f"Time: {opp.ts.isoformat()}"
        )

        try:
            await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
            direction = f"{opp.buy_from}_to_{opp.sell_to}"
            alerts_sent_total.labels(symbol=opp.symbol, direction=direction).inc()
        except Exception:
            # Fail silently to avoid interrupting the main process
            pass

    async def send_text(self, text: str) -> None:
        """Send a plain text message."""
        if not (self._bot and self.chat_ids):
            return
        try:
            await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
        except Exception:
            pass
