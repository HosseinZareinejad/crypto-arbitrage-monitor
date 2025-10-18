#!/usr/bin/env python3
"""
تست کامل سیستم آربیتراژ
"""
import asyncio
import sys
import os
import time

# اضافه کردن src به path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.worker.loop import run_worker
from src.config import settings

async def test_full_system():
    """تست کامل سیستم برای 30 ثانیه"""
    print("🧪 شروع تست کامل سیستم...")
    print(f"📊 آستانه: {settings.THRESHOLD_PERCENT}%")
    print(f"⏱️ خنک‌سازی: {settings.COOLDOWN_SECONDS}s")
    print(f"📈 نمادها: {settings.symbols_list}")
    print("⏰ تست برای 30 ثانیه...")
    
    # اجرای worker برای 30 ثانیه
    start_time = time.time()
    try:
        await asyncio.wait_for(run_worker(), timeout=30)
    except asyncio.TimeoutError:
        print("✅ تست 30 ثانیه‌ای کامل شد!")
    except Exception as e:
        print(f"❌ خطا در تست: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_system())
