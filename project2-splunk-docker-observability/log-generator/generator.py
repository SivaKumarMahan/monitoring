"""Sends fake web-service access events to Splunk HTTP Event Collector (HEC).

Only the Python standard library is used. Settings come from environment
variables (see docker-compose.yml). The HEC token is never printed.
"""

import json
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid

HEC_URL = os.environ.get("HEC_URL", "https://splunk:8088").rstrip("/")
HEC_TOKEN = os.environ["HEC_TOKEN"]
INDEX = os.environ.get("HEC_INDEX", "app_logs")
SOURCETYPE = os.environ.get("HEC_SOURCETYPE", "lab:app:json")
EVENTS_PER_SECOND = float(os.environ.get("EVENTS_PER_SECOND", "5"))
ERROR_RATE = float(os.environ.get("ERROR_RATE", "0.02"))
LATENCY_MS = float(os.environ.get("LATENCY_MS", "150"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))
# The Splunk container uses a self-signed certificate. Verification is off by
# default for this local lab only. Set HEC_VERIFY_TLS=true with a real cert.
VERIFY_TLS = os.environ.get("HEC_VERIFY_TLS", "false").lower() == "true"

SERVICES = {
    "checkout": ["/api/cart", "/api/checkout", "/api/payment"],
    "catalog": ["/api/products", "/api/search"],
    "users": ["/api/login", "/api/profile"],
}
METHODS = ["GET", "GET", "GET", "POST"]

ssl_ctx = ssl.create_default_context()
if not VERIFY_TLS:
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE


def make_event():
    service = random.choice(list(SERVICES))
    roll = random.random()
    if roll < ERROR_RATE:
        status = random.choice([500, 502, 503])
    elif roll < ERROR_RATE + 0.05:
        status = random.choice([400, 401, 404])
    else:
        status = 200
    duration = round(random.expovariate(1.0 / LATENCY_MS), 1)
    return {
        "time": round(time.time(), 3),
        "host": "log-generator",
        "source": f"lab:{service}",
        "sourcetype": SOURCETYPE,
        "index": INDEX,
        "event": {
            "service": service,
            "method": random.choice(METHODS),
            "path": random.choice(SERVICES[service]),
            "status": status,
            "duration_ms": duration,
            "level": "ERROR" if status >= 500 else "INFO",
            "trace_id": uuid.uuid4().hex,
            "message": f"request handled with status {status}",
        },
    }


def post(path, body=None):
    req = urllib.request.Request(
        f"{HEC_URL}{path}",
        data=body,
        headers={"Authorization": f"Splunk {HEC_TOKEN}", "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
        return resp.status, resp.read().decode()


def wait_for_hec():
    while True:
        try:
            status, _ = post("/services/collector/health")
            if status == 200:
                print("HEC is healthy, start sending", flush=True)
                return
        except (urllib.error.URLError, OSError) as err:
            print(f"waiting for HEC: {err}", flush=True)
        time.sleep(10)


def main():
    wait_for_hec()
    sent = 0
    while True:
        # HEC accepts several JSON objects in one request body (no array).
        batch = "".join(json.dumps(make_event()) for _ in range(BATCH_SIZE)).encode()
        try:
            status, text = post("/services/collector/event", batch)
            sent += BATCH_SIZE
            if sent % (BATCH_SIZE * 30) == 0:
                print(f"sent {sent} events (last status {status})", flush=True)
        except urllib.error.HTTPError as err:
            print(f"HEC rejected batch: {err.code} {err.read().decode()}", file=sys.stderr, flush=True)
        except (urllib.error.URLError, OSError) as err:
            print(f"HEC not reachable: {err}", file=sys.stderr, flush=True)
        time.sleep(BATCH_SIZE / EVENTS_PER_SECOND)


if __name__ == "__main__":
    main()
