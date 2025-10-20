from fastapi import FastAPI
from starlette.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
import asyncio

from ..config import settings
from ..adapters.nobitex import NobitexClient
from ..adapters.wallex import WallexClient
from ..domain.arbitrage_engine import ArbEngine
from ..consolidated_imports import TelegramNotifier
from ..domain.models import PriceSnapshot

app = FastAPI(title="Arbitrage Notifier", version="1.0.0")

engine = ArbEngine(settings.THRESHOLD_PERCENT, settings.COOLDOWN_SECONDS, settings.HYSTERESIS_DELTA_PCT)
notifier = TelegramNotifier()

state = {"latest": {}}

@app.on_event("startup")
async def startup():
    app.state.nobitex = NobitexClient()
    app.state.wallex = WallexClient()
    if settings.ENABLE_WORKER:
        app.state.worker_task = asyncio.create_task(worker_loop())

@app.on_event("shutdown")
async def shutdown():
    task = getattr(app.state, "worker_task", None)
    if task:
        task.cancel()
    try:
        await app.state.nobitex.close()
        await app.state.wallex.close()
    except Exception:
        pass

@app.get("/healthz")
def healthz():
    return {"status": "ok", "worker_enabled": settings.ENABLE_WORKER}

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

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
                    for opp in (engine.evaluate(a, b), engine.evaluate(b, a)):
                        if opp:
                            await notifier.send(opp)
        except Exception:
            pass
        await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
