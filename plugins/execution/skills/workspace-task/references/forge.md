# Forge 도구

연결된 Agent Forge MCP의 현재 schema가 기준이다. 도구는 호출자 scope가 허용할 때만 목록에 나온다.
조직·owner·email·token을 인수로 만들지 않는다. 오류는 `{error, code, status, outcome}`로 반환된다.
일시 장애에는 `retryAfterSeconds`가, `git_connection_required`에는 `connectUrl`이 함께 올 수 있다.

## 도구 목록

| 단계 | 도구 | 주요 입력 |
|---|---|---|
| profile | `profile_list`, `profile_get`, `profile_models` | `profileId` |
| profile 삭제 | `profile_delete` | `profileId`, `expectedRevision` |
| 모델 채널 | `model_channels` | 없음 |
| Workspace 조회 | `workspace_list`, `workspace_get` | `workspaceId` |
| Workspace 생성 | `workspace_create` | `title`, `profileId`+`profileRevision` 또는 `runtime`·`modelChannel`·`idleTtlSeconds`, `requestKey` |
| 실행 접수 | `run_submit` | `workspaceId`, `input`, 선택 `timeoutMs`·`checks`, profile Workspace는 `profileId`+`profileRevision`, `requestKey` |
| 실행 관측 | `run_get`, `run_events`, `run_result`, `run_list`, `run_usage` | `runId` 또는 `workspaceId` |
| 접수 확인 | `workspace_lookup_request`, `run_lookup_request` | 원래 `requestKey` |
| 중지·재시도 | `run_cancel`, `run_retry` | `runId`, 재시도는 `requestKey`와 현재 `profileRevision` |
| 수명 관리 | `workspace_suspend`, `workspace_resume`, `workspace_close` | `workspaceId` |
| Git 호스트 연결 상태 | `git_connections` | 없음 |
| 보호 작업 승인 조회 | `git_approval_get` | `approvalId` |
| 저장소 생성(GitHub) | `repository_create` | `origin`, `profileId`+`profileRevision`, `repository`, 선택 `description`, `private`, `requestKey` |
| 저장소 생성 확인 | `repository_get`, `repository_lookup_request` | `creationId` 또는 원래 `requestKey` |

저장소를 등록하거나 Git 호스트 계정을 연결하는 도구는 없다.

`profile_save`·`profile_select`는 사용자가 profile 저장·선택을 명시적으로 요청한 경우에만 쓴다.
`profile_delete`는 사용자가 profile의 영구 삭제를 명시적으로 요청한 경우에만 쓴다. 소유자만 삭제할 수 있고 되돌릴 수 없다.
삭제하면 그 profile을 기본으로 선택한 사용자의 선택이 해제된다. 닫은 Workspace와 끝난 Run은 수락한 설정을 유지한다.
응답을 잃으면 `profile_get`을 읽는다. `profile_not_found`이면 삭제된 것이다.
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

## Git 호스트와 연결 상태

`git_connections`는 `{hosts}`를 반환한다. 저장소 목록은 없다. 어느 Forge 도구도 계정 ID나 연결 ID를 입력으로 받지 않는다.

| 필드 | 뜻 |
|---|---|
| `hosts[].origin` | Git 호스트 주소(`https://<host>`). Git `prepare`와 `repository_create`의 `origin`으로 그대로 쓴다 |
| `hosts[].provider` | `github` 또는 `gitlab` |
| `hosts[].status` | `connected`, `not_connected`, `reconnect_required` |
| `hosts[].account` | `connected`일 때만 있다. 연결된 계정의 `id`와 `login`이다 |
| `hosts[].connectUrl` | 사용자가 그 호스트를 연결·재연결하는 Agent Studio 주소 |

- 사용자는 Git 호스트를 Agent Studio의 프로필 → Git 계정에서 한 번 연결한다. Forge 콘솔과 MCP에는 계정 연결 기능이 없다.
- `status`가 `connected`가 아니면 그 host의 `connectUrl`을 사용자에게 준다. 사용자가 연결한 뒤 이어간다.
- `hosts`가 `null`이면 이 호출로는 호스트를 알 수 없다는 뜻이다. 호스트가 없다고 판단하지 않는다.
  사용자가 지정한 저장소의 호스트 주소(`https://<host>`)를 `origin`으로 보내면 Forge가 접수할 때 판정한다.
- 저장소 접근은 Git 호스트가 판정한다. 연결된 계정이 읽을 수 있는 저장소는 `prepare`할 수 있고, 쓸 수 있는 저장소에 커밋·게시할 수 있다.
  profile의 저장소 규칙(`repositoryMode`)이 그 범위를 더 좁힐 수 있다. 새 profile의 기본값 `all`은 좁히지 않는다.
