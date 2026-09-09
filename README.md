# agent-plugins

A collection of task-focused plugins using [Agent Plugins 1.0.0](https://agent-plugins.org/)
and [Agent Skills](https://agentskills.io/specification). Each plugin groups related
capabilities; the repository does not prescribe a cloud, organization, industry,
language or deployment topology. Everything is [MIT-licensed](LICENSE).

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
  mcp.json                            # optional, shared service endpoints only
  skills/<skill>/
    SKILL.md                          # selection description and task workflow
    references/                       # optional conditional guidance/templates
  org.opspresso.agent-studio/mcp/      # optional bundled server descriptions
    <server>.md
docs/
  agent-studio.md                      # client/runtime contracts for operators
  integrations/<server>.md             # separately registered service guidance
scripts/                              # repository validation, not skill payloads
```

A plugin without MCP declarations has no `mcp.json`. Do not create empty skill
folders or empty manifests. Skill and server names are unique across the whole
repository because the supported registry is flat.

## Plugins

| Plugin | Skills | Bundled MCP servers |
|---|---|---|
| devops | gitops-change, incident-triage | github |
| research | document-authoring, spreadsheet-authoring | aws-knowledge |
| workspace | korean-writing, korean-humanize, tech-spec, meeting-minutes, audio-processing | notion, plaud |
| design | html-wireframe, html-prototype, html-explainer, frontend-design, diagram-design, tufte-charts, html-report, image-generation | — |
| engineering | code-review, pr-description, engineering-writing | — |
| agent-craft | prompt-writer, skill-writer, mcp-writer, simple-orchestration, structured-output | — |
| saju | saju-analysis | — |

Bundling is not automatic tool availability or authorization. Bind the capabilities
needed for a run or use supported discovery. A writing request does not authorize
publishing, and a read request does not authorize mutations. Preserve permissions
already granted for the requested work.

## Integrations

Shared manifests contain actual provider-hosted endpoints. Account connections,
credentials, model selections, private addresses, regions and runtime bindings
belong to the installation. Never put credentials in manifests, URLs or skill text.
This repository permits only `streamable-http` declarations with `type` and `url`;
that is a repository policy, not the full MCP transport specification.

Infrastructure and search deployments vary by installation. Register these
separately using their real endpoint and adjust the suggested description to the
exposed tools:

- [Argo CD](docs/integrations/argocd.md)
- [CloudWatch](docs/integrations/cloudwatch.md)
- [Grafana](docs/integrations/grafana.md)
- [Kubernetes](docs/integrations/kubernetes.md)
- [Brave Search](docs/integrations/brave-search.md)

These operator references are not auto-synced declarations. The plugins do not
assume their hostnames, namespaces, upstream identities or RBAC. Removing a
bundled declaration does not remove an existing installation; see
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
It rejects non-loopback HTTP endpoints without a namespace-specific exception.
Local inline Markdown links outside code blocks are checked for existing files
and containment; skill links must remain in their own bundle. This is not a full
Markdown parser or a remote-link availability check.

Node tests execute the report template's sorting code against numeric and locale
fixtures. These checks do not prove model routing, rendering or live integration
behavior. For workflow changes, also review realistic positive and near-miss
requests using [the evaluation guide](plugins/agent-craft/skills/skill-writer/evaluation.md),
and distinguish scenario review from actual model/tool execution.
