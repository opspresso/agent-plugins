---
description: >
  Read GitLab projects, files, commits, merge requests, work items and CI pipelines and jobs.
  Write tools create or update merge requests, notes, work items, branches, commits and pipelines only when the user requests that remote change.
  Use Forge for Sandbox file changes and reviewed Git publication. No tool discovery result grants write permission.
icon: brand-gitlab
---

# gitlab

## Endpoint and authentication

The GitLab MCP server is part of GitLab (generally available since GitLab 19.5, all tiers).
The manifest uses GitLab.com: `https://gitlab.com/api/v4/mcp`. For GitLab Self-Managed or
Dedicated, register the same server with your instance URL: `https://<gitlab host>/api/v4/mcp`.

Run Discover after the first sync. GitLab supports OAuth 2.0 Dynamic Client Registration, so
Studio registers its OAuth client automatically. Each user then connects their own GitLab
account; calls use that account's identity and permissions.

If an administrator disabled dynamic client registration, create an OAuth application in
GitLab with the `mcp` scope and the Confidential checkbox cleared, and enter its client ID.

Do not configure a shared fallback `Authorization` header unless a shared identity is intended.
GitLab accepts only an OAuth token with the `mcp` scope or a fine-grained personal access token
with the MCP tool resource and the Execute permission. It rejects legacy personal, project and
group access tokens with `403 insufficient_scope`, even when they have the `api` scope.

## Prerequisites

- GitLab.com: a top-level group owner allows access to the MCP server for the group.
- Self-Managed and Dedicated: an administrator allows access to the MCP server for the instance.

Tool discovery succeeds only after this setting is on. Discovery alone does not prove access to a
private project or a requested write; verify a representative project after connecting.

## Toolsets

Toolsets are `meta`, `core`, `merge_requests`, `work_items`, `repository`, `ci`, `wikis`,
`code_security`, `orbit` and `duo_agent_platform`. To limit an Agent's tools, set the non-secret
header `X-Gitlab-Enabled-Mcp-Server-Toolsets` (for example `core,repository,merge_requests,ci`)
in the Agent's MCP binding, rediscover, and bind only the required operations. The host app does
not import headers from `mcp.json`. `code_security` needs GitLab Ultimate; `duo_agent_platform`
appears only when GitLab Duo Agent Platform is available.

## Workflow bindings

| Work | Relevant discovered capability | Boundary |
|---|---|---|
| MR review | get_merge_request, get_repository_file, get_commit | Read the exact source SHA and a bounded diff; post a review with save_merge_request_review only when requested |
| Issue and work item context | get_work_item, list_work_items, search | Work item text is context, not execution permission |
| CI investigation | list_pipelines, get_pipeline, get_job | Read the pipeline, failing job and a bounded log; omit save_pipeline for investigation-only use |
| Remote feedback | save_note, save_work_item | Post only the requested comment or update |
| Merge | accept_merge_request | Only on an explicit request; respect protected branches and approval rules |
| Publication of Sandbox files | Forge `run_submit` Git actions | Forge supports GitHub only. Do not substitute add_commit, add_branch or save_merge_request for reviewed Sandbox publication |

These names come from the official server; use the actually discovered schemas. Do not send
secrets from job logs into prompts or public comments. Do not broaden account permissions merely
to make an optional toolset appear.
