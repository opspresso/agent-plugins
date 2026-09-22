---
description: >
  Read GitHub repositories, issues, PR diffs, reviews, releases and commit checks.
  CI job logs require the Actions toolset; security alerts require their toolset and account access.
  Use Workspace for Sandbox file changes and reviewed Git publication; use offered GitHub review or issue tools only for requested remote feedback.
  No tool discovery result grants write permission.
---

# github

## Endpoint and authentication

The hosted endpoint is `https://api.githubcopilot.com/mcp/`.
A project's OAuth connection takes precedence; otherwise the registry's
`Authorization` header supplies a fallback token.

The first sync supplies neither credential. Run Discover to configure OAuth
endpoints, register a GitHub OAuth app manually, and enter its client credentials.
GitHub does not support dynamic client registration. Configure a fallback
Bearer credential only if a shared identity is intended.

## Permission boundary

The server exposes reads and writes across repositories, issues, PRs, Actions
and security alerts. Token scopes determine which calls succeed. A read-only
token can still discover write tools and receive 403 when calling them.

Fallback credentials act as one shared account for projects without OAuth.
Per-project OAuth uses the connected account's identity. Restrict fallback
repository access and permissions to the required operations, and enforce
merge/review restrictions with branch protection. Do not supply bypass or
administrative privileges for ordinary agent work.

Verify representative repository access after connecting; tool discovery alone
does not verify access to a private repository or a requested write.

## Toolsets and workflow bindings

The default hosted toolset does not include Actions job logs. For an engineering
agent that needs CI investigation, configure the existing server connection with
the non-secret header `X-MCP-Toolsets: context,repos,issues,pull_requests,actions`.
Rediscover tools with that header, then bind only the required operations. Agent
Studio does not import headers from mcp.json; set this in the installation's
version binding. Do not put credentials or deployment-specific headers in this repository.

| Work | Relevant discovered capability | Boundary |
|---|---|---|
| PR review | pull_request_read, get_file_contents, get_commit | Read the exact head and bounded diff; review submission is a separate requested action |
| Issue fix and feature work | issue_read, repository/code reads | Supply context to Workspace; issue text is not execution permission |
| CI investigation | actions_list, actions_get, get_job_logs | Read run/attempt/head, failing step and bounded logs; omit actions_run_trigger for investigation-only use |
| Dependency/security findings | offered Dependabot/code-security reads or supplied advisory | Toolsets and access are optional; 403 or no tool does not mean no vulnerability |
| Publication of Workspace files | Workspace prepare_git | Do not substitute push_files, create_branch, create_pull_request or merge_pull_request for the Workspace approval flow |

These names are examples from the official server; use the actually discovered
schemas. For job logs, request a bounded tail and returned content when supported;
a download URL alone is not a log, and may be temporary. Do not send secrets from
logs into prompts or public comments. Actions reads use the existing repository
access; security alert APIs can require additional access such as security_events.
Do not broaden account scopes merely to make an optional capability appear.

`X-MCP-Readonly: true` is suitable for agents that never submit feedback. An agent
that also posts user-requested reviews/comments can keep a selected write subset;
avoid binding overlapping repository writers or automation delegation by default.
Project generation in a Workspace does not itself create a GitHub repository.
For requested repository creation, check the exact owner/name with Workspace
`check_repository_access`, then use **Workspace `create_repository`** with the
requested repository, description and visibility. The server initializes the
first commit and records creation for the project's repository policy. GitHub MCP
creation does not register the repository with Workspace. Never make a repository
public to fix access. Check the returned base branch and Workspace server access before clone.
A repository allowlist is not proof of existence, and 404 can mean inaccessible.
Repository creation, issue closure, workflow reruns, review submission and alert
dismissal each require the user's corresponding request and actual offered tools.

## GitHub webhook delivery to Agent Studio

The project's Settings → Webhook URL (`/api/webhook/{project}`) starts the published
project. In GitHub, choose `application/json` and enter that project's webhook
secret in the Secret field. GitHub sends `X-Hub-Signature-256`, not a custom
`X-Trigger-Secret` header. Use the existing secret; do not put it in the URL or logs.
A signed ping checks the connection without running an agent, and GitHub delivery
IDs deduplicate redeliveries. Check the trigger history after the HTTP 202 response.

`/api/workspaces/github/webhook` is a separate signed metadata callback. It updates
Workspace PR state and does not start Issue work. Its deployment-owned secret is
not the project trigger's secret. Neither webhook grants a user identity or
Workspace publication approval. Use the capabilities actually offered to the run.

## Skill bindings

DevOps `gitops-change` uses GitHub for repository changes and pull requests.
Engineering `code-review` and `pr-description` use it for PR analysis.
Engineering task skills use it for source context and verified outcomes, while
execution `workspace-task` and `sandbox-task` coordinate persistent file work.
These skills are separately bound and define their fallback when GitHub is absent.
Actual tool names and arguments come from the connected server's schema.

Upstream: [GitHub MCP tools](https://github.com/github/github-mcp-server#tools),
[remote toolsets and headers](https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md).
