import asyncio
from ..config import settings
from ..notify.telegram import TelegramNotifier
from .fetch import fetch_all
from .compute import compute_opps
from ..core.arbitrage import ArbState

async def run_worker():
    """حلقه اصلی worker برای آربیتراژ"""
    notifier = TelegramNotifier()
    state = ArbState(
        threshold_pct=settings.THRESHOLD_PERCENT,
        hysteresis_delta_pct=settings.HYSTERESIS_DELTA_PCT,
        cooldown_seconds=settings.COOLDOWN_SECONDS
    )
    symbols = settings.symbols_list

    print(f"🚀 Worker شروع شد - نمادها: {symbols}")
    print(f"📊 آستانه: {settings.THRESHOLD_PERCENT}% - خنک‌سازی: {settings.COOLDOWN_SECONDS}s")

    while settings.ENABLE_WORKER:
        try:
            # فچ قیمت‌ها از هر دو صرافی
            quotes = await fetch_all(symbols)
            
            # محاسبه فرصت‌ها برای هر نماد
            for sym in symbols:
                for opp in compute_opps(quotes, sym):
                    if opp.diff_pct == opp.diff_pct and state.should_alert(opp):  # NaN check
                        print(f"⚡ فرصت آربیتراژ: {opp.symbol} - {opp.diff_pct:.2f}%")
                        await notifier.send(opp)
                        
        except Exception as e:
            print(f"❌ خطا در worker: {e}")
            
        await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
