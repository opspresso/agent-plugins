---
description: "Work with GitHub: repositories and code search, issues, pull requests, Actions and security alerts."
---

# github

Two ways in, and the entry carries both. A project that has connected via OAuth
uses its own token; everything else falls back to the entry's `Authorization`
header.

**OAuth needs a hand-registered app.** GitHub offers no dynamic client
registration, so the console's Discover step finds the endpoints but not a way to
create a client — register the OAuth app on GitHub and enter its credentials.

After the first sync the entry has neither credential. Run Discover for the OAuth
block, and add the `Authorization` header for the fallback.
