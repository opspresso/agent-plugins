---
description: >
  Read a YouTube link or video id as timestamped captions or metadata. Use
  get_transcript for spoken content; metadata is not evidence of what was said.
  State transcript truncation when reported, and summarize only the returned part.
  No continuation or time-range input is supported. Caption languages marked
  "could not be listed" mean discovery failed, not that captions are absent.
---

# youtube

Turns a YouTube link into something a model can read — `get_transcript` for
the captions as `[m:ss] line` rows (human track preferred, auto-generated
fallback, language selectable), `get_video_info` for metadata and which
transcript languages exist. The `url` argument accepts watch, youtu.be, shorts,
embed and live links, or a bare 11-character video id. It extracts the id and
does not fetch arbitrary caller-supplied URLs.

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

With `MCP_API_KEY` unset, callers are trusted through the deployment's network
boundary. If that key is set, supply its matching Bearer credential in the
registry settings, not in this repository.

## Metadata and transcript availability

The optional server environment variable `YOUTUBE_API_KEY` moves
`get_video_info` to the official YouTube Data API. It is separate from
`MCP_API_KEY` and does not unlock transcripts: `get_transcript` still uses
YouTube's player and caption endpoints, which can reject datacenter traffic
or require tokens. Missing tracks, unavailable videos and provider refusals
return tool errors; metadata success does not imply transcript access.

When the requested caption language is unavailable, the error lists available
languages. A failed Data API caption-language lookup can leave valid video
metadata with languages marked `could not be listed`; that is not evidence
that no captions exist.

## Returned content

Transcript text is capped at 90,000 characters on complete line boundaries.
Its truncation note identifies the retained lines and ending timestamp; the
tools offer no continuation or time-range argument. Descriptions are capped
at 2,000 characters with a truncation note. Auto-generated tracks are labeled.
Results mark third-party text as untrusted data, never instructions.

Source: https://github.com/opspresso/mcp-youtube
