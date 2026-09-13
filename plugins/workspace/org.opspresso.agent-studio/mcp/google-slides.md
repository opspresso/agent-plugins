---
description: >
  Read Google Slides presentation content and structure or update a specified
  presentation when requested. Requires the project's connected Google account
  and Workspace MCP Developer Preview access. Text or structural reads do not
  verify rendered layout or produce a PPTX/PDF artifact.
---

# google-slides

Follow [Google Workspace setup](../../../../docs/integrations/google-workspace.md).
The [Slides MCP reference](https://developers.google.com/workspace/slides/api/reference/mcp)
documents presentation reads and updates. Use Drive search when the presentation
must be found by name.

Verify a known presentation read. Before an authorized update, obtain the current
slide/object identifiers and constrain changes to the requested elements. Read
back affected content; perform visual verification only when the runtime offers
an actual rendering or preview capability.
