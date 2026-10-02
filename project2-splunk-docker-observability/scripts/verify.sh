#!/usr/bin/env bash
# Verifies the Splunk lab through its APIs:
#   HEC health -> send one test event -> search for it -> list app objects.
# Reads SPLUNK_PASSWORD and SPLUNK_HEC_TOKEN from ../.env.
# -k is used because the container has a self-signed certificate (lab only).
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a

MGMT=https://localhost:18089
HEC=https://localhost:18088
APP=observability_lab
AUTH=(-u "admin:${SPLUNK_PASSWORD}")

search() {
  curl -sk "${AUTH[@]}" "$MGMT/services/search/jobs/export" \
    -d output_mode=json -d earliest_time=-60m -d latest_time=now \
    --data-urlencode "search=$1"
}

echo "--- HEC health"
curl -sk "$HEC/services/collector/health"; echo

echo "--- Send one test event through HEC"
marker="verify-$(date +%s)"
curl -sk "$HEC/services/collector/event" \
  -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \
  -d "{\"index\":\"app_logs\",\"sourcetype\":\"lab:app:json\",\"source\":\"verify.sh\",\"event\":{\"service\":\"verify\",\"status\":200,\"duration_ms\":1,\"message\":\"$marker\"}}"
echo

echo "--- Search for the test event (indexing takes a few seconds)"
found=0
for _ in $(seq 1 12); do
  if search "search index=app_logs source=verify.sh message=\"$marker\" | stats count" | grep -q '"count":"1"'; then
    found=1
    break
  fi
  sleep 5
done
if [ "$found" -eq 1 ]; then echo "OK    test event is searchable"; else echo "FAIL  test event not found"; exit 1; fi

echo "--- Events per service in the last 60 minutes"
search 'search index=app_logs sourcetype="lab:app:json" | stats count AS events, sum(is_error) AS errors, perc95(duration_ms) AS p95_ms BY service' |
  python3 -c 'import json,sys
for line in sys.stdin:
    r = json.loads(line).get("result")
    if r: print(r["service"].ljust(10), "events", r["events"].rjust(6), " errors", r["errors"].rjust(5), " p95_ms", r["p95_ms"])'

echo "--- Saved searches in app $APP"
curl -sk "${AUTH[@]}" "$MGMT/servicesNS/nobody/$APP/saved/searches?output_mode=json&count=0&search=eai:acl.app=$APP" |
  python3 -c 'import json,sys
for e in json.load(sys.stdin)["entry"]:
    c = e["content"]
    print(e["name"].ljust(34), "scheduled" if c["is_scheduled"] else "report   ", c["cron_schedule"])'

echo "--- Dashboards in app $APP"
curl -sk "${AUTH[@]}" "$MGMT/servicesNS/nobody/$APP/data/ui/views?output_mode=json&search=eai:acl.app=$APP" |
  python3 -c 'import json,sys; [print(e["name"], "(Dashboard Studio)" if e["content"].get("version") == "2" else "") for e in json.load(sys.stdin)["entry"]]'

echo "--- Triggered alerts"
curl -sk "${AUTH[@]}" "$MGMT/servicesNS/-/$APP/alerts/fired_alerts?output_mode=json" |
  python3 -c 'import json,sys; rows=[(e["name"], e["content"].get("triggered_alert_count")) for e in json.load(sys.stdin)["entry"] if e["name"] != "-"]; [print(n, "-", c, "time(s)") for n, c in rows] or print("none yet")'
