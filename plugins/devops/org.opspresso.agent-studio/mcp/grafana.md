---
description: >
  Explore Grafana dashboards, datasources, metrics, logs, alerting and incidents for the connected environment. Available operations depend on enabled tool categories and datasource permissions; writes require a requested change.
---

# grafana

Bundled endpoint: `http://mcp-grafana.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-demo` k3s deployment exposes this service inside the cluster.
See [in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

Configure Grafana authentication, datasources and exposed tool categories in
the deployment. Do not assume username and password authentication or that all
datasources describe Kubernetes.

Keep the registered description consistent with enabled categories. Validate a
representative datasource query after changes. Successful tool discovery does
not establish Grafana or datasource authorization.

Upstream: https://github.com/grafana/mcp-grafana
