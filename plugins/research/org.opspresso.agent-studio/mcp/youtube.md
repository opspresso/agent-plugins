---
description: "Read a YouTube video from a link or bare video id: the transcript as timestamped text, or its title, duration, description and available caption languages."
---

# youtube

Turns a YouTube link into something a model can read — `get_transcript` for
the captions as `[m:ss] line` rows (human track preferred, auto-generated
fallback, language selectable), `get_video_info` for metadata and which
transcript languages exist. Accepts every usual link shape and a bare
11-character video id.

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. Without it the sync
reports this entry as `invalid-url` and moves on.

No credential: nothing routes to the Service from outside the cluster.

Source: https://github.com/opspresso/mcp-youtube
