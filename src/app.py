import asyncio
from fastapi import FastAPI
from starlette.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from .worker.loop import run_worker
from .config import settings

app = FastAPI(title="Arbitrage Notifier", version="1.0.0")

@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "worker_enabled": settings.ENABLE_WORKER}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    data = generate_latest()   # uses default REGISTRY where your metrics live
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
async def startup():
    """Startup event - launch worker if enabled"""
    if settings.ENABLE_WORKER:
        print("🚀 Starting arbitrage worker...")
        asyncio.create_task(run_worker())
    else:
        print("⏸️ Worker disabled in config")

@app.get("/")
def root():
    """Root endpoint with basic info"""
    return {
        "service": "Arbitrage Notifier",
        "version": "1.0.0",
        "endpoints": {
            "health": "/healthz",
            "metrics": "/metrics"
        }
    }
