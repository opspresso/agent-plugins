---
description: >
  Find Google Drive files, read content and inspect metadata or permissions;
  create or copy files when requested and supported. Requires the project's
  connected Google account and Workspace MCP Developer Preview access. A Drive
  file ID is not an Agent Studio artifact ID; inaccessible files need supplied content.
---

# google-drive

Use the [Google Workspace setup](../../../../docs/integrations/google-workspace.md)
for the provider-hosted endpoint and account connection. Verify search and a
selected file read under the intended account, including Shared Drive access
when the installation needs it.

The [Drive MCP reference](https://developers.google.com/workspace/drive/api/reference/mcp)
describes file search, content, metadata, permissions, creation and copying.
Permission inspection does not imply permission editing. Native Docs, Sheets
and Slides have their own MCP servers for structured operations.

A returned file ID, download URL or resource URI does not establish an Agent
Studio artifact. Verify the actual file delivery path before offering a download
or passing content to the builtin `File` tool.
