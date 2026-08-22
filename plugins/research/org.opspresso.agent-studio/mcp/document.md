---
description: >
  Read office documents — DOCX, PPTX, XLSX, HWP, HWPX, ODT/ODS/ODP, RTF — as
  text; inspect XLSX formulas without executing them; and create new XLSX,
  DOCX, PPTX, PDF or HWPX files the user receives. PDFs, plain text and web
  pages are read by Agent Studio itself, not here.
---

# document

Cluster-internal (`agent-mcps` namespace, no ingress), so registering it at all
depends on `MCP_INTERNAL_HOST_SUFFIXES` naming that suffix. No credential:
nothing routes to the Service from outside the cluster.

Four tools. `read_document` extracts text from a DOCX, PPTX, XLSX, HWP 5.x,
HWPX, OpenDocument or RTF file. `inspect_spreadsheet` returns addressed XLSX
values and formulas without executing them. `render_spreadsheet` creates a new
XLSX workbook from named rows and explicit formula cells. `render_document`
takes Markdown and returns a generated `.docx`, `.pptx`, `.pdf` or `.hwpx`.
Both renderers return the file **as bytes** — Agent Studio stores it as an
artifact and hands it to the user.

## What it deliberately does not do

Since v0.2.0 this server fetches nothing, stores nothing, and reads no PDF.
Each of those was a second copy of something Agent Studio already had — the
outbound SSRF boundary, the `unpdf` reader, an S3 bucket with its own retention
window — so what is left is the parser and renderer, and only those.

Consequences worth knowing when binding it:

- **No `url` parameter.** A model that has an address uses the `FetchUrl`
  builtin, which a version has to opt into (`urlFetch` in its parameters). This
  tool takes bytes the caller already holds.
- **No download link, and no tenant header.** The bytes come back in the tool
  result; the artifact row, the retention window and the delete button belong to
  Agent Studio. `x-document-tenant` is gone — remove it from any registry entry
  that still carries it.
- **PDF, plain text and HTML are refused by name**, pointing at the caller that
  reads them. That refusal is the design, not a gap.
- **The 97-2003 binaries (`.doc` `.xls` `.ppt`) stay refused.** They are record
  streams rather than containers, and a half-right parse of one produces
  something that *looks* like text — worse than saying no.

## Operating notes

- **No AWS role needed any more.** `pod-role--mcp-document` and its S3 grant
  were for the upload path and can be retired.
- A simple spreadsheet read returns cached values, never formulas, one heading
  per visible sheet, and cuts on a whole row so columns never come apart.
  `inspect_spreadsheet` is the formula-aware path: hidden sheets require opt-in,
  formulas are never recalculated, external links are not followed, and VBA is
  not executed. `render_spreadsheet` creates a new workbook; it does not edit or
  preserve styles, charts, macros, comments or links from an input workbook.
- A document read is content extraction, not original-preserving editing.
  Machine-readable `complete` and `omissions` state the boundary. Re-rendering
  extracted text creates a new package and may not preserve headers, footers,
  comments, tracked changes, notes, formatting, charts or relationships.
- A deck comes back as slide text in deck order, numbered; speaker notes are
  left out, being the presenter's script rather than the slide.
- **Writing a deck plans a deck.** An opening `#` is the cover
  (its first paragraph becomes the subtitle), every later `#` a numbered
  section divider, every `##` a slide; level 3 and below stay in the body. A
  slide whose shape says what it is gets a designed layout — two to four
  `###`s with a short line each become cards, short numeric bullets
  (`- 99.99% Availability`) become big-number metrics, a lone block quote with
  `— author` a quote slide, two `###`s under an "A vs B" title a two-column
  comparison, three to five short numbered steps a process flow with arrows,
  date-led steps (`1. Q1 파일럿`) a timeline, and a final 감사합니다 /
  Thank-you heading a closing slide. Recognition is conservative; wrapping one
  such group in `:::cards` … `:::` (also `metrics`, `comparison`, `process`,
  `timeline`, `quote`) forces the layout. Overflow breaks at sub-headings and
  titles the continuation `제목 — 소제목`; `(계속)` appears only when there was
  no boundary to break at.
