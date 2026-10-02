#!/usr/bin/env bash
# Checks that every component is up and wired together.
set -euo pipefail

PROM=http://localhost:19090
AM=http://localhost:19093
GRAFANA=http://localhost:13000
failures=0

check() {
  local name=$1 url=$2
  if curl -fsS -o /dev/null "$url"; then
    echo "OK    $name"
  else
    echo "FAIL  $name ($url)"
    failures=$((failures + 1))
  fi
}

check "Prometheus ready" "$PROM/-/ready"
check "Alertmanager ready" "$AM/-/ready"
check "Grafana health" "$GRAFANA/api/health"
check "node-exporter metrics" "http://localhost:19100/metrics"

echo "--- Prometheus targets (job health)"
curl -fsS "$PROM/api/v1/targets" |
  python3 -c 'import json,sys; [print(t["labels"]["job"].ljust(14), t["health"]) for t in json.load(sys.stdin)["data"]["activeTargets"]]'

echo "--- Loaded alert rules"
curl -fsS "$PROM/api/v1/rules?type=alert" |
  python3 -c 'import json,sys; [print(r["name"], "-", r["state"]) for g in json.load(sys.stdin)["data"]["groups"] for r in g["rules"]]'

echo "--- Alertmanager sees Prometheus alerts"
curl -fsS "$AM/api/v2/alerts" | python3 -c 'import json,sys; a=json.load(sys.stdin); print(len(a), "alert(s):", ", ".join(sorted({x["labels"]["alertname"] for x in a})) or "none")'

if [ "$failures" -gt 0 ]; then
  echo "$failures check(s) failed"
  exit 1
fi
