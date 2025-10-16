# Arbitrage Notifier (Nobitex vs Wallex)

FastAPI service that fetches crypto orderbooks from Nobitex and Wallex, detects arbitrage opportunities, sends Telegram alerts, and exposes Prometheus metrics. Docker Compose includes Prometheus and Grafana with a prebuilt dashboard.

## Quickstart

1. Create env file:

```bash
cp .env.example .env
# fill TELEGRAM_TOKEN and TELEGRAM_CHAT_ID (optional)
```

2. Run locally with Docker:

```bash
docker-compose up -d
```

- App: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

## Environment Variables

See `.env.example` for full list.

## Development (without Docker)

```bash
python -m venv .venv
. .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.app.main:app --reload
```

## Testing & Linting

```bash
pytest -q
ruff check .
ruff format .
mypy --ignore-missing-imports .
```

## Adding Symbols or Exchanges

- Edit `SYMBOLS` in env (comma-separated, e.g., `BTC/USDT,USDT/IRT`).
- Add symbol mappings in `src/exchanges/common.py` if an exchange uses different tickers.
- To add an exchange, copy an existing client (`nobitex.py`, `wallex.py`) and register/use in `app/main.py`.

## Architecture (ASCII)

```
[APScheduler/Worker Loop]
        | (async fetch)
        v
 [Nobitex]    [Wallex]
    \            /
     \          /
     [Snapshots -> ArbEngine] --(opportunity)--> [Telegram]
                |
            [Metrics]
                |
          [/metrics for Prometheus] -> [Grafana]
```

## Notes

- UTC timestamps and ISO-8601 in alerts.
- Telegram is optional; service runs without it and logs nothing if unset.