- **Writing accepts a purpose profile independently of the file format.**
  `executive` (the default) is the restrained leadership style; `consulting`
  strengthens the strategy-deck accent; `formal` is square and print-first;
  `technical` uses restrained teal and light table headers; `standard` keeps
  the classic corporate-blue treatment. The profile changes palette, cover
  proportion, table contrast and card geometry, never the words or slide plan.
- **Writing a report designs a report**, and all three page
  formats — `docx`, `pdf`, `hwpx` — share the same reading of the structure:
  an opening `#` is a cover page with the first paragraph as its subtitle,
  every later `#` a numbered chapter opening on a fresh page, and a cover plus
  three or more level 1-2 headings adds a contents page. The DOCX and HWPX
  contents are complete as written, page numbers omitted — no `updateFields`,
  so Word opens with no "this document contains fields" dialog; the PDF is the
  one format whose pages this server lays out itself, so its contents page
  carries **real page numbers**. Quotes render as callout boxes everywhere;
  `:::metrics` (key-figure strip) and `:::comparison` (two-column table) are
  DOCX treatments, applied only when asked — a page never transforms prose
  unasked — and the other formats render the fenced content as plain blocks.
- **Korean documents state their language** without naming a font: DOCX
  carries `themeFontLang eastAsia="ko-KR"` (and its Latin follows the same
  east-Asian face, so 한글 and English sit in one font), PPTX labels runs
  `ko-KR` — which is what stops a non-Korean Office from setting 한글 in a
  Chinese or Japanese fallback face.
- **HWPX passes rhwp's lineseg validation** (the engine behind web viewers
  like hop): no paragraph over forty characters claims a single line segment,
  which is the rule that viewer warns on.
- **Images embed through `assets`** in `pptx`, `docx` and `pdf`:
  PNG or JPEG bytes sent by name beside the Markdown and referenced as
  `![caption](asset://name)`. A slide or paragraph that is exactly one such
  image becomes a captioned, aspect-true figure; an image inside prose stays a
  link, and a plain `![alt](url)` is never fetched. Up to 12 assets and 6MB
  decoded per call; SVG is refused with the fix named — rasterise first.
- **Output carries a designed, deliberately unbranded profile.** Every profile
  uses neutral ink, quiet rules and accessible contrast; none borrows the
  product's colours. Colour, type scale and spacing are the server's to decide,
  so a version chooses the purpose profile rather than prompting for arbitrary
  colours or fonts: "make the headings green" is ignored, `profile="technical"`
  is actionable.
- **A table column is aligned from the divider row.** `---:` sets it flush right
  and `:---:` centres it. Worth putting in a version's prompt for anything with
  figures in it — a column of numbers set left does not line up and nobody
  checks it.
- Every produced file records which release wrote it (PDF `Producer`, OOXML
  `<Application>`, OWPML `application`), which is the first thing to look at when
  a document renders oddly.
- RTF is read here rather than as plain text on purpose: it *is* a text file, so
  without a parser it arrives as thousands of control words with the prose
  scattered through them.
- Korean PDFs work: Nanum Gothic is embedded in the file, whole.
- A rendered document over 10MB is refused with a reason rather than cut by
  the transport, where it would surface as a parse failure saying nothing about
  the document being large.
- HWP 5.0 can be read but not written — writing offers HWPX instead.
- Successful renders include machine-readable structural validation. Office
  packages reopen through this server's reader and every internal relationship
  must resolve before bytes are returned. `visual=not_run` remains explicit:
  package validation does not prove appearance in Word, PowerPoint, Excel or
  한글.

Source: https://github.com/opspresso/mcp-document
