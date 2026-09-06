---
description: >
  Search and read GitHub code, files, diffs, issues, pull requests, Actions and
  security alerts; create branches, commits, PRs and comments when requested.
  Review or description-only requests do not authorize writes, and available
  operations depend on the connected token's permissions.
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

## Skill bindings

DevOps `gitops-change` uses GitHub for repository changes and pull requests.
Engineering `code-review` and `pr-description` use it for PR analysis.
These skills are separately bound and define their fallback when GitHub is absent.
Actual tool names and arguments come from the connected server's schema.

Upstream: https://github.com/github/github-mcp-server
