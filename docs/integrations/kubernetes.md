---
description: >
  Inspect Kubernetes workloads, logs, events, nodes and namespaces for scheduling, rollout and service failures. Mutations require a requested change and effective cluster permission; persist configuration through the system that owns desired state.
---

# kubernetes

Operator reference for a separately registered integration. This file is not
auto-synced as a bundled MCP declaration. Use the description as a starting
point and adjust it to the deployed tools and permission boundary.

Register the endpoint of a Kubernetes MCP deployment and identify its target
cluster and identity. Select toolsets and RBAC for the intended task. Do not
assume Secret reads, deletion, exec, Helm or workload writes are allowed or denied
merely because a tool appears or is absent in discovery.

Review cluster-wide and namespaced permissions, including Secret-backed release
storage when Helm is needed. A server may expose calls that return 403 under its
identity. Verify representative reads and the configured write boundary without
expanding privilege to make a failed call succeed.

Durable configuration follows the installation's owning repository or change
system. Direct mitigation must account for reconcilers that could overwrite it.

Upstream: https://github.com/containers/kubernetes-mcp-server
