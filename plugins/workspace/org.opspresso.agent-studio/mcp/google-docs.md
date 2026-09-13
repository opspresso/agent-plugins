---
description: >
  Read Google Docs content and structure or update a specified document when
  requested. Requires the project's connected Google account and Workspace MCP
  Developer Preview access. Resolve ambiguous files through Drive; Google document
  IDs cannot be used as Agent Studio artifact IDs.
---

# google-docs

Follow [Google Workspace setup](../../../../docs/integrations/google-workspace.md).
The [Docs MCP reference](https://developers.google.com/workspace/docs/api/reference/mcp)
documents reading and updating native Google documents. Bind Drive search as
well if users need to locate documents by title instead of supplying IDs or links.

Verify a known document read. For an authorized edit, inspect the current
structure and identifiers, apply the requested change and read back the affected
content. Native document editing does not create a DOCX/PDF artifact or prove
exported layout fidelity.
