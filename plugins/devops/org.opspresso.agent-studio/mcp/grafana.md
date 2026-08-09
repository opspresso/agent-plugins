---
description: "Query Grafana: dashboards, datasources, Prometheus and Loki queries, alerting and incidents."
---

# grafana

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

No credential on the entry: nothing routes to the Service from outside the
cluster, and upstream authenticates to Grafana itself with basic auth from the
pod's environment (`GRAFANA_USERNAME`/`GRAFANA_PASSWORD`) rather than from the
caller.

What the entry actually exposes is a deployment question, not a repository one:
upstream ships far more tool categories than it enables, and the rest come from
`--enabled-tools` on the pod. The description above names what this deployment
turns on — change one without the other and it goes stale.

Upstream: https://github.com/grafana/mcp-grafana
