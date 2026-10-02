"""Tiny demo service for the alerting lab.

- Simulates HTTP traffic in a background thread and exposes Prometheus
  metrics on /metrics (text format, no external libraries).
- POST /chaos?error_rate=0.3&latency_ms=800 changes the simulated behaviour
  so you can make alerts fire on purpose.
- POST /webhook receives Alertmanager notifications and prints them.
"""

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", "8080"))
HANDLERS = ["/api/orders", "/api/users"]
BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]

state = {
    "error_rate": float(os.environ.get("ERROR_RATE", "0.01")),
    "latency_ms": float(os.environ.get("LATENCY_MS", "120")),
}
lock = threading.Lock()
requests_total = {}  # (handler, code) -> count
bucket_counts = {h: [0] * len(BUCKETS) for h in HANDLERS}
duration_sum = {h: 0.0 for h in HANDLERS}
duration_count = {h: 0 for h in HANDLERS}


def simulate_traffic():
    """Record about 20 fake requests per second."""
    while True:
        with lock:
            error_rate = state["error_rate"]
            mean = state["latency_ms"] / 1000.0
        handler = random.choice(HANDLERS)
        code = "500" if random.random() < error_rate else "200"
        latency = random.expovariate(1.0 / mean) if mean > 0 else 0.0
        with lock:
            key = (handler, code)
            requests_total[key] = requests_total.get(key, 0) + 1
            for i, bound in enumerate(BUCKETS):
                if latency <= bound:
                    bucket_counts[handler][i] += 1
            duration_sum[handler] += latency
            duration_count[handler] += 1
        time.sleep(0.05)


def render_metrics():
    lines = [
        "# HELP http_requests_total Total HTTP requests by handler and status code.",
        "# TYPE http_requests_total counter",
    ]
    with lock:
        for (handler, code), value in sorted(requests_total.items()):
            lines.append(f'http_requests_total{{handler="{handler}",code="{code}"}} {value}')
        lines += [
            "# HELP http_request_duration_seconds HTTP request latency.",
            "# TYPE http_request_duration_seconds histogram",
        ]
        for handler in HANDLERS:
            for bound, value in zip(BUCKETS, bucket_counts[handler]):
                lines.append(
                    f'http_request_duration_seconds_bucket{{handler="{handler}",le="{bound}"}} {value}'
                )
            lines.append(
                f'http_request_duration_seconds_bucket{{handler="{handler}",le="+Inf"}} {duration_count[handler]}'
            )
            lines.append(f'http_request_duration_seconds_sum{{handler="{handler}"}} {duration_sum[handler]:.6f}')
            lines.append(f'http_request_duration_seconds_count{{handler="{handler}"}} {duration_count[handler]}')
        lines += [
            "# HELP demo_error_rate_setting Configured error rate (0-1).",
            "# TYPE demo_error_rate_setting gauge",
            f"demo_error_rate_setting {state['error_rate']}",
        ]
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/plain; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/metrics":
            self._send(200, render_metrics(), "text/plain; version=0.0.4")
        elif path == "/healthz":
            self._send(200, "ok\n")
        else:
            self._send(404, "not found\n")

    def do_POST(self):
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        if url.path == "/chaos":
            params = parse_qs(url.query)
            with lock:
                if "error_rate" in params:
                    state["error_rate"] = min(max(float(params["error_rate"][0]), 0.0), 1.0)
                if "latency_ms" in params:
                    state["latency_ms"] = max(float(params["latency_ms"][0]), 0.0)
                current = dict(state)
            print(f"chaos settings changed: {current}", flush=True)
            self._send(200, json.dumps(current) + "\n", "application/json")
        elif url.path == "/webhook":
            try:
                payload = json.loads(body or b"{}")
            except json.JSONDecodeError:
                self._send(400, "bad json\n")
                return
            for alert in payload.get("alerts", []):
                name = alert.get("labels", {}).get("alertname")
                severity = alert.get("labels", {}).get("severity")
                print(f"ALERT {alert.get('status')}: {name} severity={severity}", flush=True)
            self._send(200, "received\n")
        else:
            self._send(404, "not found\n")

    def log_message(self, format, *args):  # keep scrape requests out of the logs
        pass


if __name__ == "__main__":
    threading.Thread(target=simulate_traffic, daemon=True).start()
    print(f"demo-app listening on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
