---
description: >
  Search and read Notion pages, databases and comments to answer questions from
  workspace content; look up workspace users. Create or edit content only when
  requested. Requires the project's connected Notion OAuth account; if access
  is unavailable, ask for the relevant content rather than claiming it was read.
---

# notion

OAuth only — no fallback header. Notion offers dynamic client registration, so
the console's Discover step is enough to set the entry up; each project then
connects with its own account.

Sync creates the entry without the OAuth block. Run Discover once after the first
sync, then connect per project.
