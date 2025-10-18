#!/usr/bin/env python3
"""
اجرای مستقل Worker آربیتراژ
"""
import asyncio
import sys
import os

# اضافه کردن src به path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.worker.loop import run_worker

if __name__ == "__main__":
    print("🤖 شروع Worker آربیتراژ...")
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\n⏹️ Worker متوقف شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
