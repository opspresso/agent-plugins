---
description: >
  Search the web, news, images and videos for current information and source URLs with Brave. Snippets support discovery; detailed claims require source-page verification when page access is available. Operations depend on enabled tools and API plan.
---

# brave-search

Operator reference for a separately registered integration. This file is not
auto-synced as a bundled MCP declaration. Use the description as a starting
point and adjust it to the deployed tools and permission boundary.

Deploy a Brave MCP server and register its reachable endpoint. Supply the API
credential through the deployment's secret configuration. Do not put it in this
repository, the endpoint URL or a model-visible tool argument.

Select enabled tools and keep the registered description aligned with them.
Plan-gated operations can be discoverable but fail when called. Verify a
representative search after changing the key, plan or deployment. Treat plan
rejection as an access limitation, not an empty search result.

Upstream: https://github.com/brave/brave-search-mcp-server
