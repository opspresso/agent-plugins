---
description: "Work with Argo CD, the GitOps deployer for the Kubernetes cluster: applications and their resource tree, workload logs, events, clusters and projects — including create, sync and resource actions."
---

# argocd

Drives the Argo CD API: what exists (`list_applications`, `get_application`,
`get_appproject`, `list_clusters`), what a deployed app is actually doing
(resource tree, managed resources, workload logs, resource events), and what to
change about it (`create_application`, `update_application`,
`delete_application`, `sync_application`, `run_resource_action`).

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

**The token is the last mile.** The `mcp-argocd` chart in argocd-env-demo lands
the same `mcp-<slug>` Service on port 80 its six siblings use, but it cannot
carry the credential: Argo CD signs its own API tokens. argocd-env-addons'
`install/token.sh` mints one and pins it in parameter store alongside the token
list Argo CD checks it against, so the same token survives a cluster rebuild and
the installer needs no token step. Until that parameter holds a real token the
pod runs and `/healthz` stays green while every tool call answers 401 — a tool
error rather than a registration problem.

No credential on the entry: nothing routes to the Service from outside the
cluster, and the server authenticates to Argo CD with `ARGOCD_API_TOKEN` from
the pod's environment (External Secrets, parameter-store) rather than from the
caller. `ARGOCD_BASE_URL` points in-cluster at
`http://argocd-server.argocd.svc.cluster.local` — plain HTTP, because
argocd-env-addons runs the server with `server.insecure: true` and TLS
terminates at the gateway.

The write tools are listed because `MCP_READ_ONLY` is left unset, but what they
can actually do is Argo CD's own RBAC, not anything this entry decides. The
token belongs to the `mcp` account, and `role:mcp` in argocd-env-addons bounds
its writes to applications alone — create, update, delete, sync and resource
actions. Nothing else is writable, and `exec` is granted by neither that role
nor the default one.

Reads are wider than that role suggests, deliberately: the deployment keeps
`policy.default: role:readonly`, and Argo CD's built-in definition of that role
is `get` on applications, applicationsets, certificates, clusters,
repositories, projects, accounts, gpgkeys and logs. Every account inherits it,
this one included. So `role:mcp` narrows what a run may change, not what it may
see — narrowing the latter would take explicit deny rules, which Argo CD
evaluates ahead of allows.

Upstream: https://github.com/argoproj-labs/mcp-for-argocd
