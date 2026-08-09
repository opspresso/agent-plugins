---
description: "Inspect and change a Kubernetes cluster: resources, pod logs, events, nodes and namespaces, plus creating, updating and scaling workloads."
---

# kubernetes

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix, same as the other
entries here.

No credential on the entry: nothing routes to the Service from outside the
cluster, and the server reaches the cluster with its own ServiceAccount rather
than anything from the caller.

What a run may do is that ServiceAccount's RBAC, decided in the deployment
rather than here. Reads are view-level with core `secrets` deliberately
excluded, and `--toolsets core` follows from that exclusion — helm stores
releases in Secrets, so its toolset would only ever answer 403.

Writes are narrower than reads, which is the whole shape of this entry: create,
update and patch on workload objects (pods, services, configmaps, PVCs and the
apps, batch, autoscaling, policy, networking and gateway kinds), and nothing at
all on RBAC, CRDs, StorageClasses, ServiceAccounts, nodes, ExternalSecrets or
Argo CD Applications. Each of those is an escalation path rather than a
workload change — an ExternalSecret in particular would walk around the Secret
exclusion above.

No `delete` verb and no `pods/exec` are granted anywhere. `--read-only` is gone
from the pod, so `resources_delete`, `pods_delete` and `pods_exec` are listed
and answer 403 when called. Changing any of this means editing the
`mcp-kubernetes` chart in argocd-env-demo, not this file.

Upstream: https://github.com/containers/kubernetes-mcp-server
