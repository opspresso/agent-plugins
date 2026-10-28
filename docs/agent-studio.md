# Host app integration

This document describes the `agent-studio` application's integration contract.
Its deployment name can change without changing the tool or plugin contract.
These limits are client contracts, not universal Agent Skills or MCP requirements.
Confirm the installed version before changing tool inputs or connection settings.

Agent profiles: [audio processing](audio-agent.md), [Workspace coding](code-agent.md),
[Kube SRE](kube-sre.md), [general-purpose assistant](sample-agent.md), and
[PR review automation](code-review-agent.md). The [saju interpreter](saju-agent.md)
profile keeps calculations separate from explanations in plain Korean.

## Companion project contracts

The sibling projects supply different parts of the runtime. Check their source
contracts before changing a plugin's tool instructions or connection settings.

| Project | Owns | Plugin consequence |
|---|---|---|
| `agent-studio` | Plugin sync, current Agent bindings, builtin tools, attachment extraction, artifact delivery, MCP file references and service result delivery to Chat | A component must be offered through saved bindings or enabled dynamic discovery; describe only inputs and results the run can access |
| `agent-models` | Model families, provider offerings, capabilities and pricing | A catalog, not an MCP server; use the available model `id`, not its provider `wireId`, in Agent settings |
| `agent-memory` | Long-term memories and short-term task handoffs | Bind the exact service URL, current caller and `recall`/`remember`/`handoff_*` scopes |
| `agent-knowledge` | Documents, RAG, knowledge graph, recordings, transcription, meeting notes, audio profiles and job history | Bind its Tools entry; audio runs through Agent Knowledge MCP tools with the user's audio profile |
| `agent-forge` | Workspaces, Sandbox execution, native sessions, checkpoints, Workspace profiles, Git connections, protected-action approvals and run history | Bind its Tools entry; coding work runs through Forge MCP tools with the user's Workspace profile |

### Service-owned tools

Studio has no builtin audio or Workspace tools. Agent Memory, Agent Knowledge and
Agent Forge are independent services. Studio connects to each only through MCP:

- Deployment settings (`MEMORY_*`, `KNOWLEDGE_*`, `FORGE_*`) create one Tools entry
  per service. Plugin sync does not own these entries.
- Each MCP connection is offered to the Agent as one native specialist. Every
  request carries a short-lived token delegated from the current Studio user.
- Each service owns its settings (named profiles), execution and history. People
  manage them in the service console; the Tools detail page shows the settings
  and history links the service advertises through
  `org.opspresso.agent.tool-management`.
- When a service accepts long-running work (`audio_job_submit`, `run_submit`,
  `repository_create` and their retries), Studio records the keyed submission and
  delivers the terminal result to the original Chat once. Agent Knowledge transcript and
  meeting-note outputs arrive as Chat files. An authenticated schedule tick
  (`/api/triggers/scan`) drives delivery.
- A tool parameter annotated with `org.opspresso.agent.file-reference` takes a
  Studio file ID. Studio converts it at dispatch to a short-lived verified
  reference that the service downloads. A recording attached in Chat becomes a
  Chat file whose ID is passed to Agent Knowledge `recording_import`. Recording
  attachments are limited to 512 MiB; larger recordings are uploaded in the Agent Knowledge console.
- Never resubmit uncertain work. Inspect the original request with
  `audio_request_status`, `run_lookup_request`, `workspace_lookup_request` or
  `repository_lookup_request`.

Document processing belongs to the host app's builtin `File` tool and artifact
store. It needs no MCP registration or separate server binding. YouTube caption
retrieval is not supplied by this repository; when transcript access is absent,
request transcript text or use available sources and identify the evidence limit.
Video metadata alone does not establish what was spoken.

### Agent Memory

Agent Memory owns durable memories and short-term task handoffs. `recall` searches
Memory only and returns compact text plus each memory's ID, version, content,
source and scope. `remember` writes scoped memory and can supersede observed versions, `revise` saves a new version of an observed memory, and `forget` archives an observed version.
`handoff_create/list/get/update/close` preserve progress with TTL and version checks;
Forge retains actual native sessions and file checkpoints.

Agent Knowledge's `context_search` combines document and graph evidence;
`document_search`, `knowledge_search` and `knowledge_neighborhood` narrow that
search. `document_ingest` uses a stable idempotency key and
`document_ingest_status` distinguishes accepted work from a ready document.

Automatic pre-run recall requires `memoryRecall` and an explicit Memory server
binding permitting `recall`; dynamic discovery alone does not enable it. IDs from
either service are not Studio Artifact IDs. Use the
[Memory connection notes](integrations/agent-memory.md) and
[Agent Knowledge connection notes](integrations/agent-knowledge.md). Current caller delegation
uses signed, audience-bound identity and explicit local bindings, never
`X-User-Email` or matching UUIDs.

### Endpoint ownership

`mcp.json` contains provider-hosted and declared in-cluster deployment addresses.
Other organization URLs, credentials, model selections and Agent bindings
belong to the installing side. Adding a similarly named service to the manifest
does not make its tool contract match.

