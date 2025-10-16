from __future__ import annotations
import asyncio, structlog
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from ..config import settings
from ..models import PriceSnapshot, utcnow
from ..exchanges.nobitex import NobitexClient
from ..exchanges.wallex import WallexClient
from ..arb.engine import ArbEngine
from ..notify.telegram import TelegramNotifier

log = structlog.get_logger()

app = FastAPI(title="Arbitrage Notifier", version="0.1.0")
engine = ArbEngine(settings.THRESHOLD_PERCENT, settings.COOLDOWN_SECONDS, settings.HYSTERESIS_DELTA_PCT)
notifier = TelegramNotifier()

state = {
    "nobitex": None,
    "wallex": None,
    "latest": {}  # symbol -> { exchange: PriceSnapshot }
}

@app.on_event("startup")
async def startup():
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(settings.LOG_LEVEL))
    app.state.nobitex = NobitexClient()
    app.state.wallex = WallexClient()
    app.state.worker_task = asyncio.create_task(worker_loop())

@app.on_event("shutdown")
async def shutdown():
    app.state.worker_task.cancel()
    try:
        await app.state.nobitex.close()
        await app.state.wallex.close()
    except Exception:
        pass

@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return PlainTextResponse(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/status")
async def status():
    latest = {}
    for sym in settings.symbols_list:
        entry = state["latest"].get(sym) or {}
        def pack(ps: PriceSnapshot | None):
            if not ps:
                return None
            return {"exchange": ps.exchange, "bid": ps.bid, "ask": ps.ask, "ts": ps.ts.isoformat()}
        latest[sym] = { k: pack(v) for k, v in entry.items() }
    return JSONResponse({"symbols": settings.symbols_list, "latest": latest})

async def worker_loop():
    nb = app.state.nobitex
    wx = app.state.wallex
    symbols = settings.symbols_list
    while True:
        try:
            nb_data = await nb.fetch_ticker(symbols)
            wx_data = await wx.fetch_ticker(symbols)

            for sym in symbols:
                a = nb_data.get(sym)
                b = wx_data.get(sym)
                if a:
                    state["latest"].setdefault(sym, {})["nobitex"] = a
                if b:
                    state["latest"].setdefault(sym, {})["wallex"] = b

                if a and b:
                    opp1 = engine.evaluate(a, b)
                    opp2 = engine.evaluate(b, a)
                    for opp in (opp1, opp2):
                        if opp:
                            await notifier.send(opp)

        except Exception as e:
            log.error("worker_error", err=str(e))

        await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
