---
description: >
  Search AWS service documentation, API references, What's New and
  Well-Architected guidance for configuration and architecture questions.
  Provides public documentation, not live AWS account or resource state.
---

# aws-knowledge

AWS hosts this public service without authentication or an AWS account.
The configured URL is the bare host; initialization uses the root rather
than an `/mcp` path. No credential or OAuth discovery step is required after sync.

This is a documentation service. Account inventory, resource status and
telemetry require other integrations. AWS rate limits can produce tool errors
during heavy use even when registration and initialization succeed.
