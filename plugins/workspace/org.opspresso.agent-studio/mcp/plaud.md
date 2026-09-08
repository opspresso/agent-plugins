---
description: >
  Find Plaud recordings by name or date and retrieve recording details and temporary
  audio download URLs through the connected account. Plaud transcripts and summaries
  are existing provider output, not internal transcription results. Downloading and
  transcribing the audio requires a separate capable tool; this server does not record audio.
---

# plaud

## Connection

Use the official remote endpoint `https://mcp.plaud.ai/mcp` with OAuth.
After plugin sync, run Discover and connect the meeting agent's project to the
intended Plaud account. Plaud Cloud Sync must be enabled for its recordings to
be available. Do not store credentials in this repository or share a fallback
account across projects.

Public metadata advertises authorization-code flow, PKCE S256, refresh tokens
and dynamic client registration at `https://mcp.plaud.ai/register`. Agent Studio
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

## Internal transcription and meeting minutes

Use `meeting-minutes` for recording selection, internal-transcript provenance,
decisions, action items and review. Its `agent-setup.md` supplies a project prompt
and the required transcription integration boundary.

The repository registers Plaud; it does not implement an audio downloader or ASR.
Agent Studio currently catalogs Transcription models but has no transcription
execution builtin. Its `FetchUrl` reads text/images, and `File` processes documents;
neither turns an audio URL into a transcript. Internal transcription therefore
needs a configured internal tool before the full agent can run.

The hosted Plaud MCP processes requests in the US, and recordings must already
be cloud-synced. Internal ASR keeps the transcription stage internal; it does not
make acquisition from Plaud an offline workflow. Do not substitute Plaud's
transcript or its Embedded Transcription API for a requested internal model.

Sources:
- [Official MCP tools and data contract](https://docs.plaud.ai/plaud-mcp-cli/mcp)
- [Remote endpoint, OAuth and Cloud Sync requirements](https://support.plaud.ai/hc/en-us/articles/57751078986265-Plaud-MCP)
- [Protected-resource metadata](https://mcp.plaud.ai/.well-known/oauth-protected-resource/mcp)
- [Authorization-server metadata](https://mcp.plaud.ai/.well-known/oauth-authorization-server)
