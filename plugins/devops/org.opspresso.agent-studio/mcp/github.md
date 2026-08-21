---
description: "Work with GitHub: repositories and code search, issues, pull requests, Actions and security alerts — including opening a pull request and committing to a branch."
---

# github

GitHub's own hosted MCP server at `https://api.githubcopilot.com/mcp/`. The only
entry here that is neither cluster-internal nor free: it is a public endpoint
that answers for whatever account the caller authenticates as.

**Two ways in, and the entry carries both.** A project that has connected via
OAuth uses its own token; everything else falls back to the entry's
`Authorization` header. OAuth needs a hand-registered app — GitHub offers no
dynamic client registration, so the console's Discover step finds the endpoints
but not a way to create a client. Register the OAuth app on GitHub and enter its
credentials. After the first sync the entry has neither credential: run Discover
for the OAuth block, and add the `Authorization` header for the fallback.

## What a run may do is the token, not this entry

Nothing here narrows the server. It exposes reads and writes across repositories,
issues, pull requests, Actions and security alerts, and **which of those succeed
is decided by the scopes of whichever token answered** — the project's OAuth
grant or the fallback header's PAT. A read-only fine-grained token lists the
write tools and answers 403 when one is called, the same shape as the cluster
entries here.

That makes the token choice the security boundary:

- The fallback header is a **shared identity**. Every project without OAuth acts
  as that account, and the audit trail says that account rather than a person.
  Give it the narrowest scopes that let a run read code and open a pull request,
  and never a scope that can merge, force-push or administer.
- Per-project OAuth is the preferred path for the same reason — the commit and
  the PR carry the person who connected.
- Branch protection is what actually stops a bad merge. A token that can push is
  not a token that can bypass a required review, and this entry should never hold
  one that can.

## What the skills here expect of it

`gitops-change` uses it to land a chart-values change as a pull request rather
than touching the cluster, and `code-review` and `pr-description` in the
**engineering** plugin read PRs through it. Those two live in another plugin, so
a project that binds one without the other still works — each says in its own
body what it does when this server is absent.

Tool names are the server's, not this file's. A run reads the actual schema from
its own tool list; nothing here should be treated as a spelling reference.

Upstream: https://github.com/github/github-mcp-server
