from prometheus_client import Counter, Gauge, Histogram

requests_total = Counter(
    "requests_total", "Total HTTP requests to exchanges", ["exchange", "outcome"]
)

fetch_errors_total = Counter(
    "fetch_errors_total", "Total fetch errors", ["exchange"]
)

alerts_sent_total = Counter(
    "alerts_sent_total", "Total arbitrage alerts sent", ["symbol", "direction"]
)

http_client_latency_seconds = Histogram(
    "http_client_latency_seconds", "HTTP client latency", ["exchange"]
)

last_diff_pct = Gauge(
    "last_diff_pct", "Last observed percentage difference", ["symbol", "direction"]
)

last_bid = Gauge("last_bid", "Last best bid", ["exchange", "symbol"])
last_ask = Gauge("last_ask", "Last best ask", ["exchange", "symbol"])
