---
description: >
  Search earlier decisions, conventions and setup, or save reusable facts and
  conversation notes; this memory service does not search indexed documents.
  Storage is project-wide by default; use scope="conversation" for notes recalled
  only in this conversation and never fall back to project scope when it fails.
  forget permanently deletes a known id only within the authorized scope.
---

# memory

## Connection and authentication

The internal `agent-mcps.svc.cluster.local` suffix must be allowed by
`MCP_INTERNAL_HOST_SUFFIXES`. It can resolve through a Kubernetes Service or
an IDC network alias. With `MCP_API_KEY` unset, every reachable caller is trusted;
restrict network access. When set, register the matching Bearer credential
outside this repository.

## Tenant and conversation scope

Agent Studio sends `X-Tenant-Id: <project name>` on bound MCP calls.
`X-Memory-Tenant`, if configured, overrides that value and can intentionally
share a tenant across projects. Tenant headers are independent of authentication.
Discovery and connection tests work without a tenant; tool calls require one.

Conversation runs also carry `X-Conversation-Id`. `remember(scope="conversation")`
requires this header and does not fall back to project storage. Omitting scope
stores project memory even when the header exists. The `type` field is only a
classification and does not control visibility.

Conversation scope restricts recall, listing and statistics. `forget` checks
tenant and memory id, not conversation scope, and permanently deletes the target.

A version's **Recall memory before each run** setting invokes bound recall
servers before generation. Enabling it without a suitable bound server produces
a warning on each run.

## Storage and troubleshooting

`DATABASE_URL` is required; the server creates its PostgreSQL/pgvector schema
at startup. Bedrock Titan v2 is the default embedding provider. An OpenAI-compatible
deployment uses `EMBEDDING_PROVIDER=openai`, `EMBEDDING_BASE_URL`,
`EMBEDDING_API_KEY`, `EMBEDDING_MODEL` and `EMBEDDING_DIM` as server settings.

Memories do not expire automatically. Access counters update atomically.
`Already known` means a near-duplicate was not inserted; supplied tags, category
and scope do not update the existing record. A database cannot mix embedding
dimensions. Model migration requires clearing or re-embedding existing records
and recalibrating `RECALL_MIN_SIMILARITY`, whose default is tuned to Titan.

## Separate Agent Memory service

Indexed document search and RAG use Agent Memory at
`<base URL>/api/organizations/<organizationSlug>/mcp`, with a separate registry
entry and Bearer credential. An organization Agent token is limited to that
organization's MCP endpoint and organization scope. User/team scope and the
ordinary HTTP API require a user's session Bearer token.

Agent Memory exposes `context_search`, `recall`, `memory_search`,
`memory_create`, `document_search`, `knowledge_search` and
`knowledge_neighborhood`. It has no `remember`, `forget` or document-upload
MCP tool, so bindings must match the intended service.

Sources: https://github.com/opspresso/mcp-memory
and https://github.com/opspresso/agent-memory/blob/main/docs/api.md
