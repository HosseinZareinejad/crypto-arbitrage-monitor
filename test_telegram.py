import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.notify.telegram import TelegramNotifier

async def test_telegram():
    notifier = TelegramNotifier()
    message = "Test message"
    
    print("sending message...")
    await notifier.send_text(message)
    print("message sent")

if __name__ == "__main__":
    asyncio.run(test_telegram())
