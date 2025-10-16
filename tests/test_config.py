from src.config import Settings

def test_symbols_parsing():
    s = Settings(SYMBOLS="BTC/USDT, USDT/IRT , ETH/USDT")
    assert s.symbols_list == ["BTC/USDT", "USDT/IRT", "ETH/USDT"]

def test_defaults_present():
    s = Settings()
    assert s.APP_PORT == 8000
    assert s.HTTP_TIMEOUT_SECONDS > 0
