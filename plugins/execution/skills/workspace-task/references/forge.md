# Forge 도구

연결된 Agent Forge MCP의 현재 schema가 기준이다. 도구는 호출자 scope가 허용할 때만 목록에 나온다.
조직·owner·email·token을 인수로 만들지 않는다. 오류는 `{error, code, status, outcome}`로 반환된다.

## 도구 목록

| 단계 | 도구 | 주요 입력 |
|---|---|---|
| profile | `profile_list`, `profile_get`, `profile_models` | `profileId` |
| 모델 채널 | `model_channels` | 없음 |
| Workspace 조회 | `workspace_list`, `workspace_get` | `workspaceId` |
| Workspace 생성 | `workspace_create` | `title`, `profileId`+`profileRevision` 또는 `runtime`·`modelChannel`·`idleTtlSeconds`, `requestKey` |
| 실행 접수 | `run_submit` | `workspaceId`, `input`, 선택 `timeoutMs`·`checks`, profile Workspace는 `profileId`+`profileRevision`, `requestKey` |
| 실행 관측 | `run_get`, `run_events`, `run_result`, `run_list`, `run_usage` | `runId` 또는 `workspaceId` |
| 접수 확인 | `workspace_lookup_request`, `run_lookup_request` | 원래 `requestKey` |
| 중지·재시도 | `run_cancel`, `run_retry` | `runId`, 재시도는 `requestKey`와 현재 `profileRevision` |
| 수명 관리 | `workspace_suspend`, `workspace_resume`, `workspace_close` | `workspaceId` |
| Git 연결·승인 조회 | `git_connections`, `git_approval_get` | `approvalId` |
| 저장소 생성 | `repository_create`, `repository_get`, `repository_lookup_request` | 아래 참조 |

`profile_save`·`profile_select`는 사용자가 profile 저장·선택을 명시적으로 요청한 경우에만 쓴다.
`workspace_delete`는 영구 삭제 요청에만 쓴다. closed Workspace와 관측한 `expectedRevision`이 필요하다.

## 입력 형태

```json
{"tool":"workspace_create","arguments":{"title":"주문 API 상태 필터","profileId":"<profile id>","profileRevision":3,"requestKey":"<고정 키>"}}
```

```json
{"tool":"run_submit","arguments":{"workspaceId":"<workspace id>","input":{"kind":"task","prompt":"<완결된 작업 지시>"},"profileId":"<profile id>","profileRevision":3,"requestKey":"<고정 키>"}}
```

- `input`은 `{kind:"command", script}`, `{kind:"task", prompt}`, `{kind:"git", action, ...}` 중 하나다.
  command Workspace에는 셸 스크립트만, native Workspace에는 코딩 지시만 보낸다. Git 실행은 어느 Runtime에서도 가능하다.
- profile Workspace의 실행은 `profileId`·`profileRevision`을 매번 보낸다. profile과 `checks` override, 또는
  profile과 `runtime`·`modelChannel`·`idleTtlSeconds`를 함께 보내지 않는다.
- `timeoutMs`는 대기·준비·실행·검사 전체 시간이다. 기본 10분, 최대 1시간이다.
- 명시적 Workspace의 `checks`는 `{name:"test"|"lint"|"build", command}` 최대 3개다.

## requestKey와 응답 유실

- `requestKey`는 HTTP `Idempotency-Key`와 같다. 같은 키와 같은 입력은 원래 결과를 반환한다. 입력을 바꾸면 409다.
- Studio Chat 실행은 `run_submit`·`run_retry`·`repository_create`의 `requestKey`를 도구 호출마다 고정한 값으로 바꿔 보낸다.
  응답의 `work.requestKey`가 실제 키다. `workspace_create`의 키는 모델이 정하고 재전송에서 유지한다.
- 응답을 잃거나 통신 오류·408·429·5xx를 받으면 결과를 `unknown`으로 본다. 원래 키로 `*_lookup_request`를 조회한다.
  `null`은 접수 기록을 찾지 못했다는 뜻이고 통신 오류는 부재의 증거가 아니다.
- `outcome:"rejected"`는 그 호출의 명확한 거절이며 이전 접수의 부재 증거는 아니다.

## 작업 참조와 결과

`run_submit`·`run_retry` 응답의 `work`는 `id`, `workspaceId`, `requestKey`, `status`, `terminal`과
`observe`(`run_get`), `events`(`run_events`), `result`(`run_result`), `cancel`(`run_cancel`) 호출을 담는다.
보호 작업에는 `approval.id`와 `git_approval_get` 호출도 있다. 참조와 URL은 권한이 아니다.

Run 상태는 `queued`, `running`, `succeeded`, `failed`, `cancelled`, `interrupted`다.
`run_result`는 terminal 상태에서만 읽을 수 있다. `exitCode`, `error`, `checks`, `diff`, `gitResult`, `lastEventSeq`, `outputLoss`를 반환한다.
`run_events`는 `after` cursor로 읽고 `nextCursor`·`hasMore`를 따른다. 페이지 재조회는 작업을 다시 실행하지 않는다.

## 주요 오류

| code | 행동 |
|---|---|
| `profile_revision_conflict` | `profile_get`으로 현재 revision을 다시 읽는다 |
| `profile_required`, `profile_input_conflict` | profile 쌍을 함께 보내거나 충돌 입력을 뺀다 |
| `profile_runtime_mismatch` | 기존 Workspace의 Runtime·profile을 유지하거나 새 Workspace를 만든다 |
| `profile_repository_forbidden`, `git_connection_required` | profile의 저장소 규칙과 Forge 콘솔의 Git 연결을 확인하도록 안내한다 |
| `timeout_exceeds_authorization` | 오류의 만료 시각 전에 끝나도록 `timeoutMs`를 줄인다 |
| `work_authorization_invalid` | 접수 권한이 만료·철회됐다. 사용자가 다시 로그인한 뒤 새 요청으로 제출한다 |
| `model_gateway_unavailable` | 운영자 설정 문제다. 새 키로 반복하지 않는다 |
