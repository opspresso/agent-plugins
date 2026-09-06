---
description: >
  Read YouTube videos as timestamped captions for summaries and quotations, or
  retrieve video metadata and caption languages. Metadata does not establish
  spoken content; transcripts may be truncated and have no continuation input.
  A language lookup failure does not mean captions are absent.
---

# youtube

## Connection and authentication

The internal `agent-mcps.svc.cluster.local` suffix must be allowed by
`MCP_INTERNAL_HOST_SUFFIXES`; the bundled deployment has no ingress.
With `MCP_API_KEY` unset, the network boundary controls access. When it is set,
register the matching Bearer credential outside this repository.

## Capabilities and provider access

`get_transcript` returns timestamped captions, preferring human tracks and
falling back to labeled automatic tracks. Language selection is supported.
`get_video_info` returns metadata and available caption languages. Both accept
watch, youtu.be, shorts, embed and live links or an 11-character video id.
The server extracts the id and does not fetch arbitrary caller-supplied URLs.

The optional server setting `YOUTUBE_API_KEY` uses the official Data API for
metadata. It is separate from `MCP_API_KEY` and does not unlock captions.
Transcript requests still use YouTube's player and caption endpoints, which
may reject datacenter traffic or require tokens. Verify a transcript call
separately from metadata success.

## Limits and troubleshooting

Transcript text is capped at 90,000 characters on complete line boundaries.
The truncation note reports retained lines and the ending timestamp; no
continuation or time-range parameter exists. Descriptions are capped at
2,000 characters. Returned third-party text is marked as untrusted data.

Missing videos, tracks and provider refusals return tool errors. An unavailable
requested language produces a list of alternatives. A Data API language lookup
failure can leave valid metadata with languages marked `could not be listed`;
this is distinct from an empty caption list.

Source: https://github.com/opspresso/mcp-youtube
