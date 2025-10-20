# src/notify/telegram.py
from __future__ import annotations
from typing import Optional, Iterable, List, Union
from ..models import ArbOpportunity
from ..metrics import alerts_sent_total
from ..config import settings
import asyncio
import logging
from telegram import Bot

logger = logging.getLogger(__name__)

def _normalize_chat_ids(raw):
    if not raw:
        return []
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")] if "," in raw else [raw.strip()]
        out = []
        for p in parts:
            try: out.append(int(p))
            except ValueError: out.append(p)
        return out
    try:
        return [int(x) if (not isinstance(x, str) or x.lstrip("-").isdigit()) else x for x in raw]
    except Exception:
        return [str(x) for x in raw]

class TelegramNotifier:
    """Handles sending messages and arbitrage alerts via Telegram bot."""
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN
        raw_ids = settings.TELEGRAM_CHAT_ID
        self.chat_ids: List[Union[int, str]] = _normalize_chat_ids(raw_ids)
        self._bot: Optional[Bot] = Bot(token=self.token) if self.token else None

    async def _send_one(self, chat_id, text: str) -> None:
        if not self._bot:
            return
        await self._bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)

    async def send(self, opp: ArbOpportunity) -> None:
        if not (self._bot and self.chat_ids):
            return
        text = (
            "Arbitrage Opportunity\n"
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
            logger.info(f"✅ Telegram alert sent for {opp.symbol}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alert: {e}", exc_info=True)

    async def send_text(self, text: str) -> None:
        if not (self._bot and self.chat_ids):
            return
        try:
            await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
            logger.info("✅ Telegram test message sent")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram test message: {e}", exc_info=True)
