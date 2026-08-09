---
description: "Fetch a URL as usable content: images as bytes, documents (HTML, PDF, CSV, JSON) as text."
---

# url-fetch

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

No credential: nothing routes to the Service from outside the cluster.

Source: https://github.com/opspresso/mcp-url-fetch
