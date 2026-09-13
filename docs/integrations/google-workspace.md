# Google Workspace MCP

The `workspace` plugin bundles Google's provider-hosted MCP endpoints. They are
in **Developer Preview**, with access governed by Google's preview program.
Follow the current [Google configuration guide](https://developers.google.com/workspace/guides/configure-mcp-servers)
for eligibility, API enablement, consent-screen setup and OAuth client creation.
Manifest sync alone does not connect an account.

## Recommended services

| Bundled name | Purpose | Google API / MCP service |
|---|---|---|
| `gmail` | Mail context, reply drafts and labels | `gmail.googleapis.com` / `gmailmcp.googleapis.com` |
| `google-drive` | Locate files and retrieve source content | `drive.googleapis.com` / `drivemcp.googleapis.com` |
| `google-calendar` | Availability, meeting times and requested event changes | `calendar-json.googleapis.com` / `calendarmcp.googleapis.com` |
| `google-docs` | Read and edit native documents | `docs.googleapis.com` / `docsmcp.googleapis.com` |
| `google-sheets` | Read and edit live spreadsheet data | `sheets.googleapis.com` / `sheetsmcp.googleapis.com` |
| `google-slides` | Read and edit native presentations | `slides.googleapis.com` / `slidesmcp.googleapis.com` |

Gmail and Drive form the mail-and-source workflow. Calendar supports scheduling;
the three editors preserve native document structure. Slack complements them
with team discussion context; see its
[connection notes](../../plugins/workspace/org.opspresso.agent-studio/mcp/slack.md).
Bind only the services needed by the agent. Existing Notion, Plaud and GitHub
integrations remain available for their respective sources.

## Connect in Agent Studio

Check [discovery compatibility](#agent-studio-discovery-compatibility) before
starting account authorization. The declarations are ready to sync; the current
companion client's metadata checks prevent Google OAuth discovery from completing.

1. Confirm preview access and enable the corresponding API and MCP service in
   the selected Google Cloud project. Configure consent and test users as needed.
2. Create a web OAuth client with the callback URL shown by the actual Agent
   Studio deployment. Use that deployment's callback, not a sample Claude or
   Antigravity callback.
3. Sync the plugin, Discover each selected server's OAuth metadata and save the
   client ID and secret in the project's connection settings. A registered
   Google OAuth client is required; do not assume dynamic client registration.
4. Select scopes for the intended tools and connect the intended account per
   server. Google documents `gmail.readonly` for mail reads and `drive.readonly`
   for file reads. Use the complete scope URIs and requirements from its guide.

Credentials, consent and refresh tokens belong to the installing side. Do not
copy them into shared manifests, screenshots, skill text or tool arguments.
Discover is metadata retrieval; Connect authorizes the account. Neither proves
that every tool is permitted for every file or calendar.

Granting a scope and enabling a tool are separate decisions. A readonly setup
may discover tools that it cannot execute. For edits, consult the selected tool's
current scope requirements and grant only the intended operations. Gmail compose
permission does not establish a send tool, and the Calendar guide's readonly
scope examples do not authorize event changes. Preserve the client security
checks; if metadata discovery or token renewal fails, report the specific
provider/client incompatibility before enabling unattended use.

## Agent Studio discovery compatibility

Google's public protected-resource documents, for example
[Gmail metadata](https://gmailmcp.googleapis.com/.well-known/oauth-protected-resource/mcp/v1),
advertise the authorization server as `https://accounts.google.com/`. Its
[authorization-server metadata](https://accounts.google.com/.well-known/oauth-authorization-server)
declares `issuer` as `https://accounts.google.com`, without the trailing slash.

The companion Agent Studio client's
`src/infrastructure/mcp/oauthMetadata.ts` requires an exact issuer match, so these
documents fail its discovery validation. The
[OpenID fallback](https://accounts.google.com/.well-known/openid-configuration)
declares the same issuer without the slash. Public protocol and tool catalog
checks still work and do not establish OAuth compatibility.

Account connection requires compatible provider metadata or a reviewed client
change. Do not bypass issuer validation, copy a token into the bundled manifest,
or report the account connected to get past this failure. Verify the installed
client version and discovery before continuing with Connect and authenticated
reads. Slack has a separate resource-identifier mismatch described in its
[connection notes](../../plugins/workspace/org.opspresso.agent-studio/mcp/slack.md).

## Verify the installed connection

Use an authorized, representative read after connection:

| Server | Read check |
|---|---|
| Gmail | Narrow thread search, then read one selected thread |
| Drive | Find a known file, then read its metadata and content |
| Calendar | List calendars, then query a bounded interval in the intended timezone |
| Docs | Read one known document's structure and text |
| Sheets | Read spreadsheet metadata and a small known range |
| Slides | Read one known presentation's structure and content |

Inspect discovered schemas rather than assuming tool names from another server.
Google can answer public protocol or catalog requests before account access is
established; successful `initialize` or `tools/list` is insufficient validation.
Record authorization failures, unavailable services and partial results separately
from a successful empty query. Do not create drafts, send invitations or edit
documents as a connection test.

Google IDs and links are external source references. They are not Studio artifact
IDs, and native edits do not automatically create downloadable Office files.
Use the actual runtime's import/export capability when file delivery is requested.

## When preview access is unavailable

Keep these account connections unbound and report the access requirement. If the
installation chooses a community server, assess its tools and OAuth boundary and
register its own reachable Streamable HTTP endpoint separately under a distinct
name, following [sync ownership](../agent-studio.md#registration-and-sync-ownership).
Do not replace a bundled Google URL with an installation-specific address.
