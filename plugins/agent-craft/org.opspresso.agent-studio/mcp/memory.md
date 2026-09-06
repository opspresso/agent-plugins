---
description: >
  Remember and recall this project's durable knowledge — decisions, conventions
  and setup from earlier sessions. Call recall before asking the user to
  re-explain anything, and remember a decision or convention as soon as it lands.
---

# memory

The bundled address uses the internal `agent-mcps.svc.cluster.local` suffix;
`MCP_INTERNAL_HOST_SUFFIXES` must allow it for registration. The address can
resolve to a Kubernetes Service or an IDC container network alias.

With `MCP_API_KEY` unset, the server trusts every caller that can reach it, so
the deployment must restrict network access. If an operator sets that key,
configure the matching `Authorization: Bearer …` header in the registry's
credential settings. Keep the value out of this repository.

## Memories are scoped per project, with no header to set

Agent Studio stamps `X-Tenant-Id: <project name>` on every MCP request a run
makes, and this server reads it as the tenant when no explicit `X-Memory-Tenant`
is present. **Binding supplies the tenant**: each project gets its own memory,
and requests with different tenants cannot read each other's memories. No
tenant header needs to be configured on the entry or binding; authentication
headers, when required by the deployment, are separate.

The tenant is deliberately a header and not a tool argument: a tool argument is
chosen by the model, and a model that can name its own tenant can read another
project's memories by asking — including one talked into it by text it just
retrieved. The platform supplies `X-Tenant-Id` outside the model's control.

Set `X-Memory-Tenant` only to name the tenant yourself — for instance so
several projects share one memory. It wins over the stamped project name. A
request carrying neither header may still discover the server and list its
tools, so **Test connection** and the catalog probe work without a project. The
tenant is resolved when a tool runs; an unscoped call is refused, while a bound
run carries the stamped project header.

When the run is in a conversation (a chat, a Slack thread, an A2A context, an
API caller that declared one) the platform also sends `X-Conversation-Id`, and
`remember(scope: "conversation")` files a memory that only that conversation
recalls or lists. Omitting `scope` stores a project memory even when a
conversation header is present. Requesting conversation scope without that
header is refused; it does not fall back to project scope. `type` is only a
classification: `type: "conversation"` does not change visibility.

Conversation scope limits recall, listing and statistics. `forget` checks the
tenant and memory id, not the conversation; it permanently deletes the target.

## Recalling before the first token

Bound alone, `recall` is a tool the model may or may not think to call. A
version that turns on **Recall memory before each run** has the run call it
first, with the newest user turn, and adds the answer to the system prompt.
That option asks only the servers the version has bound — bind this one, or
the run warns on every turn that nothing could answer.

## Storage

PostgreSQL with pgvector stores each memory, its embedding and its access count
in one row. `DATABASE_URL` is required and the server creates its schema at
startup. Bedrock Titan v2 is the default embedding provider. Deployments using
an OpenAI-compatible endpoint set `EMBEDDING_PROVIDER=openai` together with
`EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` and `EMBEDDING_DIM`.
These are server environment settings, not MCP request headers.

The server does not provide document search. Use Agent Memory when a project
needs indexed documents or RAG.

## Connecting Agent Memory separately

Agent Memory uses a separate registry entry pointing to
`<base URL>/api/organizations/<organizationSlug>/mcp`, with a Bearer credential
configured by the operator. Its organization Agent token works only on that
organization's MCP endpoint and only for organization scope. User or team scope
and the ordinary HTTP API require a user's session Bearer token.

Its tools are `context_search`, `recall`, `memory_search`, `memory_create`,
`document_search`, `knowledge_search` and `knowledge_neighborhood`. It does not
expose this server's `remember` or `forget`, or a document-upload MCP tool.
Choose the tools actually bound to the agent rather than reusing the same
memory instructions unchanged. Connection and API details:
https://github.com/opspresso/agent-memory/blob/main/docs/api.md

## Operating notes

- Access counters are updated atomically in PostgreSQL.
- Nothing expires on its own. `forget` is the only removal.
- `remember` may return `Already known` for near-identical content. That means
  nothing new was stored; supplied tags, category and scope did not update the
  existing memory.
- One database cannot mix embedding dimensions. Changing the embedding model
  requires clearing or re-embedding existing memories and recalibrating
  `RECALL_MIN_SIMILARITY`, which is tuned to Titan's similarity scale.

Source and full design notes: https://github.com/opspresso/mcp-memory