- `prepare`가 성공하면 Workspace가 저장소 신원(Git 호스트, 연결 계정, 저장소 ID, 공개 범위)을 보관한다.
  Forge는 이후 Git 단계마다 현재 연결 계정과 저장소를 이 신원과 비교한다.

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
| `profile_in_use` | 삭제하려는 profile을 닫지 않은 Workspace나 끝나지 않은 Run이 쓴다. `error`가 본인 Workspace 수, 다른 사용자의 Workspace 수, 끝나지 않은 Run 수를 알린다. 사용자가 요청하면 본인 Workspace를 `workspace_close`로 닫고, Run이 끝난 뒤 다시 삭제한다. 다른 사용자의 Workspace가 쓰면 소유자가 먼저 profile을 `scope:user`로 저장해야 한다고 알린다 |
| `profile_required`, `profile_input_conflict` | profile 쌍을 함께 보내거나 충돌 입력을 뺀다 |
| `profile_runtime_mismatch` | 기존 Workspace의 Runtime·profile을 유지하거나 새 Workspace를 만든다 |
| `profile_repository_forbidden` | profile의 저장소 규칙이 그 저장소를 허용하지 않는다. profile 소유자가 Forge 콘솔 설정에서 규칙을 바꿔야 한다고 안내한다 |
| `timeout_exceeds_authorization` | 오류의 만료 시각 전에 끝나도록 `timeoutMs`를 줄인다 |
| `work_authorization_invalid` | 접수 권한이 만료·철회됐다. 사용자가 다시 로그인한 뒤 새 요청으로 제출한다 |
| `model_gateway_unavailable` | 운영자 설정 문제다. 새 키로 반복하지 않는다 |

## Git 오류

`run_submit`의 거절(도구 오류의 `code`)이나 끝난 Run의 `errorCode`로 온다. `prepare`는 접수할 때 호스트 연결과 저장소를
확인하므로 `git_connection_required`·`git_repository_not_found`·`invalid_repository`가 `run_submit`의 거절로 온다.
어느 경우에도 GitHub MCP 쓰기·다른 계정·native Git으로 대신하지 않는다.

| code | 뜻 | 행동 |
|---|---|---|
| `git_connection_required` | 사용자가 그 Git 호스트를 Agent Studio에서 연결하지 않았거나 다시 연결해야 한다 | 오류나 Run의 `connectUrl`을 사용자에게 준다. 없으면 `git_connections`의 그 host `connectUrl`을 준다. 사용자가 연결한 뒤 새 요청으로 다시 제출한다 |
| `git_repository_not_found` | 저장소가 없거나, 이름이 바뀌었거나, 연결된 계정이 볼 수 없다 | 계정은 연결돼 있다. 다시 연결하라고 하지 않는다. 저장소 이름과 그 계정의 저장소 권한을 사용자와 확인한다. Workspace 저장소의 이름이 바뀌었으면 새 Workspace에서 새 이름으로 `prepare`한다 |
| `invalid_repository` | `origin`이 이 설치의 Git 호스트가 아니거나 저장소 경로 형식이 틀렸다. GitHub는 `owner/repo` 두 마디, GitLab은 두 마디 이상의 프로젝트 경로만 받는다. Forge는 Git 호스트 연결을 확인하기 전에 이 형식을 검사한다 | `git_connections`의 host `origin`과 경로를 확인해 고친다. 연결을 다시 하라고 하지 않는다 |
| `workspace_repository_attached` | 저장소가 있는 Workspace에 `prepare`를 보냈다 | 그 Workspace의 브랜치에서 이어간다. 다른 저장소·브랜치의 작업이면 새 Workspace를 만든다 |
| `git_account_changed` | Studio에 연결된 Git 계정이 이 Workspace를 `prepare`한 계정과 다르다 | 사용자에게 알린다. 사용자가 원래 계정을 Studio에서 다시 연결하면 같은 Workspace에서 이어가고, 현재 계정으로 작업하려면 새 Workspace에서 `prepare`한다 |
| `repository_identity_changed` | Workspace 저장소의 이름이 가리키는 저장소 ID·공개 범위·주소가 바뀌었다 | 사용자와 대상 저장소를 확인한 뒤 새 Workspace에서 `prepare`한다 |
| `git_host_removed` | 운영자가 Workspace 저장소의 Git 호스트를 설치에서 제거했다 | 현재 Git 호스트의 저장소로 새 Workspace에서 `prepare`한다 |
| `git_fetch_failed` | Forge가 저장소를 받지 못했다(권한·없는 브랜치·네트워크) | `error`의 원인을 고친 뒤 새 요청으로 다시 제출한다 |
| `git_action_unsupported` | 이 Workspace에서 실행할 수 없는 Git 단계다. `sourceRevision`으로 준비한 Workspace의 `review` 밖의 모든 단계, 기준 브랜치가 저장소의 기본 브랜치가 아닌 Workspace의 `merge`, `ref`가 기본 브랜치가 아닌 `deploy`, GitLab 저장소의 `release`·`deploy`다. `error`가 이유를 알린다 | 접수할 때 거절되며 승인과 Run은 만들어지지 않았다. 다시 제출하지 않는다. 읽기 전용 Workspace이면 `sourceRevision` 없이 새 Workspace에서 `prepare`한다. `merge`이면 사용자가 Git 호스트에서 그 PR을 병합해야 한다고 알린다. 실행 직전에 기본 브랜치가 바뀐 `merge`는 Run의 `errorCode`로 온다 |
| `sandbox_outdated` | Workspace의 Sandbox가 이전 Forge 이미지로 시작돼, Forge가 승인에 기록할 커밋된 변경을 읽을 수 없다 | Git `review`를 한 번 실행한 뒤 그 결과의 `headSha`·`fingerprint`로 보호 작업을 다시 제출한다 |
| `github_unavailable`, `gitlab_unavailable` | Git 호스트의 일시 장애나 요청 수 제한 | `retryAfterSeconds` 뒤에 원래 키의 결과를 조회하거나 같은 요청을 다시 보낸다 |
