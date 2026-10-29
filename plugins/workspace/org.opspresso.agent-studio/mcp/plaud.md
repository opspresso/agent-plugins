---
description: >
  Find Plaud recordings by name or date through the connected account and read Plaud's
  existing transcripts and notes as provider output. In Studio, mapped get_file downloads
  the original into a user-owned file and returns file_id, filename and mime_type.
  Pass file_id to Agent Knowledge recording_import, then submit transcription and meeting notes
  with audio_job_submit when the recording is ready. This server does not transcribe audio.
icon: brand-plaud
---

# plaud

## Connection

Use the official remote endpoint `https://mcp.plaud.ai/mcp` with OAuth.
After plugin sync, run Discover and connect the meeting Agent to the
intended Plaud account. Plaud Cloud Sync must be enabled for its recordings to
be available. Do not store credentials in this repository or share a fallback
account across Agents.

Public metadata advertises authorization-code flow, PKCE S256, refresh tokens
and dynamic client registration at `https://mcp.plaud.ai/register`. The host app
can discover these settings; do not copy tokens from the local Plaud CLI.
An unauthenticated MCP initialize returns 401 with a protected-resource metadata
challenge. A browser GET to `/mcp` can return 404 and is not a connection test.
Verify discovery and a recording read after completing OAuth; metadata checks
alone do not prove access to the user's account.

## Recording contract

The documented tools include `list_files`, `get_file`, `get_transcript` and
`get_note`. Use discovered schemas for exact arguments. `list_files` filters
recording names with `query` and dates with `date_from`/`date_to`; its pagination
is ignored when filters are set. Recording duration is in milliseconds.
`get_file` supplies a `presigned_url` valid for 24 hours and may also include
existing transcripts and notes. Studio consumes the URL server-side when importing
the mapped file. Treat the URL as temporary access to private audio, not as a
permanent citation or an artifact ID.

## Transcription and meeting minutes

Use `meeting-minutes` for recording selection, transcript provenance,
decisions, action items and review. Its `agent-setup.md` supplies a project prompt
and the transcription boundary.

Agent Knowledge transcribes recordings and writes meeting notes. Studio reaches it
only through the Agent Knowledge MCP tools: `recording_import` takes a Studio file ID,
which Studio converts to a short-lived verified file reference, and
`audio_job_submit` starts processing. See the `audio-processing` skill.

The workspace plugin declares `get_file` in plugin.json under
`extensions.org.opspresso.agent-studio.mcpFileOutputs.plaud`. Each mapping contains
`tool`, `urlPath`, `idPath`, optional `namePath`, and `mimeType`. Studio applies it
to the raw MCP result, downloads the original through its URL and byte-limit checks,
and stores a user-owned Studio file. The model receives only
`file_id`, `filename`, `mime_type`, `size_bytes`, `source` and `external_id`.
The download URL and original bytes stay outside model context. This mapping has
no source-reference lifecycle or automatic URL refresh.

Deploy Studio with `mcpFileOutputs` support before syncing workspace plugin 1.3.0
or later. Plugin sync updates the declaration and skills; it does not upgrade Studio.
Verify a real `get_file` call returns `file_id` after sync. A missing file ID or a
download error is a failed import; do not invent an ID or pass the raw URL through
another tool.

For a requested Agent Knowledge transcription, use `list_files` to identify the
recording, call `get_file`, and pass the returned `file_id` to
`recording_import.source`. Reuse the returned filename and MIME type. Submit the
processing job only after the recording is ready. Users do not need to download
and attach the same audio manually. Reuse an existing returned file ID instead of
downloading the same original again in the run. The transfer and Agent Knowledge
original limits are both 512 MiB. `FetchUrl` and document `File` do not transcribe audio.

The hosted Plaud MCP processes requests in the US, and recordings must already
be cloud-synced. Agent Knowledge transcription keeps the transcription stage internal; it does not
make acquisition from Plaud an offline workflow. Do not substitute Plaud's
transcript or its Embedded Transcription API for a requested Agent Knowledge transcription.

Sources:
- [Official MCP tools and data contract](https://docs.plaud.ai/plaud-mcp-cli/mcp)
- [Remote endpoint, OAuth and Cloud Sync requirements](https://support.plaud.ai/hc/en-us/articles/57751078986265-Plaud-MCP)
- [Protected-resource metadata](https://mcp.plaud.ai/.well-known/oauth-protected-resource/mcp)
- [Authorization-server metadata](https://mcp.plaud.ai/.well-known/oauth-authorization-server)
