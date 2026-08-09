---
description: "Web, image, video and news search on Brave's independent index, plus AI summaries."
---

# brave-search

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

No credential on the entry: nothing routes to the Service from outside the
cluster, and upstream authenticates to the Brave Search API with `BRAVE_API_KEY`
from the pod's environment (External Secrets, parameter-store) rather than from
the caller. Brave has no hosted MCP endpoint — self-hosting is the only
official path, which is why this runs in-cluster.

What the entry exposes is a deployment question, not a repository one: the
deployment runs upstream's default tool set — all eight, verified against the
running pod: web, image, video, news, local and place search, summarizer, and
LLM context — and trimming it is `BRAVE_MCP_ENABLED_TOOLS`/`DISABLED_TOOLS` on
the pod. Plan matters more than the list: local search and summarizer are gated
by the API key's Brave plan, and on a Free key they still list but fail at call
time — that shows up as tool errors, not a registration problem.

Upstream: https://github.com/brave/brave-search-mcp-server
