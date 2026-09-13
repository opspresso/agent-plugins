---
description: >
  Search and read Gmail threads and messages, inspect labels and create drafts or
  change labels when requested. Requires the project's connected Google account
  and Workspace MCP Developer Preview access. Draft creation does not send email;
  use supplied text if mailbox access is unavailable.
---

# gmail

Google hosts this endpoint. Follow the shared
[Google Workspace setup](../../../../docs/integrations/google-workspace.md)
before connecting the project's account.

Use the [Gmail MCP reference](https://developers.google.com/workspace/gmail/api/reference/mcp)
and discovered schemas to choose tools. The documented toolset includes thread
search, message/thread reads, drafts and label operations; it does not list a
send-email tool. Do not infer sending support from an OAuth scope.

Verify with a narrow thread search and a read of a selected result. A successful
`initialize` or `tools/list` response does not prove mailbox authorization.
Keep label changes and draft creation out of a read-only connection check.
