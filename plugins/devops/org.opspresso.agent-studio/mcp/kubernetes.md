---
description: >
  Inspect Kubernetes workloads, logs, events, nodes and namespaces for scheduling, rollout and service failures. Read-only: the bundled deployment offers no write tools. Make changes through the repository that owns desired state.
icon: brand-kubernetes
---

# kubernetes

Bundled endpoint: `http://mcp-kubernetes.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-apps` k3s deployment exposes this service inside the cluster.
See [in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

The bundled deployment runs with `--read-only` and view-only RBAC. It cannot
read Secrets, run Helm, exec into pods, or create, change or delete resources.
Only Agent Studio execution pods can reach it.

Another installation may enable writes. Do not treat tool discovery as
authorization; verify representative reads and the configured write boundary
without expanding privilege to make a failed call succeed.

Durable configuration follows the installation's owning repository or change
system. Direct mitigation must account for reconcilers that could overwrite it.

Upstream: https://github.com/containers/kubernetes-mcp-server
