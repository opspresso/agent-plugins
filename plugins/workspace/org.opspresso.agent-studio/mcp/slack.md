---
description: >
  Search accessible Slack messages and files and read channels or threads through
  the project's connected Slack account. Send messages or change workspace content
  only when explicitly requested and supported. Access requires an eligible Slack
  app and granted scopes; missing private-channel access is not an empty result.
---

# slack

The [official Slack MCP server](https://docs.slack.dev/ai/slack-mcp-server/)
provides Streamable HTTP at the bundled URL. Slack restricts MCP access to
Marketplace-published or internal apps; an unlisted app is not eligible.

Before connecting, verify Agent Studio discovery compatibility. Slack's 401 at
`/mcp` points to its
[protected-resource metadata](https://mcp.slack.com/.well-known/oauth-protected-resource),
which identifies the resource as `https://mcp.slack.com`. The current companion
client's `src/infrastructure/mcp/oauthMetadata.ts` requires challenged metadata
to identify the exact endpoint `https://mcp.slack.com/mcp`, so discovery rejects
this document. A compatible provider/client update is needed; do not bypass
resource validation or substitute an undocumented endpoint.

After discovery is compatible, configure the installation's registered
Slack app client ID and secret in the project's connection. Register the actual
Agent Studio callback URL with that app. Use the supported user-token OAuth flow
and the scopes needed for the selected tools; do not reuse another client's app
identity or add credentials to the manifest.

Workspace app approval and any configured IP restrictions also apply. Verify a
bounded search and a selected thread read in the intended workspace. Tool
discovery alone does not verify private-channel or DM access. No message sending
is needed to test a read connection.
