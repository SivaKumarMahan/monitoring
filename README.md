# Monitoring and observability projects

Hands-on monitoring projects: metrics with Prometheus and Grafana on Kubernetes (AKS), log analytics and alerting
with Splunk, and SLO-based alert rules that have their own unit tests. Each project has its own README with
architecture, steps, tests and interview talking points.

## Projects

| Folder | What it shows | Main tools | Status |
| --- | --- | --- | --- |
| [`project1/`](project1/README.md) | Self-managed Prometheus, Grafana and Node Exporter on AKS with Kubernetes service discovery and RBAC | AKS, Azure CLI, kubectl, Kustomize, Prometheus, Grafana, Node Exporter | Static checks only |
| [`project2-splunk-docker-observability/`](project2-splunk-docker-observability/README.md) | Splunk Enterprise with HEC, a log generator, and a Splunk app as code (index, sourcetype, alerts, Dashboard Studio dashboard) | Splunk Enterprise, HEC, SPL, Docker Compose, Python | Validated locally |
| [`project3-prometheus-alerting/`](project3-prometheus-alerting/README.md) | SLO burn-rate alerts with `promtool` unit tests, Alertmanager routing and inhibition, provisioned Grafana | Prometheus, Alertmanager, Grafana, node-exporter, promtool, Docker Compose | Validated locally |

## Prerequisites

| Tool | Needed for |
| --- | --- |
| Docker with the Compose plugin | Projects 2 and 3 |
| `make`, `curl`, `python3` | Projects 2 and 3 (verify scripts, shortcuts) |
| Azure CLI and an Azure subscription | Project 1 (creates an AKS cluster) |
| `kubectl` 1.28+ | Project 1 |
| `promtool`, `amtool`, `kubeconform` (optional) | Local validation. Project 3 can run them from Docker images instead. |

## How to use

1. Clone the repo and pick a project.
2. Read its README. Copy `.env.example` to `.env` where there is one, and set your own values.
3. Follow the steps, then run the project's verify step.
4. Clean up when you are done (`docker compose down -v`, or delete the Azure resource group).

The two Docker projects use different host ports, so they can run at the same time:

| Project | Host ports |
| --- | --- |
| project2 (Splunk) | 18000 (Web), 18088 (HEC), 18089 (REST API) |
| project3 (Prometheus) | 19090 (Prometheus), 19093 (Alertmanager), 13000 (Grafana), 19100 (node-exporter) |

## Repo layout

```text
.
├── .github/workflows/validate.yml        # CI: kubeconform, promtool, amtool, rule unit tests, shellcheck
├── project1/                              # AKS: Prometheus + Grafana + Node Exporter (plain YAML + Kustomize)
├── project2-splunk-docker-observability/  # Splunk Enterprise + HEC + log generator + app as code
│   ├── docker-compose.yml
│   ├── log-generator/
│   ├── scripts/verify.sh
│   └── splunk/apps/observability_lab/     # indexes, props, savedsearches, dashboard
└── project3-prometheus-alerting/          # Prometheus + Alertmanager + Grafana + rule unit tests
    ├── docker-compose.yml
    ├── prometheus/{rules,tests}/
    ├── alertmanager/
    ├── grafana/
    └── demo-app/
```

## CI

`.github/workflows/validate.yml` runs on every push and pull request:

- Project 1: `kubectl kustomize` piped into `kubeconform -strict`, `promtool check config`, `shellcheck`.
- Project 2: `docker compose config`, Python syntax check, Dashboard Studio XML/JSON check.
- Project 3: `make check` (promtool, amtool, routing tests) and `make test` (`promtool test rules`).

No secrets are needed for CI.

## Skills demonstrated

- Kubernetes monitoring on AKS: service discovery, least-privilege RBAC for Prometheus, DaemonSets with host mounts.
- Prometheus: scrape configs, recording rules, multi-window multi-burn-rate SLO alerts, `predict_linear` capacity alerts.
- Testing alert rules as code with `promtool test rules`, including negative (quiet) cases.
- Alertmanager: severity-based routing, grouping, throttling and inhibit rules, checked with `amtool`.
- Grafana provisioning: data sources and dashboards from files, no manual clicks.
- Splunk: HEC ingestion, `indexes.conf` retention and size caps, search-time JSON extraction in `props.conf`,
  scheduled alerts with throttling in `savedsearches.conf`, Dashboard Studio, REST API automation with `curl`.
- Docker Compose: health checks, `depends_on` conditions, one-shot init jobs, memory limits, non-root containers.
- Secrets hygiene: passwords and tokens from git-ignored `.env` files or Kubernetes Secrets, never in Git.
- Shell scripts with `set -euo pipefail` and `shellcheck`. CI with GitHub Actions.
