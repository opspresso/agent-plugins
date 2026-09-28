---
description: >
  Read Google Sheets structure and cell values; update specified values, formulas
  or sheet structure when requested. Requires the project's connected Google
  account and Workspace MCP Developer Preview access. Confirm spreadsheet, tab
  and range; this accesses a live sheet rather than an XLSX artifact.
  Preserve existing styles; use the offered spreadsheet-authoring design contract
  for new sheets and keep formatting writes separate from value/formula writes.
---

# google-sheets

Follow [Google Workspace setup](../../../../docs/integrations/google-workspace.md).
The [Sheets MCP reference](https://developers.google.com/workspace/sheets/api/reference/mcp)
describes spreadsheet metadata, values, formulas and structural updates.
Use discovered schemas for ranges and input interpretation.

Verify metadata and a small known range. For requested updates, distinguish raw
values, formatted values and formulas, preserve unrelated cells and read back
the affected range. Do not assume locale-dependent date/number parsing or claim
an XLSX file was created by a native Sheets operation.
