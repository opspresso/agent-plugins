# Agent Librio connection

Agent Librio owns source documents, document processing, RAG passages,
source-grounded knowledge, recordings, transcripts and meeting summaries. It is
separate from Agent Memory's durable preferences and short-term task handoffs.

Studio's deployment settings (`LIBRIO_URL`, `LIBRIO_OIDC_CLIENT_ID`) create one
Tools entry for the service's `/api/mcp` endpoint. Plugin sync does not own it.
Studio issues a delegated user token for that exact URL on every MCP request;
the service validates the issuer/subject binding and current membership. Email headers and matching service names do not delegate identity.
Keep credentials, provider endpoints and connection IDs in installation settings.

## Discovered knowledge tools

| Tool | Purpose |
|---|---|
| `context_search` | Search accessible document passages and source-grounded knowledge |
| `document_search` | Search processed document chunks |
| `knowledge_search`, `knowledge_neighborhood` | Find knowledge nodes and bounded graph context |
| `document_ingest` | Accept a scoped document with a stable idempotency key |
| `document_ingest_status` | Check processing and distinguish accepted work from `ready` |
| `document_ingest_retry` | Retry a failed document using its observed `expectedAttempts` and a stable key |
| `knowledge_object_types`, `knowledge_objects`, `knowledge_object` | Read ontology object types, list objects of a type, and read one object (`knowledge:read`) |
| `knowledge_object_update` | Change editable properties of one object; send the state version that was read (`knowledge:write`) |

Long-term memories come from Memory's `recall`, not Librio. Select the discovered
server by its purpose and trusted connection, not the bare tool name. A source document ID,
recording ID or graph node ID is not a Studio file ID.

## Audio tools

Studio connects to Librio only through this MCP server. Each MCP connection is
offered to the Agent as one native specialist, and every call carries a
short-lived token delegated from the current Studio user. Librio owns audio
settings (named profiles), recordings, processing jobs, outputs and history.
Studio keeps no copy of them.

| Step | Tool |
|---|---|
| Read settings | `audio_profile_get` (omit `id` for the user's default), `audio_profile_list`, `audio_models` |
| Import a Chat file | `recording_import` with the Studio file ID in `source` |
| Submit processing | `audio_job_submit` with `profileId`/`profileRevision` or explicit model IDs, not both |
| Observe | `audio_status`, `audio_list` |
| Recover a lost response | `audio_request_status` with the original key |
| Read text outputs | `audio_output_read` (bounded pages, unchanged cursor) |
| Explicit lifecycle requests | `audio_job_cancel`, `audio_job_retry`, `audio_job_delete`, `recording_archive`, `recording_delete`, `recording_delete_status` |

`recording_import.source` declares the `org.opspresso.agent.file-reference`
annotation. The model passes a Studio file ID; Studio replaces it at dispatch
with a short-lived verified reference (`url`, `checksum`, `sizeBytes`,
`expiresAt`). Recording attachments are limited to 512 MiB; larger recordings are
uploaded in the Librio console. Plaud's mapped `source_ref` is not a Studio file
ID, and no current tool accepts it.

Submission and retry responses carry a work reference in
`structuredContent.work` and `_meta["org.opspresso.agent.work"]`. Studio records
keyed submissions, delivers the terminal result to the original Chat once and
saves available transcript and meeting-note outputs as Chat files. Never resubmit
uncertain work under a new key or `processingRevision`; inspect the original
request with `audio_request_status`.

When the deployment sets `AUTH_BASE_URL`, MCP initialize advertises
`org.opspresso.agent.tool-management` with `settingsUrl` and `historyUrl`.
Studio's Tools detail page shows those links. Job responses also include a
console-relative `historyHref`.

Librio publishes each transcript and meeting note as the caller's search document.
Do not ingest them again as documents. Save a decision or fact to Memory only on
explicit request, through the `personal-records` skill and the Memory MCP.
See [Librio audio contract](https://github.com/opspresso/agent-librio/blob/main/docs/AUDIO.md).
