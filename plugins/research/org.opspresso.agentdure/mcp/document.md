---
description: >
  Read office documents — DOCX, PPTX, XLSX, HWP, HWPX, ODT/ODS/ODP, RTF — as
  text, and write Markdown out as a DOCX, PPTX, PDF or HWPX file the user
  receives. PDFs, plain text and web pages are read by AgentDure itself, not
  here.
---

# document

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. No credential:
nothing routes to the Service from outside the cluster.

Two tools. `read_document` takes base64 `content` and returns the text of a
DOCX, PPTX, XLSX, HWP 5.x, HWPX, OpenDocument or RTF file. `render_document`
takes Markdown and returns the generated `.docx`, `.pptx`, `.pdf` or `.hwpx`
**as bytes** — AgentDure stores it as an artifact and hands it to the user.

## What it deliberately does not do

Since v0.2.0 this server fetches nothing, stores nothing, and reads no PDF.
Each of those was a second copy of something AgentDure already had — the
outbound SSRF boundary, the `unpdf` reader, an S3 bucket with its own retention
window — so what is left is the parser, and only the parser.

Consequences worth knowing when binding it:

- **No `url` parameter.** A model that has an address uses the `FetchUrl`
  builtin, which a version has to opt into (`urlFetch` in its parameters). This
  tool takes bytes the caller already holds.
- **No download link, and no tenant header.** The bytes come back in the tool
  result; the artifact row, the retention window and the delete button belong to
  AgentDure. `x-document-tenant` is gone — remove it from any registry entry
  that still carries it.
- **PDF, plain text and HTML are refused by name**, pointing at the caller that
  reads them. That refusal is the design, not a gap.
- **The 97-2003 binaries (`.doc` `.xls` `.ppt`) stay refused.** They are record
  streams rather than containers, and a half-right parse of one produces
  something that *looks* like text — worse than saying no.

## Operating notes

- **No AWS role needed any more.** `pod-role--mcp-document` and its S3 grant
  were for the upload path and can be retired.
- A spreadsheet comes back as values, never formulas, one heading per sheet, and
  the read is cut on a whole row so columns never come apart.
- A deck comes back as slide text in deck order, numbered; speaker notes are
  left out, being the presenter's script rather than the slide.
- **Writing a deck splits on headings.** In `pptx` every level 1 or 2 heading
  starts a slide and becomes its title, so a version prompting for one should
  say "one heading per slide, a few bullets under each". Level 3 and below stay
  in the body, and content that does not fit continues on a slide titled
  `… (계속)`. A document written as prose renders as one long slide per section.
- RTF is read here rather than as plain text on purpose: it *is* a text file, so
  without a parser it arrives as thousands of control words with the prose
  scattered through them.
- Korean PDFs work: Nanum Gothic is embedded in the file, whole.
- A rendered document over 10MB is refused with a reason rather than cut by
  the transport, where it would surface as a parse failure saying nothing about
  the document being large.
- HWP 5.0 can be read but not written — writing offers HWPX instead.

Source: https://github.com/opspresso/mcp-document
