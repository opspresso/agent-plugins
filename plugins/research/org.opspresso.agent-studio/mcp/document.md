---
description: >
  Create DOCX/PPTX/PDF/HWPX documents from Markdown or XLSX workbooks from rows
  and explicit formulas; extract Office/HWP/HWPX/ODF/RTF text and inspect document structure or
  XLSX formulas. Reading and inspection require original base64 bytes, which
  Studio attachments do not expose for reuse. PDF reading, formula calculation
  and original-preserving edits are unsupported.
---

# document

## Connection and authentication

The bundled endpoint uses the internal `agent-mcps.svc.cluster.local` suffix,
which must be allowed by `MCP_INTERNAL_HOST_SUFFIXES`. The deployment exposes
no ingress. With `MCP_API_KEY` unset, any caller that can reach the service is
trusted. When it is set, configure the matching Bearer credential in the registry.

## Capabilities

| Tool | Input and result |
|---|---|
| `read_document` | Original DOCX/PPTX/XLSX/HWP/HWPX/ODT/ODS/ODP/RTF bytes to Markdown text |
| `inspect_document` | Original document bytes to block structure and previews; refuses XLSX |
| `inspect_spreadsheet` | Original XLSX bytes to addressed values, formulas and warnings |
| `render_document` | Markdown to DOCX/PPTX/PDF/HWPX bytes |
| `render_spreadsheet` | Named rows and explicit formula cells to new XLSX bytes |

The server does not fetch URLs, store files or issue download links. Agent
Studio owns artifact delivery, retention and deletion. No tenant header or
AWS storage role is required. PDF, plain text, HTML and legacy DOC/XLS/PPT
inputs are unsupported. HWP 5.x is readable; writing uses HWPX.

## Studio integration

Attachments and enabled `FetchUrl` Office reads return extracted text to the
model, not original bytes or a reusable input handle. Generated artifacts
likewise return a delivery notice. Inspection, embedded images and generated
file reinspection therefore require a separate byte-input path.

When an MCP result has non-empty `content`, Studio does not also forward
`structuredContent`. Full `omissions`, `counts` and `validation` metadata
need client support or a server text representation. Visible renderer text
reports package validation and the absence of visual validation.

## Limits and verification

- Requests are limited to 16MiB; decoded source files to 12MiB. Base64 overhead
  counts toward the request limit. Extracted text is capped at 90,000 characters.
- Document inspection returns up to 500 blocks per call, with zero-based
  `from` and inclusive `to`. Spreadsheet inspection is capped at 10,000 cells
  and has no sheet, range or pagination arguments.
- Spreadsheet reads return cached values from visible sheets. Formula inspection
  does not calculate formulas, follow external links or execute VBA. Hidden
  sheets require opt-in.
- Extraction and regeneration do not preserve the original package. Omissions
  include unsupported features and observed losses; HWP 5.x heading levels are
  not recovered.
- Markdown generation accepts 500,000 characters. PPTX/DOCX/PDF can embed up to
  12 PNG/JPEG assets totaling 6MiB; URLs are never fetched. HWPX images are links.
  Rendered files are limited to 10MB.
- Office outputs are reopened and internal package relationships validated.
  `visual=not_run` means layout has not been checked in an Office viewer.
  File producer metadata identifies the server release for rendering diagnosis.

The `document-authoring` and `spreadsheet-authoring` skills describe authoring
procedures, supported profiles and Markdown layout rules. Layout directives
still require content to fit their supported shapes and sizes.

Source: https://github.com/opspresso/mcp-document
