---
description: >
  Read Google calendars and events, check availability and propose meeting times.
  Create, update, delete or respond to events only when requested and supported
  by the connected account's scopes. Requires Workspace MCP Developer Preview
  access; time proposals do not reserve slots or send invitations.
---

# google-calendar

Follow [Google Workspace setup](../../../../docs/integrations/google-workspace.md).
The [Calendar MCP reference](https://developers.google.com/workspace/calendar/api/v3/reference/mcp)
lists calendar/event reads, time suggestions and event mutations. Confirm the
selected operation's scopes; discovery of a write tool does not grant write access.

Verify with calendar listing and a bounded event query. Confirm the calendar ID,
timezone, all-day interpretation and recurring-instance behavior before binding
event-changing tools to a version. A connection check must not invite attendees.
