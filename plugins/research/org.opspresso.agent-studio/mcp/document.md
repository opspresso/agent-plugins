---
description: >
  Read document files — PDF, DOCX, HWP, HWPX — as text, from a URL or an upload,
  and write Markdown out as a DOCX, PDF or HWPX file the user downloads by link.
  Web pages belong to url-fetch.
---

# document

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. No credential:
nothing routes to the Service from outside the cluster.

Two tools. `read_document` takes a `url` or base64 `content` and returns the
text of a PDF, DOCX, HWP 5.x, HWPX or plain-text file. `write_document` takes
Markdown and returns a presigned download link for a generated `.docx`, `.pdf`
or `.hwpx` — the link, not the bytes, because a non-text blob cannot survive
the MCP result path.

## Writing is scoped by the `x-document-tenant` header

**Set this per version.** Written files land in S3 under
`documents/<tenant>/…`, so the header is what keeps one project's output out of
another's prefix. It is deliberately a header and not a tool argument: a tool
argument is chosen by the model, and a model that can name its own tenant can
write into another project's space — including one talked into it by a document
it just read.

Sync creates the entry with no headers, so set `x-document-tenant` in the
console before binding it to anything. Reading needs no tenant; a write without
one fails with the header named in the error.

## Operating notes

- Write needs the pod role: the ServiceAccount is bound to
  `pod-role--mcp-document` (terraform-env-demo/demo/8-role), which grants
  Get/Put on `agent-studio-document`. Until that role is applied, reads work
  and writes fail with the S3 reason in the tool result.
- Download links are presigned GETs valid for 7 days (SigV4's ceiling). The
  bucket stays private; nothing in it expires on its own.
- Korean PDFs work: Nanum Gothic is embedded in the file, whole.
- Boundaries the tools state themselves: web pages belong to url-fetch's
  `fetch_document`; a scanned PDF is an error naming OCR, never empty text;
  HWP 5.0 can be read but not written — writing offers HWPX instead.

Source: https://github.com/opspresso/mcp-document
