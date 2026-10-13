# Agent Librio connection

Agent Librio owns source documents, document processing, RAG passages,
source-grounded knowledge, recordings, transcripts and meeting summaries. It is
separate from Agent Memory's durable preferences and short-term task handoffs.

Register the installation's exact MCP URL (normally `/api/mcp`) independently of
Plugin sync. Studio signs delegation for that configured URL with
`aud=agent-librio`; the service validates the issuer/subject binding and current
membership. Email headers and matching service names do not delegate identity.
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

Both Memory and Librio expose `context_search`; select the discovered server by
its purpose and trusted connection, not the bare tool name. A source document ID,
recording ID or graph node ID is not a Studio Artifact ID.

## Audio through Studio

Studio keeps the public `ImportFile`, `TranscribeAudio` and `AudioJob` wrappers.
They orchestrate source access and delegate original storage and transcription to
Librio. Librio can run its configured summary model independently; an explicitly
selected Studio Agent handles custom postprocessing in Studio.

Read the actual wrapper schema. Do not expose internal Librio request keys,
recording IDs or service credentials as new AudioJob arguments. Console lifecycle
APIs do not imply model tools named cancel, retry or delete. Verify current output
availability before linking a completed recording or transcript. Retention and
processing completion are different facts.

## Direct clients and Studio have different execution paths

Independent clients using their own Librio credential or an explicitly configured
local issuer can discover `recording_reserve`, `recording_archive`,
`audio_job_submit`, `audio_job_cancel`, `audio_job_retry` and `audio_job_delete`
when authorized. Read tools are `audio_models`, `audio_status`, `audio_list`,
`audio_request_status` and `audio_output_read`. These are Librio MCP names, not
operations to add to Studio's AudioJob request object.

Studio's general Librio MCP delegation includes `audio:read` but excludes
`audio:write`. AudioJob's server-side HTTP flow creates durable dispatch context
and verifies current policy before execution. Required-policy Studio issuers cannot
submit directly without that stored context. Do not swap credentials or use
another MCP route to bypass this boundary.