### In-cluster MCP services

The `devops` plugin declares four MCP services deployed by the sibling
`argocd-env-apps` repository in k3s:

| Server | Streamable HTTP endpoint |
|---|---|
| `argocd` | `http://mcp-argocd.agent-mcps.svc.cluster.local/mcp` |
| `cloudwatch` | `http://mcp-cloudwatch.agent-mcps.svc.cluster.local/mcp` |
| `grafana` | `http://mcp-grafana.agent-mcps.svc.cluster.local/mcp` |
| `kubernetes` | `http://mcp-kubernetes.agent-mcps.svc.cluster.local/mcp` |

These are ClusterIP services in the `agent-mcps` namespace. The URLs use the
Service's HTTP port 80, not the container's target port. They require cluster
DNS and network reachability from the host app. The k3s deployment sets
`MCP_INTERNAL_HOST_SUFFIXES=agent-mcps.svc.cluster.local`; other installations
must configure the appropriate network access before using these declarations.
This setting permits internal connections; it does not grant upstream access.
Credentials and RBAC remain in the service deployments.

In the `argocd-env-apps` deployment, `argocd`, `grafana` and `kubernetes` are
read-only, and each MCP service admits only Agent Studio execution pods through a
NetworkPolicy. Agents investigate through these servers and change desired state
through the GitOps repository.

Sync the `devops` plugin to import the endpoints and matching MCP descriptions,
then bind the servers to the intended Agent's current settings or enable supported dynamic
discovery. Verify tool discovery and a representative authorized read for each
service from the host app. Registration alone does not verify the upstream credentials
or make the tools available to every agent.

### Google Workspace and Slack

The `workspace` plugin bundles Gmail, Drive, Calendar, Docs, Sheets, Slides and
Slack. Use [Google Workspace setup](integrations/google-workspace.md) and
[Slack connection notes](../plugins/workspace/org.opspresso.agent-studio/mcp/slack.md)
for eligibility and OAuth configuration. Google MCP endpoints are in Developer
Preview; Slack requires an eligible registered app. Both need installation-side
account connections before authenticated reads can be verified.

Google discovery requires the companion client's explicit handling of the
`https://accounts.google.com/` → `https://accounts.google.com` issuer alias;
older clients reject the metadata. Callback issuer validation remains exact.
Slack discovery accepts the official endpoint's challenged origin-level resource
identifier through a narrowly scoped alias. Older clients without these provider
aliases need an update. Manifest sync does not update the client or authorize an account.

The `email-triage`, `calendar-management` and `workspace-search` skills use only
the capabilities offered to the run. Native Google IDs are source identifiers,
not builtin `File` artifact IDs. Bind Drive search alongside native editors when
users identify documents by name, and verify actual import/export support before
promising Office files or downloads.

### Plaud recordings to meeting minutes

