---
description: >
  Inspect Kubernetes workloads, logs, events, nodes and namespaces for scheduling, rollout and service failures. Mutations require a requested change and effective cluster permission; persist configuration through the system that owns desired state.
---

# kubernetes

Bundled endpoint: `http://mcp-kubernetes.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-demo` k3s deployment exposes this service inside the cluster.
See [in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

Identify the deployment's target cluster and identity. Select toolsets and RBAC
for the intended task. Do not assume Secret reads, deletion, exec, Helm or workload
writes are allowed or denied merely because a tool appears or is absent in discovery.

Review cluster-wide and namespaced permissions, including Secret-backed release
storage when Helm is needed. A server may expose calls that return 403 under its
identity. Verify representative reads and the configured write boundary without
expanding privilege to make a failed call succeed.

Durable configuration follows the installation's owning repository or change
system. Direct mitigation must account for reconcilers that could overwrite it.

Upstream: https://github.com/containers/kubernetes-mcp-server
