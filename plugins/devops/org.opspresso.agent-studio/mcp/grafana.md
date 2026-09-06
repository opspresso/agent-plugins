---
description: >
  Investigate Kubernetes metrics and logs with Grafana dashboards, datasources,
  Prometheus and Loki queries, alerting and incidents.
  Available operations depend on the deployment's enabled tool categories.
---

# grafana

The bundled service is internal to `agent-mcps` with no ingress.
`MCP_INTERNAL_HOST_SUFFIXES` must allow its suffix or sync reports `invalid-url`.
There is no registry credential; the pod authenticates to Grafana with
`GRAFANA_USERNAME` and `GRAFANA_PASSWORD` from its environment.

The pod's `--enabled-tools` controls exposed categories. The description reflects
dashboards, datasources, Prometheus/Loki queries, alerting and incidents.
Keep it synchronized with deployment flags.

After credential or datasource changes, verify a representative query.
Successful MCP discovery does not establish Grafana or datasource access.

Upstream: https://github.com/grafana/mcp-grafana