The `workspace` plugin declares the official [Plaud MCP](https://docs.plaud.ai/plaud-mcp-cli/mcp)
at `https://mcp.plaud.ai/mcp`. After sync, Discover its OAuth settings and connect
the intended Plaud account for the meeting Agent. Cloud Sync is required.
Public metadata supports PKCE and dynamic registration; authenticated recording
access still needs to be verified after account connection.

Plaud finds recordings and returns Plaud's existing transcripts and notes. The
plugin's `get_file` mapping hides the download URL behind an opaque `source_ref`,
but no current Studio or Agent Knowledge tool accepts `source_ref`. To transcribe a Plaud
recording with Agent Knowledge, the user attaches the audio file in Chat or uploads it in
the Agent Knowledge console; the `audio-processing` skill then runs `recording_import` →
`audio_job_submit`. Agent Knowledge publishes transcripts and meeting notes as search
documents; Memory records are written only on explicit request. Plaud's existing
transcript must not replace a requested Agent Knowledge transcription.

Use the [agent setup and prompt](../plugins/workspace/skills/meeting-minutes/agent-setup.md)
to configure the Agent and the [operator notes](../plugins/workspace/org.opspresso.agent-studio/mcp/plaud.md)
for connection and data handling. Credentials and installation-specific model
endpoints do not belong in these manifests.

## What the skills assume

When running these skills in the host app, the following constraints apply. A skill may document its
environment in `compatibility`, but the host app does not pass that field or
`allowed-tools` to the model or use them to configure permissions. Keep essential
conditions and fallbacks in the description and body:

- **No shell, no filesystem, no network of its own.** A skill cannot run `git`,
  execute a script, or fetch a URL. Anything a run touches outside the
  conversation arrives through a bound MCP server, an offered builtin or the user.
- **Builtins appear only when the run has them.** `GenerateImage`, `EditImage`,
  `SaveFile`, `File`, `FetchUrl`, `delegate_<name>` and `handoff_<name>` are offered
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

An Agent may also enable `dynamicCapabilities` to discover relevant catalog
entries for the request. This supplements explicit bindings; it does not make
every installed skill or tool available. Use the actual offered list and schemas.
OAuth-backed MCP discovery still requires that Agent's connection.

### Files and artifacts

The host app extracts attachments and, when artifact storage succeeds, retains
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

### MCP results visible to the model

For MCP results with non-empty `content`, the model receives those blocks, not
the accompanying `structuredContent`. Check visible counts and validation
messages; absent metadata is not proof that an extraction is complete. Server
authors must include model-critical metadata in text until the client carries
both representations.

## Skill attachments and parsing

Plugin sync in the host app carries `.md`, `.txt`, `.json`, `.yaml`, `.yml` and `.csv` reference
files: up to 64KiB each, 20 files and 200KiB total per skill. `SKILL.md` is excluded
from attachment limits. Executable scripts and binary assets are not carried.
Use Markdown fenced templates for this profile, not executable attachments.
These limits are enforced by this repository's validator.

Frontmatter uses the host app's parsing: flat scalars, indented `>`, `|`, `>-` or
`|-` blocks, and one level of `key: value` entries under a key with no value (the
Agent Skills `metadata` map). Multiline descriptions must not contain blank
continuation lines. Metadata does not configure runtime permissions. The
description limit also applies in UTF-16 code units. Confirm actual offered tools
and their schemas.

### Console icons

The console reads a plugin icon from `extensions.org.opspresso.agent-studio.icon`,
a skill icon from the `SKILL.md` metadata entry `org.opspresso.agent-studio.icon`,
and a bundled server icon from the `icon` frontmatter field of its extension
document. Values come from the host app's supported set: Tabler icon names and
service marks. A bundled server uses the mark of its service; a plugin or skill
uses an icon for the kind of work it does. See
[Console icons](../README.md#console-icons). Sync writes the icon with the entry.
When a plugin-owned server document no longer declares an icon, sync clears the
stored icon. An administrator sets icons for hand-registered entries in the
console. The console also shows the tool icons that an MCP server returns from
`tools/list`. It accepts only inline images (`data:`) and HTTPS images from the
server's own origin.

## Registration and sync ownership

Bundled MCP declarations contain only `type` and `url`; credentials belong to
the installing side. The four in-cluster services above are owned by the `devops`
plugin and sync updates their endpoints and descriptions. Register other
installation-specific integrations under distinct names so plugin sync does not
own their endpoint configuration. Do not add credentials or invent replacement
URLs in a manifest.

For an authorized private endpoint, configure the installing client's network
allowlist and the deployment's transport and authentication boundary. A suffix
allowlist is not proof of service authentication. The repository validator allows
internal HTTP only for the four declared server names and their exact URLs above;
other non-loopback endpoints must use HTTPS. This validation exception does not
change the client's network policy or the deployment's access controls.

Sync creates and updates declared names. It can overwrite console edits to
those entries, so change bundled content in this repository. Entries whose names
no plugin declares remain independently managed. Removing a declaration reports
an orphan; it does not delete the registration, credentials or deployment.
Inspect affected bindings before deciding whether to retain a separate entry or
remove it through the installing side. Repository edits do not authorize those
external actions.

## Persistent Workspace and Sandbox tasks

The execution plugin supplies reusable task guidance, not a shell or account credentials.
Bind the Agent Forge Tools entry and the workspace-task and sandbox-task skills.
The operator configures the Forge service, its Sandbox provider, worker and model gateway.
Each user creates a Workspace profile (runtime, central model, repository rules,
checks and deployment workflows), selects a default, connects GitHub and registers
repositories in the Forge console. The plugin grants none of these permissions.
The actual tool schemas remain authoritative. Model tool inputs cannot choose the
Forge URL, caller identity, organization or provider credentials.

### Start and observe a task

Read the profile with `profile_list`/`profile_get`, reuse an existing Workspace from
`workspace_list`, or create one with `workspace_create`. Prepare a repository with
a Git `prepare` run on an `agent/` branch, then submit command, native task or Git
steps with `run_submit`. One run executes per Workspace at a time. Keep
queued/running distinct from success. Read `run_result`, then `run_events` up to
`lastEventSeq` until `hasMore` is false; `outputLoss` remains a permanent warning.
`interrupted` means an uncertain external effect and is never replayed automatically.
Lost responses are reconciled with `run_lookup_request` or `workspace_lookup_request`,
not a new execution.

### Git publication

A coding request includes review, commit, work-branch push and pull-request runs
without another approval, unless the user limits the scope. Protected branch
publication, merge, tags, releases and deployment workflow dispatch require a
separate request and the Workspace owner's approval in the Forge console; MCP has
no approval tool. Tags bind to the reviewed HEAD; releases bind to an existing tag
and its exact commit. General agent descriptions and system prompts identify
capabilities; account, repository, branch and requested file changes belong in
each user's task input.
See the [Workspace agent profile](code-agent.md) for task bindings, runtime limits,
GitHub Actions toolset configuration and the general system prompt.
