import httpx
import json
from src.exchanges.nobitex import NobitexClient
from src.exchanges.wallex import WallexClient

class MockTransport(httpx.BaseTransport):
    def __init__(self, handler):
        self.handler = handler
    def handle_request(self, request):
        return self.handler(request)

def nobitex_handler(request: httpx.Request) -> httpx.Response:
    data = {"asks": [["101", "1"]], "bids": [["99", "1"]]}
    return httpx.Response(200, json=data)

def wallex_handler(request: httpx.Request) -> httpx.Response:
    data = {"result": {"BTCUSDT": {"asks": [["102", "1"]], "bids": [["100", "1"]]}}}
    return httpx.Response(200, json=data)

def test_nobitex_fetch_basic():
    transport = MockTransport(nobitex_handler)
    client = httpx.AsyncClient(transport=transport)
    nb = NobitexClient(client=client)
    data = nb  # silence linter for now


def test_wallex_fetch_basic():
    transport = MockTransport(wallex_handler)
    client = httpx.AsyncClient(transport=transport)
    wx = WallexClient(client=client)
    data = wx  # silence linter for now
