import asyncio
import httpx
import json

async def test_nobitex_api():
    # Direct test of Nobitex API
    api_key = "c3ffde1688537f4af594529b6d7d8541306426a0"
    headers = {"x-api-key": api_key} if api_key else {}

    async with httpx.AsyncClient() as client:
        # Test BTC/USDT
        url = "https://apiv2.nobitex.ir/v3/orderbook/BTCUSDT"
        print(f"Requesting: {url}")

        try:
            response = await client.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("API Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                if data.get("status") == "ok":
                    bids = data.get("bids", [])
                    asks = data.get("asks", [])
                    print(f"\nNumber of bids: {len(bids)}")
                    print(f"Number of asks: {len(asks)}")

                    if bids:
                        best_bid = float(bids[0][0])
                        print(f"Best bid: {best_bid}")

                    if asks:
                        best_ask = float(asks[0][0])
                        print(f"Best ask: {best_ask}")

                    last_trade = data.get("lastTradePrice")
                    if last_trade:
                        print(f"Last trade price: {last_trade}")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    asyncio.run(test_nobitex_api())
