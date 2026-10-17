# Agent Memory connection

Register the installation's exact MCP URL (normally `/api/mcp`) separately from
Plugin sync. Agent Memory owns long-term memories and short-term task handoffs.
Documents, RAG passages, source-grounded knowledge and recordings belong to
[Agent Librio](agent-librio.md).

## Identity and access

Personal coding clients use revocable personal credentials. Studio delegates the
current caller with a short-lived signed token for the exact configured service
URL and `aud=agent-memory`. The service validates the trusted issuer, subject,
organization, scope and expiry, resolves an explicit issuer/subject binding to a
local user, and checks current membership. Matching local UUIDs are not a binding.

`X-User-Email`, display email, tenant headers and caller-supplied owner fields do
not grant user access. Do not copy a shared service token into a client or use an
email header to impersonate another member. Credentials and delegation keys stay
in installation secret configuration, never skills, prompts or task inputs.

## Tools

| Discovered tool | Purpose |
|---|---|
| `recall` | Ranked long-term memories: compact text plus ID, version, content, source and scope; no document or graph search |
| `remember` | Durable scoped memory with provenance; keep an explicit idempotency key on retries |
| `forget` | Archive the observed memory version with manage permission |
| `handoff_create` | Save goal, summary, next actions, blockers and references with an idempotency key |
| `handoff_list`, `handoff_get` | Find active tasks and inspect full context before resuming |
| `handoff_update`, `handoff_close` | Change progress or close using the observed `expectedVersion` |
| `memory_delete`, `handoff_delete` | Permanently erase memories or a handoff with all history. Offered only to credentials that hold `memory:delete` or `handoff:delete` |

Permanent deletion is a separate grant. Studio delegation and organization tokens
never hold the delete scopes, so Studio Agents do not see the delete tools. A
personal client token holds them only when the user enables permanent deletion
when the token is issued. Call a delete tool only on an explicit
permanent-deletion request; use `forget` or `handoff_close` otherwise.

The actual discovered schema is authoritative. Handoff references identify a
project, branch, task or native session; they do not contain a resumable CLI
process, provider transcript, credential or file checkpoint. Those remain in
Forge. Closed or expired handoffs are not active work and cannot be reopened by
editing their version.

## Studio setup

1. Register the exact service connection and complete the local identity binding.
2. Bind the server and only the needed tools to the intended Agent.
3. Verify an actual caller-scoped read; tool discovery alone does not prove access.
4. For automatic pre-run recall, enable `memoryRecall` and explicitly bind `recall`.

Dynamic discovery alone does not enable automatic recall. A blocked or
approval-gated recall is not silently executed before a run. Choosing user, team
or organization scope must follow the requested sharing scope and current server
permissions. A denied personal write must not be retried as an organization write.

Console description example:

```text
현재 인증된 사용자에게 허용된 장기 기억과 단기 작업 인수인계를 조회·관리합니다. 결정·선호·경험은 recall/remember로, 진행 중 작업은 handoff 도구로 다룹니다. 문서·RAG·지식 그래프 검색은 Agent Librio에서 수행합니다.
```
