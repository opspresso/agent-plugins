---
description: >
  Inspect Kubernetes resources, pod logs, events, nodes and namespaces for
  workload, scheduling and rollout failures, with requested workload writes
  for temporary mitigation. Durable changes belong in GitOps; this deployment
  denies Secret reads, deletion and pods/exec even when those tools are listed.
---

# kubernetes

## Connection and identity

The bundled service is internal to `agent-mcps` with no ingress.
`MCP_INTERNAL_HOST_SUFFIXES` must allow its suffix. The registry has no caller
credential; the server uses its own Kubernetes ServiceAccount.

## Effective permissions

Deployment RBAC permits view-level reads excluding core Secrets.
`--toolsets core` excludes Helm operations, which require Secret-backed releases.

Writes allow create, update and patch on workload objects: pods, services,
configmaps, PVCs and the apps, batch, autoscaling, policy, networking and gateway
kinds. RBAC, CRDs, StorageClasses, ServiceAccounts, nodes, ExternalSecrets and
Argo CD Applications are not writable.

No delete or `pods/exec` permission is granted. The pod does not use
`--read-only`, so deletion and exec tools may be discoverable but return 403.
Tool visibility is not the permission boundary.

RBAC and toolset changes belong to the `mcp-kubernetes` chart in
argocd-env-demo. Verify representative resource access after deployment changes.
Durable workload configuration belongs in the GitOps repository.

Upstream: https://github.com/containers/kubernetes-mcp-server
