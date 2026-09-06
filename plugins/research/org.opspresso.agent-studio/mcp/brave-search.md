---
description: >
  Search the web, news, images and videos for current information and source
  URLs with Brave. Snippets and AI summaries support discovery; detailed claims
  need source-page verification with FetchUrl when available.
  Local search and summarization depend on the configured API plan.
---

# brave-search

## Connection and credentials

The internal `agent-mcps.svc.cluster.local` suffix must be allowed by
`MCP_INTERNAL_HOST_SUFFIXES`; otherwise sync reports `invalid-url`.
The bundled service has no ingress or registry credential. It authenticates
to Brave with `BRAVE_API_KEY` from the pod environment through External Secrets
and parameter store.

## Tool availability

The deployment enables upstream's eight default tools: web, image, video,
news, local and place search, summarizer, and LLM context.
`BRAVE_MCP_ENABLED_TOOLS` and `BRAVE_MCP_DISABLED_TOOLS` control the pod's tool
selection. Keep the registry description consistent with deployed capabilities.

Local search and summarizer access depend on the Brave plan. A tool can appear
in discovery and fail when called with a Free key. Verify representative calls
after changing the key or plan; plan rejection is a tool-access issue rather
than a registration failure.

Upstream: https://github.com/brave/brave-search-mcp-server
