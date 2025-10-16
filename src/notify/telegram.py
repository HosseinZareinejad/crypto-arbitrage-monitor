from __future__ import annotations
from typing import Optional
from ..config import settings
from ..models import ArbOpportunity
from ..metrics import alerts_sent_total
import asyncio
from telegram import Bot

class TelegramNotifier:
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self._bot: Optional[Bot] = Bot(token=self.token) if self.token else None

    async def send(self, opp: ArbOpportunity) -> None:
        if not (self._bot and self.chat_id):
            return
        text = (
            "⚡️ فرصت آربیتراژ\n"
            f"جفت‌ارز: {opp.symbol}\n"
            f"خرید از: {opp.buy_from} @ {opp.buy_price:.4f}\n"
            f"فروش به: {opp.sell_to} @ {opp.sell_price:.4f}\n"
            f"اختلاف: {opp.diff_abs:.4f} ({opp.diff_pct:.2f}%)\n"
            f"زمان: {opp.ts.isoformat()}"
        )
        try:
            await asyncio.to_thread(self._bot.send_message, chat_id=self.chat_id, text=text)
            direction = f"{opp.buy_from}_to_{opp.sell_to}"
            alerts_sent_total.labels(symbol=opp.symbol, direction=direction).inc()
        except Exception:
            pass
