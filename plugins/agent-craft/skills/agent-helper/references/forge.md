# Agent Forge

코딩 Workspace·Run·Workspace profile·Git 연결·보호된 Git 작업 승인을 다루거나 Forge 콘솔을 안내할 때 읽는다.
실제 작업 실행 절차는 `workspace-task` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **Workspace**: 격리된 Sandbox와 파일 checkpoint를 가진 지속형 작업 공간. 상태는 `active`·`suspended`·`closed`다.
  runtime(`command`·`codex`·`claude`·`opencode`)은 생성 후 바꿀 수 없다. 한 Workspace는 한 번에 Run 하나를 실행한다.
- **유휴 시간**(`idleTtlSeconds`, 기본 1800초): 이 시간 동안 쓰지 않으면 `suspended`가 된다. 다음 `run_submit`이
  다시 시작하고 checkpoint를 복원한다. 유휴 시간은 Workspace 생성 때 정해지므로 profile을 바꿔도 기존 Workspace에는 적용되지 않는다.
- **Run**: 명령·native 코딩 작업·Git 단계. 상태는 `queued`·`running`·`succeeded`·`failed`·`cancelled`·`interrupted`다.
  `interrupted`는 외부 효과가 불확실하다는 뜻이며 자동으로 다시 실행하지 않는다. 기본 제한 시간 10분, 최대 1시간이다.
- **Workspace profile**: runtime·모델·검사(test/lint/build)·유휴 시간·허용 저장소 규칙(`repositoryMode`: `selected`·`owners`·`all`·`new`)을
  저장한 사용자 설정. revision이 있으며 생성·제출 때 `profileId`와 `profileRevision`을 함께 보낸다. 기본 profile은 자동 적용되지 않는다.
- **Git 단계**: `prepare`(연결 ID·base branch·작업 branch)·`review`·`commit`·`push`(`agent/` branch만)·`pull-request`는 요청 범위에서 실행한다.
  `publish-protected`·`merge`·`tag`·`release`·`deploy`는 **보호된 작업**이며 Workspace 소유자가 Forge 콘솔에서 승인해야 한다.

## Helper가 쓸 수 있는 도구

| 영역 | 도구 | 주의 |
|---|---|---|
| 조회 | `profile_list`, `profile_get`, `profile_models`, `model_channels`, `workspace_list`, `workspace_get`, `run_list`, `run_get`, `run_result`, `run_events`, `run_usage`, `git_connections`, `git_approval_get`, `repository_get` | 읽기 전용 |
| 응답 유실 복구 | `workspace_lookup_request`, `run_lookup_request`, `repository_lookup_request`, `workspace_deletion` | 같은 `requestKey`로 조회한다. 삭제 결과는 `workspace_deletion`으로 확인한다 |
| profile | `profile_save`, `profile_select` | 저장은 revision 비교로 충돌을 거절한다 |
| Workspace | `workspace_create`, `workspace_suspend`, `workspace_resume`, `workspace_close`, `workspace_delete` | 닫기·삭제는 되돌릴 수 없다. 삭제는 닫은 뒤 `expectedRevision`과 함께 한다 |
| 실행 | `run_submit`, `run_cancel`, `run_retry` | `run_submit`은 접수다. 결과는 원래 Chat으로 돌아온다. `run_retry`는 사용자가 명시적으로 요청할 때만 |
| 저장소 | `repository_create` | 접수형 작업. 결과가 `unknown`이면 다시 만들지 않는다 |

승인 도구는 MCP에 없다. Git 연결(`git:connect`)도 위임되지 않는다.

## 콘솔 페이지 (`agent-forge`)

| 경로 | 용도 |
|---|---|
| `/` | Workspace 목록·상태·Run, Workspace 생성과 작업 시작. `/?workspace=<id>&run=<id>`로 특정 Run을 연다 |
| `/settings` | Workspace profile과 기본 profile. `/settings?profile=<id>` |
| `/git` | GitHub 계정 연결·저장소 등록, 보호된 Git 작업 승인. `/git?approval=<id>` |
| `/profile` | 계정 정보 |

Forge 콘솔은 페이지마다 전체 문서를 새로 불러온다.

콘솔 전용 작업: GitHub 계정 연결·해제, 저장소 등록, 보호된 Git 작업 승인·거절(원래 소유자의 콘솔 세션만 가능).

## 처음 설정

1. Forge 콘솔에 Studio 계정으로 로그인한다(`open_console(service="agent-forge", path="/")`).
2. `/git`에서 GitHub를 연결하고 작업할 `owner/repo`를 등록한다. Studio의 GitHub 연결은 옮겨지지 않는다.
3. `/settings`에서 profile을 만들고 기본으로 선택한다. 새 저장소를 만들 계획이면 `repositoryMode`를 `new`로 하거나 허용 저장소를 지정한다.
   `selected` 모드에 저장소 목록이 비어 있으면 `repository_create`는 성공할 수 없다.
4. Studio에서 작업할 Agent의 `mcpList`에 `agent-forge`를 연결한다. [journeys](journeys.md#코딩-agent-준비)

## 오류

| 코드·증상 | 원인과 해결 |
|---|---|
| `git_connection_required`, `profile_repository_forbidden` (403) | `/git`에서 GitHub 연결·저장소 등록을 하고 profile의 저장소 규칙을 확인한다 |
| `git_approval_invalid` (403), 승인 만료 | 승인은 Run 생성 시각 + `timeoutMs`에 만료된다. 만료 후에는 콘솔에 대기로 보일 수 있어도 승인되지 않는다. 더 긴 `timeoutMs`로 새 Run을 제출하고 `/git?approval=<id>`에서 바로 승인하게 안내한다 |
| `profile_revision_conflict` (409) | profile을 다시 읽는다 |
| `profile_required`, `profile_input_conflict` (400) | `profileId`·`profileRevision`을 함께 보낸다 |
| `profile_runtime_mismatch` (409) | runtime이 다르다. 새 Workspace를 만든다 |
| `profile_model_unavailable` | profile에 활성 모델을 다시 고른다 |
| `timeout_exceeds_authorization` (400) | `timeoutMs`를 줄인다 |
| `work_authorization_invalid` | 다시 로그인하고 새 `requestKey`로 제출한다 |
| `reauthorization_required` (403, Run `errorCode`) | 이전 위임으로 접수된 작업은 계속할 수 없다. 사용자가 새 Run을 제출한다 |
| `model_gateway_unavailable` (503) | 운영 문제다. 무조건 다시 제출하지 않는다 |
| `delivery_variables_invalid` | dev Variable 이름이 Sandbox 예약 이름(예: `OPENAI_*`)과 겹친다. Delivery에서 이름을 바꾼다 |
| Run `succeeded`인데 `outputLoss=true` | 출력 일부가 영구 손실됐다. 결과 전체를 추정하지 않고 남은 검증 근거를 확인한다 |
