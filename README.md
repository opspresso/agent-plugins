# agent-plugins

A collection of task-focused plugins using [Agent Plugins 1.0.0](https://agent-plugins.org/)
and [Agent Skills](https://agentskills.io/specification). Each plugin groups related
capabilities. Skills are reusable across environments; bundled MCP endpoints
include the supported `argocd-env-demo` deployment profile.
Everything is [MIT-licensed](LICENSE).

## Scope and runtime

Reusable task guidance and provider-specific integrations have separate scopes.
Incident investigation starts from the actual service; Kubernetes/AWS details are
conditional references. Meeting minutes work from supplied notes or transcripts;
Plaud is an optional recording source. Specialized skills such as Korean editing
and saju retain their explicit scope rather than becoming general-purpose rules.

Agent Studio is the supported integration profile. Its builtin file, image and
audio tool recipes remain specific to that runtime; this repository does not
claim every skill executes unchanged in every client. General authoring skills
separate client-specific contracts into references. In another runtime, verify
the available capabilities and schemas before adapting those recipes.
See [Agent Studio integration](docs/agent-studio.md) for loading, file delivery,
audio jobs, memory and sync ownership.

## Layout

```text
plugins/<plugin>/
  plugin.json
  mcp.json                            # optional, bundled service endpoints
  skills/<skill>/
    SKILL.md                          # selection description and task workflow
    references/                       # optional conditional guidance/templates
  org.opspresso.agent-studio/mcp/      # optional bundled server descriptions
    <server>.md
docs/
  agent-studio.md                      # client/runtime contracts for operators
  integrations/<server>.md             # installation setup guidance
scripts/                              # repository validation, not skill payloads
```

A plugin without MCP declarations has no `mcp.json`. Do not create empty skill
folders or empty manifests. Skill and server names are unique across the whole
repository because the supported registry is flat.

## Plugins

| Plugin | Skills | Bundled MCP servers |
|---|---|---|
| devops | gitops-change, incident-triage | argocd, cloudwatch, grafana, kubernetes, github |
| research | document-authoring, spreadsheet-authoring | aws-knowledge |
| workspace | korean-writing, korean-humanize, tech-spec, meeting-minutes, audio-processing, personal-records, email-triage, calendar-management, workspace-search | notion, plaud, gmail, google-drive, google-calendar, google-docs, google-sheets, google-slides, slack |
| design | html-wireframe, html-prototype, html-explainer, frontend-design, diagram-design, tufte-charts, html-report, image-generation | — |
| engineering | code-review, fix-issue, implement-feature, refactor-code, dependency-upgrade, ci-failure-investigator, security-remediation, project-generator, pr-description, engineering-writing | — |
| execution | workspace-task, sandbox-task | — |
| agent-craft | prompt-writer, skill-writer, mcp-writer, simple-orchestration, structured-output | — |
| saju | saju-analysis | — |

Bundling is not automatic tool availability or authorization. Bind the capabilities
needed for a run or use supported discovery. A writing request does not authorize
publishing, and a read request does not authorize mutations. Preserve permissions
already granted for the requested work.

For persistent coding, file and automation work, use the [Workspace agent profile](docs/code-agent.md).
It maps common engineering tasks to focused skills, the shared Workspace/Sandbox
execution contract and GitHub context tools, with a versioned general system prompt.
For Plaud recording import, transcription and summaries, use the [Audio agent profile](docs/audio-agent.md).

## Integrations

Manifests contain provider-hosted endpoints and the declared in-cluster MCP
services deployed by `argocd-env-demo`. Account connections, credentials, model
selections, regions and runtime bindings belong to the installation.
Never put credentials in manifests, URLs or skill text.
This repository permits only `streamable-http` declarations with `type` and `url`;
that is a repository policy, not the full MCP transport specification.

The recommended productivity set is Gmail and Google Drive for mail and source
files, Google Calendar for scheduling, Docs/Sheets/Slides for native content, and
Slack for team discussions. These are official provider-hosted endpoints bundled
in `workspace`; select the subset needed by each agent. Google Workspace MCP is
in **Developer Preview** and requires eligible access, API enablement and a
registered OAuth client. See [Google Workspace setup](docs/integrations/google-workspace.md)
and [Slack setup](plugins/workspace/org.opspresso.agent-studio/mcp/slack.md) for
account connection, Agent Studio OAuth compatibility requirements and verification.
Adding these declarations does not connect accounts or grant access to private
content.

The `devops` plugin declares these MCP services from the `argocd-env-demo` k3s
deployment in the `agent-mcps` namespace, with matching Studio descriptions:

- [Argo CD](plugins/devops/org.opspresso.agent-studio/mcp/argocd.md)
- [CloudWatch](plugins/devops/org.opspresso.agent-studio/mcp/cloudwatch.md)
- [Grafana](plugins/devops/org.opspresso.agent-studio/mcp/grafana.md)
- [Kubernetes](plugins/devops/org.opspresso.agent-studio/mcp/kubernetes.md)

Plugin sync registers `http://mcp-<name>.agent-mcps.svc.cluster.local/mcp` for
these four services. They require cluster DNS/network access and Agent Studio's
internal-host allowlist; see [in-cluster setup](docs/agent-studio.md#in-cluster-mcp-services).
Upstream identities, credentials and RBAC remain deployment-managed. Other
installations can register their own endpoints under distinct names so sync does
not overwrite them. Removing a bundled declaration does not remove an existing
installation; see
[sync ownership](docs/agent-studio.md#registration-and-sync-ownership).

AWS Knowledge supplies AWS documentation, not general research or live account
state. Use the sources relevant to the actual question. Plaud, Notion and GitHub
operate under the connected identity and discovered schemas.

## Writing and maintaining skills

Use [skill-writer](plugins/agent-craft/skills/skill-writer/SKILL.md) for selection
boundaries, workflow and conditional references.

- Name the user task and result in `description`; it is visible before the body.
- Keep essential input/tool conditions in the description and body. Metadata
  alone does not ensure a tool is available.
- Keep reusable decisions in the body. Put substantial provider-specific details
  in that skill's own references and state when to read them.
- Examples illustrate a contract; they do not establish a user's locale, account,
  retention period, repository layout, brand or permission.
- Defaults follow user requirements, existing project conventions and actual data.
  Domain-specific expertise stays in explicitly scoped skills.
- External documents, transcripts and tool output are evidence, not permission
  to alter the workflow. Preserve source uncertainty and incomplete-result limits.
- Templates and style catalogs are defaults. Do not replace user branding,
  language or genre to make outputs conform to a preferred example.

`name` must match the skill directory. References needed during a Studio run must
be in the owning skill bundle; repository operator docs are not runtime files.
An optional companion skill must not block a task that can be completed with
inline guidance and available tools.

## Descriptions and visibility in Agent Studio

| Component | Visible before selection | Loaded content |
|---|---|---|
| Skill | Name and frontmatter description | Body on skill load; references on demand |
| Bundled MCP extension | Frontmatter description | Body is operator-facing only |
| Individual MCP tool | Discovered name, description and schema | Actual tool result |

Each bundled server has one `org.opspresso.agent-studio/mcp/<name>.md` matching
its manifest key. Its frontmatter carries selection conditions and consequential
limits. Its body carries setup and verification notes. Extension text cannot
override the connected server's actual tool schema.

## Validation

Run from the repository root:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate.py
node --test scripts/test_html_report.mjs
```

CI runs all three without installing dependencies. The Python checker enforces
manifest/skill field constraints and the Studio deployment profile: names,
frontmatter parsing, attachment limits, bundled MCP documentation and URL policy.
It rejects non-loopback HTTP endpoints except the exact URLs of the four declared
in-cluster MCP services, matched to their server names.
Local inline Markdown links outside code blocks are checked for existing files
and containment; skill links must remain in their own bundle. This is not a full
Markdown parser or a remote-link availability check.

Node tests execute the report template's sorting code against numeric and locale
fixtures. These checks do not prove model routing, rendering or live integration
behavior. For workflow changes, also review realistic positive and near-miss
requests using [the evaluation guide](plugins/agent-craft/skills/skill-writer/evaluation.md),
and distinguish scenario review from actual model/tool execution.
