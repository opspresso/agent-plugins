---
description: "Search Slack and act in it: messages, threads, files, canvases, reactions and users."
---

# slack

OAuth only — no fallback header. Each project connects with its own Slack user
token, so what a run can see is what the connecting user can see.

**OAuth needs a hand-registered app.** Like GitHub, Slack has no dynamic client
registration: Discover finds the endpoints (`slack.com/oauth/v2_user/authorize`
and `slack.com/api/oauth.v2.user.access`) but not a way to create a client —
register a Slack app and enter its client ID and secret. Only directory-published
or internal apps may use MCP, so an unlisted app is refused. Scopes are per-tool
(`search:read.public`, `chat:write`, `canvases:write`, …), and the workspace's
admins approve the app like any other.

Note the address and the identity are not the same string: the server is served
at `https://mcp.slack.com/mcp` but identifies itself as `https://mcp.slack.com`,
which is the `resource` every token is bound to. Discover reads that off the
server's own metadata — do not hand-edit it.

Sync creates the entry without the OAuth block; run Discover after the first sync.
