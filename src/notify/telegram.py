# src/notify/telegram.py
from __future__ import annotations
from typing import Optional, Iterable, List, Union
from ..models import ArbOpportunity
from ..metrics import alerts_sent_total
from ..config import settings
import asyncio
import logging
from telegram import Bot
import aiohttp

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
        self._bale_notifier = BaleNotifier()

    async def _send_one(self, chat_id, text: str) -> None:
        if not self._bot:
            return
        await self._bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)

    async def send(self, opp: ArbOpportunity) -> None:
        text = (
            "Arbitrage Opportunity\n"
            f"Pair: {opp.symbol}\n"
            f"Buy from: {opp.buy_from} @ {opp.buy_price:.4f}\n"
            f"Sell to: {opp.sell_to} @ {opp.sell_price:.4f}\n"
            f"Spread: {opp.diff_abs:.4f} ({opp.diff_pct:.2f}%)\n"
            f"Time: {opp.ts.isoformat()}"
        )
        
        # Send to Telegram
        if self._bot and self.chat_ids:
            try:
                await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
                logger.info(f"✅ Telegram alert sent for {opp.symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to send Telegram alert: {e}", exc_info=True)
        
        # Send to Bale
        try:
            await self._bale_notifier.send(opp)
        except Exception as e:
            logger.error(f"❌ Failed to send Bale alert: {e}", exc_info=True)
        
        # Update metrics
        direction = f"{opp.buy_from}_to_{opp.sell_to}"
        alerts_sent_total.labels(symbol=opp.symbol, direction=direction).inc()

    async def send_text(self, text: str) -> None:
        # Send to Telegram
        if self._bot and self.chat_ids:
            try:
                await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
                logger.info("✅ Telegram test message sent")
            except Exception as e:
                logger.error(f"❌ Failed to send Telegram test message: {e}", exc_info=True)
        
        # Send to Bale
        try:
            await self._bale_notifier.send_text(text)
        except Exception as e:
            logger.error(f"❌ Failed to send Bale test message: {e}", exc_info=True)


class BaleNotifier:
    """Handles sending messages and arbitrage alerts via Bale bot."""
    def __init__(self):
        self.token = settings.BALE_TOKEN
        raw_ids = settings.BALE_CHAT_ID
        self.chat_ids: List[Union[int, str]] = _normalize_chat_ids(raw_ids)
        self.base_url = "https://tapi.bale.ai/bot"

    async def _send_one(self, chat_id, text: str) -> None:
        if not self.token:
            return
        
        url = f"{self.base_url}{self.token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    logger.error(f"Bale API error: {response.status} - {await response.text()}")

    async def send(self, opp: ArbOpportunity) -> None:
        if not (self.token and self.chat_ids):
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
            logger.info(f"✅ Bale alert sent for {opp.symbol}")
        except Exception as e:
            logger.error(f"❌ Failed to send Bale alert: {e}", exc_info=True)

    async def send_text(self, text: str) -> None:
        if not (self.token and self.chat_ids):
            return
        try:
            await asyncio.gather(*[self._send_one(cid, text) for cid in self.chat_ids], return_exceptions=True)
            logger.info("✅ Bale test message sent")
        except Exception as e:
            logger.error(f"❌ Failed to send Bale test message: {e}", exc_info=True)
