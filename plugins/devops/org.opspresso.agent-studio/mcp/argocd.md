---
description: >
  Investigate Argo CD application health, sync status, revisions and GitOps drift. Changes, sync and resource actions require a requested change and effective Argo CD permission.
---

# argocd

Bundled endpoint: `http://mcp-argocd.agent-mcps.svc.cluster.local/mcp`.
The `argocd-env-demo` k3s deployment exposes this service inside the cluster.
See [in-cluster MCP setup](../../../../docs/agent-studio.md#in-cluster-mcp-services)
for network access, plugin sync and agent bindings.

Configure upstream URL, credentials and RBAC in the deployment. The MCP endpoint
uses internal HTTP; the upstream Argo CD API token remains deployment-managed.
Keep the description aligned with the deployed tools and permission boundary.

Check inherited default roles as well as account-specific roles. Tool visibility
is not authorization. Verify an application read and the intended permission
boundary; a healthy MCP process does not verify its upstream token. Maintain
persistent desired state in the repository that owns it.

Upstream: https://github.com/argoproj-labs/mcp-for-argocd
