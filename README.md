# agent-plugins

A plugin monorepo following the [Agent Plugins 1.0.0](https://agent-plugins.org/)
specification. Skills and MCP servers ship together as **one plugin per domain**.

This repository replaces
[`agent-skills`](https://github.com/opspresso/agent-skills) and
[`agent-tools`](https://github.com/opspresso/agent-tools). Those two split the
same material by kind, so the skill and the servers that "investigate an
incident" needs lived in different repositories. Here they arrive as one
`devops` plugin.

**This repository targets Agent Studio.** The manifests and `SKILL.md` files
follow the published specs, so another conformant client can read them, but the
skills are written against Agent Studio's runtime and stop making sense outside
it — see [What the skills assume](#what-the-skills-assume). Anything that would
have to change for a second runtime is a change to this repository, not a
compatibility shim inside a skill.

Everything here is MIT-licensed ([`LICENSE`](LICENSE)), and every `plugin.json`
declares it.

## Layout

```
plugins/
  <plugin-name>/
    plugin.json                        # required: the plugin manifest
    mcp.json                           # optional: MCP server declarations
    skills/
      <skill-name>/
        SKILL.md                       # frontmatter + markdown body
    org.opspresso.agent-studio/        # optional: this org's client extension
      mcp/
        <server-name>.md
```

## Plugins

| Plugin | Skills | MCP servers |
|---|---|---|
| **devops** — investigate the cluster, change it through GitOps | gitops-change, incident-triage | argocd, cloudwatch, grafana, kubernetes, github |
| **research** — bring in material the model cannot reach, and write documents back out | document-authoring, spreadsheet-authoring | brave-search, aws-knowledge |
| **workspace** — write what moves around the company | korean-writing, korean-humanize, tech-spec | notion |
| **design** — build what a person will look at | html-wireframe, html-prototype, html-explainer, frontend-design, diagram-design, tufte-charts, html-report, image-generation | — |
| **engineering** — get a change reviewed and out the door | code-review, pr-description, engineering-writing | — |
| **agent-craft** — build agents and their interfaces | prompt-writer, skill-writer, mcp-writer, simple-orchestration, structured-output | — |
| **saju** — read a birth chart school by school | saju-analysis | — |

A plugin with no skills has no `skills/` directory, and one with no MCP servers
has no `mcp.json`. Do not create empty directories or empty manifests.

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

## Skills

Skills follow the Agent Skills specification as-is: `SKILL.md` is frontmatter
plus a markdown body, and the body is what the model reads once it loads the
skill.

**The frontmatter `name` must equal the directory name.** The two previous
repositories treated the directory as the truth and ignored `name`; the spec
requires them to match. To rename a skill, change the directory and `name`
together.

`description` should say **when to load the skill**, not what it is. The system
prompt carries only the name and description — the body loads at call time
(progressive disclosure) — so this is where routing is decided. Writing
guidance lives in
[`plugins/agent-craft/skills/skill-writer`](plugins/agent-craft/skills/skill-writer/SKILL.md).

### Description is the selection contract

Write each description so a model can select the capability without reading
operator notes, compatibility metadata or another skill first.

| Field | Model visibility | What belongs here |
|---|---|---|
| Skill `description` | Available Skills table before selection | User task, output, nearest competing task and essential tool/input conditions |
| Skill body (`content`) | Returned after an explicit `Skill` call | Detailed workflow and references; cannot rescue a missed selection |
| MCP extension `description` | Connected MCP Servers table | When to use this server, supported work, consequential limits and write boundaries |
| MCP extension body (`content`) | Operator-facing only | Setup, deployment and maintenance notes; no model-only instruction should live solely here |
| Individual MCP tool description and schema | Discovered from the server | Exact arguments and call behavior; not overridden by this repository's extension body |

Put the actual task first. Name an adjacent skill only when it prevents a likely
collision, rather than repeating the plugin's whole catalog. Keep prerequisites
that change whether a call can succeed in the description: an XLSX inspection
needs an accessible file ID, and an image edit needs both the builtin and an
image id. Describe observable limits without copying the full procedure into every run's prompt.
Two or three sentences usually suffice. Keep each sentence focused, but do not
remove a necessary capability or limit to meet a fixed count. Skill bodies carry
the executable workflow; MCP bodies carry connection, authentication, limits and
operator troubleshooting. Preserve user intent and existing authorization, and
avoid arbitrary question counts, output quotas or repeated approval steps.

Check descriptions alone against realistic requests and similar out-of-scope
requests. For example, distinguish a numeric chart from a dependency graph, an
interactive explanation page from a two-sentence explanation, and an HTML report
from an unspecified report file. Static validation detects lost frontmatter
lines; it does not prove that a model selects the right capability.

A skill directory may carry reference files alongside `SKILL.md`. Use them for
material too large for the body (bulk mapping tables, a full style guide), not
to split a few dozen lines of body.

**Only some of those files reach the model.** The sync carries `.md` `.txt`
`.json` `.yaml` `.yml` `.csv`, up to 64KB each and 20 attachments or 200KB of
attachments per skill. `SKILL.md` is not part of those attachment limits. The
sync leaves everything else behind — an executable script or a bundled asset
stays in git and is simply not there at run time. A body that tells the model to
run or copy such a file gives an instruction that cannot be followed, and nothing
reports it. `scripts/validate.py` fails the build on it; a template belongs in a
`.md` file as a fenced block, and work that would need a script belongs in an MCP
server instead.

## What the skills assume

The runtime is Agent Studio, and the skills are written to it rather than to a
generic client. Four assumptions run through them. A skill may document its
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
  directory, and a skill that instructs an MCP server ships in the plugin that
  declares it. Where that is genuinely impossible — code-review and
  pr-description read PRs through devops's `github` — the skill says in its body
  what it does when the server is not bound. Agent Memory is registered separately;
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

Writing skills carry the genre-specific rules needed to produce their own
results. Preserve facts, uncertainty, user templates and the intended audience.
Detailed prose guidance is optional; a missing companion skill must not prevent
the requested draft from being completed.

The full pattern catalog with before/after examples is
[`plugins/workspace/skills/korean-humanize/ai-tell-catalog.md`](plugins/workspace/skills/korean-humanize/ai-tell-catalog.md),
which supplies editing defaults, not an AI-authorship test. The user's style and
the original meaning take precedence. Load it only when `korean-humanize` is bound,
using `Skill(skill_name="korean-humanize", file_path="ai-tell-catalog.md")`;
otherwise follow the inline rules. Repository paths cannot be used as runtime
`file_path` values. Inside the **engineering** plugin the block lives in
[`engineering-writing`](plugins/engineering/skills/engineering-writing/SKILL.md);
code-review and pr-description point there rather than restating it, because it
installs alongside them.

The **design** plugin runs the same pattern against AI-looking *visuals* rather
than prose. The catalog is
[`plugins/design/skills/frontend-design/references/ai-visual-tells.md`](plugins/design/skills/frontend-design/references/ai-visual-tells.md)
— palette, type, layout, ornament, motion, and copy tells, each with a
replacement. html-report, diagram-design, tufte-charts, html-wireframe,
html-prototype and html-explainer each keep the genre-tuned rules they need
inline and point at frontend-design for the rest, naming the owning skill because
a skill cannot read another's directory.

The visual catalog is also a **default**,
and a skill that has deliberately decided otherwise for its genre wins — html-report
is single-theme on a white ground because the same report also leaves as a PDF,
html-wireframe stays deliberately unfinished, and html-explainer keeps motion
because in an explainer the movement is the explanation. Accessibility rows are
outside that ordering entirely. That rule lives in the catalog file rather than
here, because this README never reaches the model.

## mcp.json carries no credentials

**Never use `headers`.** The point is to leave no path by which a secret could
enter git. A declaration carries `type` and `url`, nothing else.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "aws-knowledge": {
      "type": "streamable-http",
      "url": "https://knowledge-mcp.global.api.aws"
    }
  }
}
```

A server that needs a token gets it **on the installing side** — in Agent
Studio, enter the header value in the console or connect via OAuth. The same
goes for installation-specific Agent Memory credentials. Register Agent Memory
outside these manifests so plugin sync does not take ownership of its settings.
Agent Studio supplies authenticated user identity in `X-User-Email`; do not put
user identity or credentials in skill text or tool arguments.

`type` is always `streamable-http`. A stdio server means launching a process on
the client machine, which is a different kind of thing from the in-cluster
servers declared here.

A private address like `*.svc.cluster.local` registers only where the
installing side allows that suffix. In Agent Studio that is
`MCP_INTERNAL_HOST_SUFFIXES`; without it the SSRF guard refuses the URL.

Agent Plugins 1.0.0 requires HTTPS for every non-loopback remote URL. The
cluster-local `http://*.agent-mcps.svc.cluster.local` entries are an explicit
Agent Studio deployment exception: they are reachable only inside the cluster
and are not portable to a strictly conformant client. The validator reports
every such entry; removing the exception requires TLS at the Service boundary.

## org.opspresso.agent-studio/ — client extension

This is the **reverse-domain client-extension namespace** the spec defines: the
place for what the spec itself does not carry. **A client that does not know
this name ignores the directory entirely** — that is the behaviour the spec
prescribes — so nothing put here can break another client's install.

`mcp/<server-name>.md` carries what `mcp.json` cannot, because the mcp.json
schema **has no description field.**

```markdown
---
description: "Search and edit Notion pages, databases and comments, and look up workspace users."
---

# notion

Operator notes, in markdown.
```

- **The frontmatter `description` goes to the model.** It becomes one cell of
  the system prompt's "Connected MCP Servers" table, so keep it **short and
  single-line** — a long one costs every run's prompt. If it needs multiple
  source lines, use `>` folding (as `aws-knowledge` does).
- **The body goes to operators only.** Unlike a skill's body it never reaches
  the model. Write setup steps, where credentials are filled in, and what is
  toggled on the deployment side.
- The file name is the server name. It must equal the key in `mcp.json`.

## Names are unique across the whole repository

Skill or MCP server, **the same name cannot appear twice — even in different
plugins.** The installing side's registry is flat: a plugin is a unit of
distribution, not a namespace. `devops/skills/tech-spec` and
`workspace/skills/tech-spec` cannot coexist; they collide at install time.

Search the whole repository for a name before adding a component.

## Validate before merging

    python3 scripts/validate.py

Checks every manifest against the 1.0.0 schemas, every `SKILL.md` against the
[Agent Skills specification](https://agentskills.io/specification), and every
name for the collision above. It also enforces this repository's no-header rule,
checks that every MCP declaration has exactly one Agent Studio extension document
with a description (and no extension is left without `mcp.json`), rejects malformed
hosts and ports, and reports the private-HTTP exceptions above. Frontmatter checks
use Agent Studio's flat scalar parsing, including paired quotes and `>-`/`|-`.
Prose that the parser would silently drop, including a misindented folded
description, fails validation instead of shortening the routing instruction.
Standard library only, no network.

`scripts/test_validate.py` pins the checker's own edges — where a limit stops
being a pass, which findings are recommendations rather than failures, and the
name collision, Studio registry slugs, UTF-16 description limits and skipped
symlinks — so a change to `validate.py` cannot loosen them unnoticed:

    python3 -m unittest discover -s scripts -p 'test_*.py'

The HTML report's executable table sorting is tested directly from its template
with Node's built-in test runner; no package installation is needed:

    node --test scripts/test_html_report.mjs

Both test suites and repository validation run in CI. Static checks do not
execute skills in a model or verify every prose reference; compare those paths
with each skill's stored attachment list when editing a workflow.

It is worth running because **neither kind of mistake fails loudly**. A skill
whose frontmatter breaks the spec is skipped by the client and loading carries
on, so the only symptom is a skill that is never called; a duplicated name gets
as far as the installing side before anything notices. CI runs these checks on every
pull request and on every push to main.

## How changes land

Merge to main and run the sync on the installing side. **This repository is
the source of truth**: in Agent Studio terms, whatever a plugin declares is
applied automatically — new names are created, and an already-registered name
is brought to this version whatever its origin, console edits and pre-plugin
hand registrations included. Change content here, not in the console. The one
thing the sync never touches is a hand-registered entry whose name no plugin
declares — the repository never claimed it.

**Deleting a directory does not delete the entry.** What the repository no
longer carries is reported as an orphan, and deleted only when named in the
console. An MCP entry holds credentials — a file disappearing from a branch is
not reason enough to remove it.

### Removing the retired MCP registrations

The `memory`, `document` and `youtube` entries are no longer declared. After
syncing this revision, inspect their orphan reports and affected version bindings,
then select those three retired entries for removal on the installing side.
Repository changes alone do not stop their deployments or remove stored registry
credentials. A separately registered Agent Memory entry remains independently
managed; do not include it in the retired-entry cleanup.

For versions that need memory, bind the separately registered Agent Memory server
and update prompts using the current `prompt-writer` guidance. Document workflows
use builtin `File` with configured artifact storage. Remove assumptions that
YouTube captions are available. Deployment resources belong to `dockpad` (IDC)
or `argocd-env-demo` (Kubernetes), not this plugin repository.
