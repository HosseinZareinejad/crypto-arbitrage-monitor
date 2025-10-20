@echo off
echo ========================================
echo    Arbitrage Notifier - Full System
echo ========================================
echo.

echo [1/3] Starting Arbitrage Service...
start "Arbitrage Service" cmd /k "uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Prometheus...
start "Prometheus" cmd /k "prometheus --config.file=prometheus.yml --web.listen-address=:9090"

echo [3/3] Starting Grafana...
start "Grafana" cmd /k "docker run --rm -p 3000:3000 grafana/grafana"

echo.
echo ========================================
echo    Services Starting...
echo ========================================
echo.
echo Arbitrage Service: http://localhost:8000
echo Health Check:      http://localhost:8000/healthz
echo Metrics:           http://localhost:8000/metrics
echo Prometheus:        http://localhost:9090
echo Grafana:           http://localhost:3000 (admin/admin)
echo.
echo Press any key to open all services in browser...
pause >nul

start http://localhost:8000
start http://localhost:8000/healthz
start http://localhost:8000/metrics
start http://localhost:9090
start http://localhost:3000

echo All services opened in browser!
