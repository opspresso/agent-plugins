---
description: >
  Explore Grafana dashboards, datasources, metrics, logs, alerting and incidents for the connected environment. Available operations depend on enabled tool categories and datasource permissions; writes require a requested change.
---

# grafana

Operator reference for a separately registered integration. This file is not
auto-synced as a bundled MCP declaration. Use the description as a starting
point and adjust it to the deployed tools and permission boundary.

Register a reachable Grafana MCP endpoint. Configure Grafana authentication,
datasources and exposed tool categories in the deployment. Do not assume username
and password authentication or that all datasources describe Kubernetes.

Keep the registered description consistent with enabled categories. Validate a
representative datasource query after changes. Successful tool discovery does
not establish Grafana or datasource authorization.

Upstream: https://github.com/grafana/mcp-grafana
