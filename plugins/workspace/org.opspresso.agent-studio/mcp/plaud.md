---
description: >
  Find Plaud recordings by name or date through the connected account and read Plaud's
  existing transcripts and notes as provider output. In the host app, mapped get_file
  returns an opaque source_ref instead of the download URL; no current Studio or Librio
  tool accepts source_ref, so Plaud audio cannot be sent to Librio transcription from Chat.
  This server does not transcribe audio.
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
existing transcripts and notes. Obtain a fresh URL from the same recording ID
when it expires. Treat the URL as temporary access to private audio, not as a
permanent citation or an artifact ID.

## Transcription and meeting minutes

Use `meeting-minutes` for recording selection, transcript provenance,
decisions, action items and review. Its `agent-setup.md` supplies a project prompt
and the transcription boundary.

Agent Librio transcribes recordings and writes meeting notes. Studio reaches it
only through the Librio MCP tools: `recording_import` takes a Studio file ID,
which Studio converts to a short-lived verified file reference, and
`audio_job_submit` starts processing. See the `audio-processing` skill.

The workspace plugin declares the default `get_file` projection in plugin.json under
`extensions.org.opspresso.agent-studio.mcpSourceOutputs.plaud`. The host app applies it
when the Agent binding has no explicit override: `presigned_url` is kept server-side and
an opaque `source_ref` is returned to the model. The declared `refreshArgument: file_id`
refreshes the URL from the same recording. Agent binding overrides take priority; an
explicit empty array disables mapping. The mapping keeps the URL out of model context.
It does not create a Studio file ID, and no current tool accepts `source_ref` as input.

To transcribe a Plaud recording with Librio, the user attaches the audio file to the
Chat (within the document attachment limit of 10 MiB) or uploads it in the Librio
console. Do not promise scheduled Plaud-to-Librio collection. `FetchUrl` and document
`File` remain unsuitable for audio transcription.

The hosted Plaud MCP processes requests in the US, and recordings must already
be cloud-synced. Librio transcription keeps the transcription stage internal; it does not
make acquisition from Plaud an offline workflow. Do not substitute Plaud's
transcript or its Embedded Transcription API for a requested Librio transcription.

Sources:
- [Official MCP tools and data contract](https://docs.plaud.ai/plaud-mcp-cli/mcp)
- [Remote endpoint, OAuth and Cloud Sync requirements](https://support.plaud.ai/hc/en-us/articles/57751078986265-Plaud-MCP)
- [Protected-resource metadata](https://mcp.plaud.ai/.well-known/oauth-protected-resource/mcp)
- [Authorization-server metadata](https://mcp.plaud.ai/.well-known/oauth-authorization-server)
