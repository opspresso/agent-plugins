---
description: >
  Search and read Notion pages, databases and comments, or find workspace users.
  Create and edit workspace content when requested through the project's
  connected Notion OAuth account; unavailable access requires supplied content.
---

# notion

The registry entry uses OAuth only, with no fallback header. Notion supports
dynamic client registration. After the first sync, run Discover once to populate
the OAuth block, then connect each project with its own account.

Access is determined by that project's connection and the content available to
the connected account. Verify a representative page or database read after
connecting; successful discovery alone does not establish workspace access.
