# Agent Forge

코딩 Workspace·Run·Workspace profile·Git 호스트 연결 상태·보호된 Git 작업 승인을 다루거나 Forge 콘솔을 안내할 때 읽는다.
실제 작업 실행 절차는 `workspace-task` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **Workspace**: 격리된 Sandbox와 파일 checkpoint를 가진 지속형 작업 공간. 상태는 `active`·`suspended`·`closed`다.
  runtime(`command`·`codex`·`claude`·`opencode`)은 생성 후 바꿀 수 없다. 한 Workspace는 한 번에 Run 하나를 실행한다.
- **유휴 시간**(`idleTtlSeconds`, 기본 1800초): 이 시간 동안 쓰지 않으면 `suspended`가 된다. 다음 `run_submit`이
  다시 시작하고 checkpoint를 복원한다. 유휴 시간은 Workspace 생성 때 정해지므로 profile을 바꿔도 기존 Workspace에는 적용되지 않는다.
- **Run**: 명령·native 코딩 작업·Git 단계. 상태는 `queued`·`running`·`succeeded`·`failed`·`cancelled`·`interrupted`다.
  `interrupted`는 외부 효과가 불확실하다는 뜻이며 자동으로 다시 실행하지 않는다. 기본 제한 시간 10분, 최대 1시간이다.
- **Workspace profile**: runtime·모델·검사(test/lint/build)·유휴 시간·허용 저장소 규칙(`repositoryMode`: `all`·`selected`·`owners`·`new`)을
  저장한 사용자 설정. revision이 있으며 생성·제출 때 `profileId`와 `profileRevision`을 함께 보낸다. 기본 profile은 자동 적용되지 않는다.
  새 profile의 `repositoryMode` 기본값은 `all`이며 연결한 Git 계정이 접근할 수 있는 모든 저장소를 허용한다. 나머지 값은 profile의 목록으로 저장소를 제한한다.
- **Git 호스트 연결**: 사용자가 Agent Studio의 프로필 → Git 계정(`/profile/git`)에서 Git 호스트(GitHub·GitLab)마다 한 번 연결한다.
  Forge는 Git credential과 저장소 목록을 갖지 않으며, 저장소를 Forge에 등록하지 않는다. `git_connections`는 host마다
  `origin`·`status`(`connected`·`not_connected`·`reconnect_required`)·`account`·`connectUrl`을 준다. `connectUrl`이 사용자가 연결하는 Studio 주소다.
- **Git 단계**: `prepare`(Git 호스트 `origin`·저장소 경로 `repository`·작업 branch, 선택 base branch)·`review`·`commit`·`push`(`agent/` branch만)·`pull-request`는 요청 범위에서 실행한다.
  `prepare`의 base branch(`baseBranch`)를 생략하면 저장소의 기본 branch에서 시작한다. 결과의 `gitResult.baseBranch`가 실제로 쓴 branch다.
  연결한 계정이 Git 호스트에서 읽을 수 있는 저장소는 `prepare`하고, 쓸 수 있는 저장소에 커밋·게시한다.
  `publish-protected`·`merge`·`tag`·`release`·`deploy`는 **보호된 작업**이며 Workspace 소유자가 Forge 콘솔에서 승인해야 한다.
  `merge`는 base branch가 `main`인 Workspace에서만 된다.

## Helper가 쓸 수 있는 도구

| 영역 | 도구 | 주의 |
|---|---|---|
| 조회 | `profile_list`, `profile_get`, `profile_models`, `model_channels`, `workspace_list`, `workspace_get`, `run_list`, `run_get`, `run_result`, `run_events`, `run_usage`, `git_connections`, `git_approval_get`, `repository_get` | 읽기 전용 |
| 응답 유실 복구 | `workspace_lookup_request`, `run_lookup_request`, `repository_lookup_request`, `workspace_deletion` | 같은 `requestKey`로 조회한다. 삭제 결과는 `workspace_deletion`으로 확인한다 |
| profile | `profile_save`, `profile_select` | 저장은 revision 비교로 충돌을 거절한다 |
| Workspace | `workspace_create`, `workspace_suspend`, `workspace_resume`, `workspace_close`, `workspace_delete` | 닫기·삭제는 되돌릴 수 없다. 삭제는 닫은 뒤 `expectedRevision`과 함께 한다 |
| 실행 | `run_submit`, `run_cancel`, `run_retry` | `run_submit`은 접수다. 결과는 원래 Chat으로 돌아온다. `run_retry`는 사용자가 명시적으로 요청할 때만 |
| 저장소 | `repository_create` | 접수형 작업. GitHub 저장소만 만든다(`origin`은 `https://github.com`). 결과가 `unknown`이면 다시 만들지 않는다 |

승인 도구는 MCP에 없다. Git 호스트 계정을 연결하거나 저장소를 등록하는 도구도 없다.

## 콘솔 페이지 (`agent-forge`)

| 경로 | 용도 |
|---|---|
| `/` | Workspace 목록·상태·Run, Workspace 생성과 작업 시작. `/?workspace=<id>&run=<id>`로 특정 Run을 연다 |
| `/settings` | Workspace profile과 기본 profile. `/settings?profile=<id>` |
| `/git` | 보호된 Git 작업 승인(`/git?approval=<id>`), Git 호스트와 연결 상태(`/git?tab=hosts`), 저장소 생성 기록(`/git?tab=creations`) |
| `/profile` | 계정 정보 |

Forge 콘솔은 페이지마다 전체 문서를 새로 불러온다.

