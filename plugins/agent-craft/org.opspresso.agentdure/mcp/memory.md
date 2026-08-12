---
description: >
  Remember and recall this project's durable knowledge — decisions, conventions
  and setup from earlier sessions. Call recall before asking the user to
  re-explain anything, and remember a decision or convention as soon as it lands.
---

# memory

Cluster-internal (`agent-mcps` namespace, no ingress), so it is reachable only
because `MCP_INTERNAL_HOST_SUFFIXES` declares that suffix. No credential:
nothing routes to the Service from outside.

## Memories are scoped by the `X-Memory-Tenant` header

**Set this per version.** The registry-level value is `default` — a shared bucket
every binding falls into if it does not override. Two projects with the same
tenant share one memory; two with different tenants cannot see each other's at
all.

The tenant is deliberately a header and not a tool argument: a tool argument is
chosen by the model, and a model that can name its own tenant can read another
project's memories by asking — including one talked into it by text it just
retrieved.

Sync creates the entry with no headers, so set `X-Memory-Tenant` in the console
before binding it to anything.

## Storage

S3 only. S3 Vectors (`agent-studio-vector/memories`) holds the memories; ordinary
S3 (`agent-studio-memory`) holds access counters. Embeddings come from Bedrock
Titan v2 via the pod's own role — no key to rotate.

## Operating notes

- Access counters are approximate: a pod that dies before its next flush loses up
  to 30s of them. They only affect ranking.
- Nothing expires on its own. `forget` is the only removal.
- The vector index's dimension, distance metric and non-filterable metadata keys
  are fixed at creation. Changing the embedding model means a new index and
  re-embedding everything — and recalibrating `RECALL_MIN_SIMILARITY`, which is
  tuned to Titan's similarity scale.

Source and full design notes: https://github.com/opspresso/mcp-memory
