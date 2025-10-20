#!/usr/bin/env python3
"""
تست کامل سیستم آربیتراژ
"""
import asyncio
import sys
import os
import time
import logging

# اضافه کردن src به path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.worker.loop import run_worker
from src.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_full_system():
    """تست کامل سیستم برای 30 ثانیه"""
    logger.info("🧪 شروع تست کامل سیستم...")
    logger.info(f"📊 آستانه: {settings.THRESHOLD_PERCENT}%")
    logger.info(f"⏱️ خنک‌سازی: {settings.COOLDOWN_SECONDS}s")
    logger.info(f"📈 نمادها: {settings.symbols_list}")
    logger.info("⏰ تست برای 30 ثانیه...")
    
    # اجرای worker برای 30 ثانیه
    start_time = time.time()
    try:
        await asyncio.wait_for(run_worker(), timeout=30)
    except asyncio.TimeoutError:
        logger.info("✅ تست 30 ثانیه‌ای کامل شد!")
    except Exception as e:
        logger.error(f"❌ خطا در تست: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_full_system())
