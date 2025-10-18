import asyncio
import httpx
import json

async def test_wallex_api():
    # Direct test of Wallex API
    api_key = "16741|zbJe8aGB5FrPtrC3WEuOGMq5QplAiTQGBudvKt3w"
    headers = {"x-api-key": api_key}

    async with httpx.AsyncClient() as client:
        # Test BTC/USDT
        url = "https://api.wallex.ir/v1/trades?symbol=BTCUSDT"
        print(f"Requesting: {url}")

        try:
            response = await client.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("API Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                if data.get("success") and "result" in data:
                    trades = data["result"].get("latestTrades", [])
                    print(f"\nNumber of trades: {len(trades)}")

                    if trades:
                        # Show a few recent trades
                        for i, trade in enumerate(trades[:3]):
                            print(f"\nTrade {i+1}:")
                            print(f"  Symbol: {trade.get('symbol')}")
                            print(f"  Price: {trade.get('price')}")
                            print(f"  Quantity: {trade.get('quantity')}")
                            print(f"  Is Buy: {trade.get('isBuyOrder')}")
                            print(f"  Timestamp: {trade.get('timestamp')}")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    asyncio.run(test_wallex_api())
