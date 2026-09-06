---
description: >
  Investigate Argo CD application health, sync status, revisions, deployment
  resources, logs and GitOps drift. Application changes, sync and resource
  actions require a requested change; durable desired state belongs in Git.
---

# argocd

## Connection and credentials

The bundled service is internal to `agent-mcps`, with no ingress.
`MCP_INTERNAL_HOST_SUFFIXES` must allow its suffix or sync reports `invalid-url`.
No caller credential is configured on the registry entry.

The pod uses `ARGOCD_API_TOKEN` supplied through External Secrets and parameter
store. In argocd-env-addons, `install/token.sh` creates the token and persists
it with Argo CD's token-list state. A healthy pod and `/healthz` do not verify
this credential: an invalid token produces 401 on tool calls.

`ARGOCD_BASE_URL` is `http://argocd-server.argocd.svc.cluster.local`.
The deployment uses `server.insecure: true` because TLS terminates at the gateway.

## Permissions and verification

`MCP_READ_ONLY` is unset, so write tools are discoverable. Effective permission
comes from Argo CD RBAC. The `mcp` account's `role:mcp` allows application
create, update, delete, sync and resource actions; it does not grant exec.

The inherited `policy.default: role:readonly` also allows reads of applications,
applicationsets, certificates, clusters, repositories, projects, accounts,
gpgkeys and logs. The account role does not remove those default reads.
Restricting inherited reads requires explicit denies.

After credential or RBAC changes, verify an application read and the intended
permission boundary. Registration alone does not validate upstream access.
Durable desired-state changes are maintained in the GitOps repository.

Upstream: https://github.com/argoproj-labs/mcp-for-argocd
