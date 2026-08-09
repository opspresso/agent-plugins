---
description: "Search AWS documentation and read it as markdown: service docs, API references, What's New posts and Well-Architected guidance."
---

# aws-knowledge

Fully managed by AWS, public, and free — no auth, no AWS account. The only
entry here that needs no console follow-up after sync: no headers to fill in,
no Discover to run.

The URL is the bare host. There is no `/mcp` path — the root answers
`initialize` directly (verified against `AWSKnowledgeMCP` v1.0.0).

Being free, it is rate-limited on AWS's side. Heavy fan-out (an agent reading
many doc pages in one run) may get throttled; that shows up as tool errors,
not a registration problem.
