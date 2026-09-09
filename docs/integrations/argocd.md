---
description: >
  Investigate Argo CD application health, sync status, revisions and GitOps drift. Changes, sync and resource actions require a requested change and effective Argo CD permission.
---

# argocd

Operator reference for a separately registered integration. This file is not
auto-synced as a bundled MCP declaration. Use the description as a starting
point and adjust it to the deployed tools and permission boundary.

Register the endpoint of the Argo CD MCP deployment reachable from the client.
Configure upstream URL, credentials and RBAC in that deployment. Do not assume a
cluster namespace, TLS termination mode, account role or write-tool setting.

Check inherited default roles as well as account-specific roles. Tool visibility
is not authorization. Verify an application read and the intended permission
boundary; a healthy MCP process does not verify its upstream token. Maintain
persistent desired state in the repository that owns it.

Upstream: https://github.com/argoproj-labs/mcp-for-argocd
