---
description: >
  Remember and recall this project's durable knowledge — decisions, conventions
  and setup from earlier sessions — and search the shared documentation library.
  Call recall before asking the user to re-explain anything, and remember a
  decision or convention as soon as it lands.
---

# memory

Cluster-internal (`agent-mcps` namespace, no ingress), so it is reachable only
because `MCP_INTERNAL_HOST_SUFFIXES` declares that suffix. No credential:
nothing routes to the Service from outside.

## Memories are scoped per project, with no header to set

Agent Studio stamps `X-Tenant-Id: <project name>` on every MCP request a run
makes, and this server reads it as the tenant when no explicit `X-Memory-Tenant`
is present. **Binding the server is enough**: each project gets its own memory,
and two projects cannot see each other's at all. Nothing needs to be configured
on the entry or on the binding — sync creates it with no headers, and that is
the intended state.

The tenant is deliberately a header and not a tool argument: a tool argument is
chosen by the model, and a model that can name its own tenant can read another
project's memories by asking — including one talked into it by text it just
retrieved. The platform applies its header last, so neither the entry nor a
version's overrides can impersonate another project.

Set `X-Memory-Tenant` only to name the bucket yourself — for instance so
several projects share one memory. It wins over the stamped project name. A
request carrying neither header is refused (including `tools/list`), which is
why **Test connection** and the catalog probe, which carry no project, report
the refusal rather than an empty tool list; a bound run is unaffected.

When the run is in a conversation (a chat, a Slack thread, an A2A context, an
API caller that declared one) the platform also sends `X-Conversation-Id`, and
`remember(scope: "conversation")` files a memory that only that conversation
recalls. Without it, memories are the project's, as before.

## Recalling before the first token

Bound alone, `recall` is a tool the model may or may not think to call. A
version that turns on **Recall memory before each run** has the run call it
first, with the newest user turn, and adds the answer to the system prompt.
That option asks only the servers the version has bound — bind this one, or
the run warns on every turn that nothing could answer.

## The documentation library

`search_docs` answers from a Bedrock Knowledge Base rather than from memories,
and the two are not the same store. Memories are what a run decided; the library
is what someone wrote down — documentation, runbooks, conventions — uploaded to
`s3://agent-studio-kb` and indexed by the knowledge base's own ingestion.

**It is shared across projects.** A tenant header is still required, but it does
not filter documents: two projects searching the same phrase get the same
excerpts. Memories remain strictly per-tenant.

Nothing ingests on a schedule. A document added to the bucket is invisible to
`search_docs` until an ingestion job runs, and the tool is offered at all only
where `KNOWLEDGE_BASE_ID` is set — alpha today, since prod has no knowledge base
of its own yet.

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
