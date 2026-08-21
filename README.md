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
| **research** — bring in material the model cannot reach, and write documents back out | document-authoring | brave-search, youtube, document, aws-knowledge |
| **workspace** — write what moves around the company | korean-writing, korean-humanize, tech-spec | notion |
| **design** — build what a person will look at | frontend-design, tufte-charts, html-report, image-generation | — |
| **engineering** — get a change reviewed and out the door | code-review, pr-description, engineering-writing | — |
| **agent-craft** — build the agents themselves | prompt-writer, skill-writer, simple-orchestration, structured-output | memory |
| **saju** — read a birth chart school by school | saju-analysis | — |

A plugin with no skills has no `skills/` directory, and one with no MCP servers
has no `mcp.json`. Do not create empty directories or empty manifests.

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

A skill directory may carry reference files alongside `SKILL.md`. Use them for
material too large for the body (bulk mapping tables, a full style guide), not
to split a few dozen lines of body.

**Only some of those files reach the model.** The sync carries `.md` `.txt`
`.json` `.yaml` `.yml` `.csv`, up to 64KB each and 20 files or 200KB per skill,
and it leaves everything else behind — an executable script or a bundled asset
stays in git and is simply not there at run time. A body that tells the model to
run or copy such a file gives an instruction that cannot be followed, and nothing
reports it. `scripts/validate.py` fails the build on it; a template belongs in a
`.md` file as a fenced block, and work that would need a script belongs in an MCP
server instead.

## What the skills assume

The runtime is Agent Studio, and the skills are written to it rather than to a
generic client. Three assumptions run through them, and a skill that depends on
one says so in its `compatibility` frontmatter:

- **No shell, no filesystem, no network of its own.** A skill cannot run `git`,
  execute a script, or fetch a URL. Anything a run touches outside the
  conversation arrives through a bound MCP server or through the user.
- **Builtins appear only when the run has them.** `GenerateImage`, `EditImage`,
  `dispatch_agents` and `transfer_to_agent` are offered per run, so
  image-generation and simple-orchestration state what they do when the tool is
  absent from the list.
- **A plugin is the install unit.** A skill loads files only from its own
  directory, and a skill that instructs an MCP server ships in the plugin that
  declares it. Where that is genuinely impossible — code-review and
  pr-description read PRs through devops's `github` — the skill says in its body
  what it does when the server is not bound.

Ten skills hand Korean prose to a person, and each carries a short, genre-tuned
rule set against AI-sounding Korean in its own body — korean-writing,
korean-humanize, document-authoring, tech-spec, incident-triage, gitops-change,
simple-orchestration, saju-analysis, prompt-writer and engineering-writing. The
duplication is deliberate: a plugin is the install unit and a skill can only load
files from its own directory, so a rule that lives elsewhere is a rule that never
arrives.

The full pattern catalog with before/after examples is
[`plugins/workspace/skills/korean-humanize/ai-tell-catalog.md`](plugins/workspace/skills/korean-humanize/ai-tell-catalog.md),
and when an inline rule and the catalog disagree the catalog wins. **Every inline
block must name it**, or a run that loaded only that skill has no way to know the
catalog exists. Inside the **engineering** plugin the block lives in
[`engineering-writing`](plugins/engineering/skills/engineering-writing/SKILL.md);
code-review and pr-description point there rather than restating it, because it
installs alongside them.

## mcp.json carries no credentials

**Never use `headers`.** The point is to leave no path by which a secret could
enter git. A declaration carries `type` and `url`, nothing else.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "document": {
      "type": "streamable-http",
      "url": "http://mcp-document.agent-mcps.svc.cluster.local/mcp"
    }
  }
}
```

A server that needs a token gets it **on the installing side** — in Agent
Studio, enter the header value in the console or connect via OAuth. The same
goes for tenant-scoping headers (`X-Memory-Tenant`): they are set per version
in the console, not in this repository. Why those are
headers rather than tool arguments is explained in each server's extension
document.

`type` is always `streamable-http`. A stdio server means launching a process on
the client machine, which is a different kind of thing from the in-cluster
servers declared here.

A private address like `*.svc.cluster.local` registers only where the
installing side allows that suffix. In Agent Studio that is
`MCP_INTERNAL_HOST_SUFFIXES`; without it the SSRF guard refuses the URL.

## org.opspresso.agent-studio/ — client extension

This is the **reverse-domain client-extension namespace** the spec defines: the
place for what the spec itself does not carry. **A client that does not know
this name ignores the directory entirely** — that is the behaviour the spec
prescribes — so nothing put here can break another client's install.

`mcp/<server-name>.md` carries what `mcp.json` cannot, because the mcp.json
schema **has no description field.**

```markdown
---
description: "Read office documents — DOCX, XLSX, PPTX, HWP, HWPX — as text."
---

# document

Operator notes, in markdown.
```

- **The frontmatter `description` goes to the model.** It becomes one cell of
  the system prompt's "Connected MCP Servers" table, so keep it **short and
  single-line** — a long one costs every run's prompt. If it needs multiple
  source lines, use `>` folding (`memory` and `document` do).
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
name for the collision above. Standard library only, no network.

It is worth running because **neither kind of mistake fails loudly**. A skill
whose frontmatter breaks the spec is skipped by the client and loading carries
on, so the only symptom is a skill that is never called; a duplicated name gets
as far as the installing side before anything notices. CI runs this on every
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