콘솔 전용 작업: 보호된 Git 작업 승인·거절(원래 소유자의 콘솔 세션만 가능).
`publish-protected`·`merge`·`tag`의 승인 화면은 Workspace branch가 커밋한 변경(`prepare` 기준 커밋부터 승인할 HEAD까지의 diff)을 보여 준다.
`merge`의 승인 화면에는 Git 호스트의 PR을 여는 **PR 열기** 링크가 있다. `release`·`deploy`의 승인 화면은 diff 대신 승인 대상을 설명한다.
Git 호스트 계정 연결·해제는 Forge 콘솔에서 하지 않는다. Git 호스트 탭은 연결 상태를 보여 주고 Studio의 연결 주소로 안내한다.

## 처음 설정

1. Forge 콘솔에 Studio 계정으로 로그인한다(`open_console(service="agent-forge", path="/")`).
2. Agent Studio의 프로필 → Git 계정(`/profile/git`)에서 작업할 Git 호스트를 연결한다. `git_connections`에서 그 host의 `status`가
   `connected`인지 확인한다. 저장소는 등록하지 않는다. Tools의 GitHub MCP 연결과는 별개의 연결이다.
3. `/settings`에서 profile을 만들고 기본으로 선택한다. `repositoryMode`의 기본값 `all`은 기존 저장소 작업과 새 저장소 생성을 모두 허용한다.
   저장소를 제한하려면 `selected`·`owners`·`new`를 고르고 허용 저장소를 지정한다.
   `selected` 모드에 저장소 목록이 비어 있으면 `repository_create`는 성공할 수 없다.
4. Studio에서 작업할 Agent의 `mcpList`에 `agent-forge`를 연결한다. [journeys](journeys.md#코딩-agent-준비)

## 오류

| 코드·증상 | 원인과 해결 |
|---|---|
| `git_connection_required` (409, Run `errorCode`) | 사용자가 그 Git 호스트를 Studio에서 연결하지 않았거나 다시 연결해야 한다. 오류나 Run의 `connectUrl`을 링크로 준다. 사용자가 연결한 뒤 다시 제출한다 |
| `git_repository_not_found` (404) | 저장소가 없거나, 이름이 바뀌었거나, 연결한 계정이 볼 수 없다. 다시 연결하게 하지 않는다. 저장소 이름과 그 계정의 권한을 확인한다 |
| `invalid_repository` (400) | `origin`이 이 설치의 Git 호스트가 아니거나 저장소 경로 형식이 틀렸다. `git_connections`의 host `origin`과 경로를 확인한다 |
| `git_account_changed` (403) | Studio에 연결된 Git 계정이 그 Workspace를 `prepare`한 계정과 다르다. 원래 계정을 Studio에서 다시 연결하거나 새 Workspace에서 `prepare`한다 |
| `repository_identity_changed` (403) | Workspace 저장소의 저장소 ID·공개 범위·주소가 바뀌었다. 대상을 확인하고 새 Workspace에서 `prepare`한다 |
| `git_host_removed` (409) | 운영자가 그 Git 호스트를 설치에서 제거했다. 현재 Git 호스트의 저장소로 새 Workspace에서 `prepare`한다 |
| `profile_repository_forbidden` (403) | profile의 저장소 규칙이 그 저장소를 허용하지 않는다. `/settings?profile=<id>`에서 규칙을 확인한다 |
| `git_approval_invalid` (403), 승인 만료 | 승인이 거절·만료됐거나 승인한 대상이 바뀌었다. 승인 기한은 Run 접수 후 50분이다. 보호된 작업의 Run은 요청한 `timeoutMs`와 관계없이 제한 시간이 1시간이므로 `timeoutMs`를 늘려도 기한은 늘지 않는다. 기한이 지나면 승인할 수 없고 Forge가 Run을 취소한다. 사용자가 다시 요청하면 새 Run을 제출하고 `/git?approval=<id>`에서 기한 안에 승인하게 안내한다 |
| `git_action_unsupported` (409) | 그 Workspace에서 실행할 수 없는 보호된 작업이다. base branch가 `main`이 아닌 Workspace의 `merge`, GitLab 저장소의 `release`·`deploy`다. 접수할 때 거절되며 승인과 Run은 만들어지지 않는다. `merge`이면 사용자가 Git 호스트에서 그 PR을 병합한다 |
| `sandbox_outdated` (409) | Workspace의 Sandbox가 이전 Forge 이미지로 시작돼 승인에 기록할 커밋된 변경을 읽을 수 없다. Git `review`를 한 번 실행한 뒤 그 결과의 `headSha`·`fingerprint`로 보호된 작업을 다시 요청한다 |
| `profile_revision_conflict` (409) | profile을 다시 읽는다 |
| `profile_required`, `profile_input_conflict` (400) | `profileId`·`profileRevision`을 함께 보낸다 |
| `profile_runtime_mismatch` (409) | runtime이 다르다. 새 Workspace를 만든다 |
| `profile_model_unavailable` | profile에 활성 모델을 다시 고른다 |
| `timeout_exceeds_authorization` (400) | `timeoutMs`를 줄인다 |
| `work_authorization_invalid` | 다시 로그인하고 새 `requestKey`로 제출한다 |
| `reauthorization_required` (403, Run `errorCode`) | 이전 위임으로 접수된 작업은 계속할 수 없다. 사용자가 새 Run을 제출한다 |
| `model_gateway_unavailable` (503) | 운영 문제다. 무조건 다시 제출하지 않는다 |
| `delivery_variables_invalid` | dev Variable 이름이 Sandbox 예약 이름(예: `OPENAI_*`)과 겹친다. Runway에서 이름을 바꾼다 |
| Run `succeeded`인데 `outputLoss=true` | 출력 일부가 영구 손실됐다. 결과 전체를 추정하지 않고 남은 검증 근거를 확인한다 |
