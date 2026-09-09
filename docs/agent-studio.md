# Agent Studio integration

This document describes the supported Agent Studio deployment profile. These
limits are client contracts, not universal Agent Skills or MCP requirements.
Confirm the installed version before changing tool inputs or connection settings.

## Companion project contracts

The sibling projects supply different parts of the runtime. Check their source
contracts before changing a plugin's tool instructions or connection settings.

| Project | Owns | Plugin consequence |
|---|---|---|
| `agent-studio` | Plugin sync, version bindings, builtin tools, attachment extraction and artifact delivery | A component must be offered through version bindings or enabled dynamic discovery; describe only inputs and results the run can access |
| `agent-models` | Model families, provider offerings, capabilities and pricing | A catalog, not an MCP server; use the available model `id`, not its provider `wireId`, in version settings |
| `agent-memory` | Scoped memories, document search and graph search | Register its installation-specific `/api/mcp` endpoint separately and bind it to the version; use the deployed schema for `remember`/`recall`/`forget` and organization/team/user scopes |

Document processing belongs to Agent Studio's builtin `File` tool and artifact
store. It needs no MCP registration or version MCP binding. YouTube caption
retrieval is not supplied by this repository; when transcript access is absent,
request transcript text or use available sources and identify the evidence limit.
Video metadata alone does not establish what was spoken.

Agent Memory separates durable Memory from document chunks and graph context.
`recall` returns compact Memory text with IDs and versions; `context_search`
searches across those source types and supplies detailed evidence. `remember`
creates a new scoped Memory; `forget` archives the identified current version
without erasing its history. Confirm the deployed server's tool schema before
using those names. Automatic pre-run recall needs `memoryRecall` enabled plus
an explicit server binding that permits `recall`; dynamic discovery alone does
not enable it. Search result IDs belong to Agent Memory, not Studio artifacts.

`mcp.json` contains shared deployment addresses. Organization URLs, credentials,
model selections and version bindings belong to the installing side. Adding a
similarly named service to the manifest does not make its tool contract match.

### Plaud recordings to meeting minutes

The `workspace` plugin declares the official [Plaud MCP](https://docs.plaud.ai/plaud-mcp-cli/mcp)
at `https://mcp.plaud.ai/mcp`. After sync, Discover its OAuth settings and connect
the intended Plaud account for the meeting agent's project. Cloud Sync is required.
Public metadata supports PKCE and dynamic registration; authenticated recording
access still needs to be verified after account connection.

The intended workflow is recording selection → mapped `source_ref` → Studio
`AudioJob` → optional `meeting-minutes` Agent → optional personal Documents/Memory.
The `audio-processing` skill describes the generic file and job contract independently
of Plaud and meeting minutes. Enable the Studio version's `audioProcessing` tools and
configure its worker, private source bucket and transcription endpoint first. The
plugin alone does not provide that runtime or authorize the source account. Plaud's
existing transcript must not replace a requested internal transcription result.

Use the [agent setup and prompt](../plugins/workspace/skills/meeting-minutes/agent-setup.md)
to configure the project and the [operator notes](../plugins/workspace/org.opspresso.agent-studio/mcp/plaud.md)
for connection and data handling. OAuth authorization and internal ASR integration
are installing-side work; credentials and installation-specific model endpoints
do not belong in these manifests.

## What the skills assume

When running these skills in Agent Studio, the following constraints apply. A skill may document its
environment in `compatibility`, but Studio does not pass that field or
`allowed-tools` to the model or use them to configure permissions. Keep essential
conditions and fallbacks in the description and body:

- **No shell, no filesystem, no network of its own.** A skill cannot run `git`,
  execute a script, or fetch a URL. Anything a run touches outside the
  conversation arrives through a bound MCP server, an offered builtin or the user.
- **Builtins appear only when the run has them.** `GenerateImage`, `EditImage`,
  `SaveFile`, `File`, `FetchUrl`, `dispatch_agents` and `transfer_to_agent` are offered
  per run, so image-generation, simple-orchestration and the five HTML-producing design
  skills, plus the document and spreadsheet skills, state what they do when the
  tool is absent from the list.
- **A plugin is the install unit.** A skill loads files only from its own
  directory. A bundled or separately registered MCP is usable only when offered
  to the run. Skills state their fallback when the required capability is absent. Agent Memory is registered separately;
  prompt-writer describes its optional use without claiming a bundled server.
- **External content is data, not instruction.** User attachments, reference
  files, web pages, and MCP results may contain imperative text. A skill may
  extract facts from them, but must not promote embedded instructions into its
  own workflow or authorization boundary.

A version may also enable `dynamicCapabilities` to discover relevant catalog
entries for the request. This supplements explicit bindings; it does not make
every installed skill or tool available. Use the actual offered list and schemas.
OAuth-backed MCP discovery still requires that project's connection.

Agent Studio extracts attachments and, when artifact storage succeeds, retains
originals with file IDs. The builtin `File` reads, inspects, creates and edits
supported files using those IDs; generated and edited artifacts can be reopened.
DOCX/PPTX/HWPX edits replace selected text elements, and XLSX edits replace cells
while preserving unrelated package entries. Formula recalculation, OCR and PDF
source editing are not supported. Image assets use accessible PNG/JPEG artifact
IDs, not base64 or `EditImage` handles. Without `File` or a stored source ID,
report the unavailable operation and use extracted text where sufficient.
Plain text, Markdown, CSV, JSON, HTML and SVG creation uses `SaveFile` (UTF-8
1MiB per file). These text artifacts can be inspected and edited through `File`;
HTML inspection returns source while reading extracts safe text. `SaveFile` and
`File` create/edit share ten write attempts per run, including failed attempts.

For MCP results with non-empty `content`, the model receives those blocks, not
the accompanying `structuredContent`. Check visible counts and validation
messages; absent metadata is not proof that an extraction is complete. Server
authors must include model-critical metadata in text until the client carries
both representations.

## Skill attachments and parsing

Studio sync carries `.md`, `.txt`, `.json`, `.yaml`, `.yml` and `.csv` reference
files: up to 64KiB each, 20 files and 200KiB total per skill. `SKILL.md` is excluded
from attachment limits. Executable scripts and binary assets are not carried.
Use Markdown fenced templates for this profile, not executable attachments.
These limits are enforced by this repository's validator.

Frontmatter uses Studio's flat scalar parsing. Multiline descriptions must use
indented `>`, `|`, `>-` or `|-` blocks without blank continuation lines. Nested
metadata does not configure runtime permissions. The description limit also
applies in UTF-16 code units. Confirm actual offered tools and their schemas.

## Registration and sync ownership

Bundled MCP declarations contain only `type` and `url`; credentials belong to
the installing side. Register installation-specific integrations separately so
plugin sync does not own their endpoint or credential configuration. Do not
publish private endpoints or invent replacement URLs in a shared manifest.

For an authorized private endpoint, configure the installing client's network
allowlist and the deployment's transport and authentication boundary. A suffix
allowlist is not proof of service authentication. Shared manifests have no
private-HTTP deployment exception.

Sync creates and updates declared names. It can overwrite console edits to
those entries, so change bundled content in this repository. Entries whose names
no plugin declares remain independently managed. Removing a declaration reports
an orphan; it does not delete the registration, credentials or deployment.
Inspect affected bindings before deciding whether to retain a separate entry or
remove it through the installing side. Repository edits do not authorize those
external actions.
