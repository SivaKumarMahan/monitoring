# Uses promtool/amtool from the official images, so nothing to install.
PROM_IMAGE := prom/prometheus:v3.15.0
AM_IMAGE   := prom/alertmanager:v0.34.1
DOCKER_RUN := docker run --rm -v "$(CURDIR)":/work -w /work

.PHONY: check test up verify down

check: ## Lint Prometheus config, rules and Alertmanager config
	$(DOCKER_RUN) --entrypoint promtool $(PROM_IMAGE) check config --syntax-only prometheus/prometheus.yml
	$(DOCKER_RUN) --entrypoint promtool $(PROM_IMAGE) check rules prometheus/rules/slo-alerts.yml
	$(DOCKER_RUN) --entrypoint amtool $(AM_IMAGE) check-config alertmanager/alertmanager.yml
	$(DOCKER_RUN) --entrypoint amtool $(AM_IMAGE) config routes test --config.file=alertmanager/alertmanager.yml --verify.receivers=pager-webhook severity=page
	$(DOCKER_RUN) --entrypoint amtool $(AM_IMAGE) config routes test --config.file=alertmanager/alertmanager.yml --verify.receivers=ticket-webhook severity=ticket

test: ## Run alert rule unit tests
	$(DOCKER_RUN) --entrypoint promtool $(PROM_IMAGE) test rules prometheus/tests/slo-alerts.test.yml

up: ## Start the stack
	docker compose up -d --build

verify: ## Quick health check of all endpoints
	./scripts/verify.sh

down: ## Stop the stack and delete its volumes
	docker compose down -v
