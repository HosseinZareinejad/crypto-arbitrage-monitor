# Arbitrage Notifier (Nobitex vs Wallex)

FastAPI service that fetches crypto prices from Nobitex and Wallex, detects arbitrage opportunities, sends Telegram alerts, and exposes Prometheus metrics with Grafana dashboard.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Prometheus/Grafana)
- Telegram Bot Token

### 1. Setup Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your Telegram token and chat ID
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Services

**Option A: All-in-one (Recommended)**

```bash
# Start main service
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# In another terminal - Start Prometheus
prometheus --config.file=prometheus.yml --web.listen-address=:9090

# In another terminal - Start Grafana
docker run -d --name grafana -p 3000:3000 grafana/grafana
```

**Option B: Using batch files (Windows)**

```bash
run_local.bat      # Starts the service
run_prometheus.bat # Starts Prometheus
run_grafana.bat    # Starts Grafana
```

### 4. Access Services

- **Main Service**: http://localhost:8000
- **Health Check**: http://localhost:8000/healthz
- **Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 📊 Monitoring

### Prometheus Metrics

- `requests_total{exchange, outcome}` - HTTP request counters
- `http_client_latency_seconds{exchange}` - Request latency histogram
- `last_bid{exchange, symbol}` - Last bid prices
- `last_ask{exchange, symbol}` - Last ask prices
- `last_diff_pct{symbol, direction}` - Price differences
- `alerts_sent_total{symbol, direction}` - Telegram alerts sent

### Grafana Dashboard

Import `grafana_dashboard.json` for pre-configured monitoring panels:

- HTTP latency trends
- Request success/error rates
- Live price feeds
- Arbitrage opportunity alerts

## ⚙️ Configuration

### Environment Variables

```bash
# Service
ENABLE_WORKER=true
THRESHOLD_PERCENT=0.1    # Lower for testing
COOLDOWN_SECONDS=45
HYSTERESIS_DELTA_PCT=0.15

# Telegram
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Exchanges
NOBITEX_API_KEY=your_nobitex_key
WALLEX_API_KEY=your_wallex_key
```

### Adding New Symbols

Edit `SYMBOLS` in `.env`:

```bash
SYMBOLS=BTC/USDT,USDT/IRT,ETH/USDT
```

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI App   │
│  (Port 8000)    │
└─────────┬───────┘
          │
    ┌─────▼─────┐
    │  Worker   │
    │   Loop    │
    └─────┬─────┘
          │
    ┌─────▼─────┐    ┌─────────────┐
    │  Fetch    │───▶│  Nobitex    │
    │  Prices   │    │  API        │
    └─────┬─────┘    └─────────────┘
          │
    ┌─────▼─────┐    ┌─────────────┐
    │  Compute  │───▶│   Wallex    │
    │Arbitrage  │    │  API        │
    └─────┬─────┘    └─────────────┘
          │
    ┌─────▼─────┐
    │ Telegram  │
    │  Alerts   │
    └───────────┘
```

## 🧪 Testing

### Test Individual Components

```bash
# Test Telegram
python tests/test_telegram.py

# Test Exchanges
python tests/test_nobitex_simple.py
python tests/test_wallex_simple.py

# Test Worker
python main_worker.py
```

### Run All Tests

```bash
pytest tests/
```

## 🔧 Development

### Code Quality

```bash
ruff check .          # Linting
ruff format .         # Formatting
mypy --ignore-missing-imports .  # Type checking
```

### Adding New Exchanges

1. Create new client in `src/exchanges/`
2. Add symbol mapping in `src/exchanges/common.py`
3. Register in `src/worker/fetch.py`

## 📝 Notes

- All timestamps are UTC
- Telegram is optional - service runs without it
- Use low `THRESHOLD_PERCENT` for testing
- Check logs for debugging
