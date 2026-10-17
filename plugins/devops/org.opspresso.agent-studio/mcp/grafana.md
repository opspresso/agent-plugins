---
description: >
  Explore Grafana dashboards, datasources, metrics, logs, alerting and incidents for the connected environment. Read-only: the bundled deployment offers no write tools and no raw SQL query tools. Available reads depend on datasource permissions.
---

# grafana

Bundled endpoint: `http://mcp-grafana.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-apps` k3s deployment exposes this service inside the cluster.
See [in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

The bundled deployment runs with `--disable-write`, which also removes the raw
SQL tools. Configure Grafana authentication, datasources and exposed tool
categories in the deployment. Do not assume username and password authentication or that all
datasources describe Kubernetes.

Keep the registered description consistent with enabled categories. Validate a
representative datasource query after changes. Successful tool discovery does
not establish Grafana or datasource authorization.

Upstream: https://github.com/grafana/mcp-grafana
