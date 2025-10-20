import asyncio
import logging
from ..config import settings
from ..notify.telegram import TelegramNotifier
from .fetch import fetch_all
from .compute import compute_opps
from ..core.arbitrage import ArbState

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_worker():
    """حلقه اصلی worker برای آربیتراژ"""
    notifier = TelegramNotifier()
    state = ArbState(
        threshold_pct=settings.THRESHOLD_PERCENT,
        hysteresis_delta_pct=settings.HYSTERESIS_DELTA_PCT,
        cooldown_seconds=settings.COOLDOWN_SECONDS
    )
    symbols = settings.symbols_list

    logger.info(f"🚀 Worker شروع شد - نمادها: {symbols}")
    logger.info(f"📊 آستانه: {settings.THRESHOLD_PERCENT}% - خنک‌سازی: {settings.COOLDOWN_SECONDS}s")

    while settings.ENABLE_WORKER:
        try:
            # فچ قیمت‌ها از هر دو صرافی
            quotes = await fetch_all(symbols)
            
            # محاسبه فرصت‌ها برای هر نماد
            for sym in symbols:
                for opp in compute_opps(quotes, sym):
                    if opp.diff_pct == opp.diff_pct and state.should_alert(opp):  # NaN check
                        logger.info(f"⚡ فرصت آربیتراژ: {opp.symbol} - {opp.diff_pct:.2f}%")
                        await notifier.send(opp)
                        
        except Exception as e:
            logger.error(f"❌ خطا در worker: {e}", exc_info=True)
            
        await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
