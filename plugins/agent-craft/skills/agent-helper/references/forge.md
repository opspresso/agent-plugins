# Agent Forge

코딩 Workspace·Run·Workspace profile·Git 호스트 연결 상태·보호된 Git 작업 승인·개발 데스크톱을 다루거나 Forge 화면을 안내할 때 읽는다.
실제 작업 실행 절차는 `workspace-task` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **Workspace**: 격리된 Sandbox와 파일 checkpoint를 가진 지속형 작업 공간. 상태는 `active`·`suspended`·`closed`다.
  runtime(`command`·`codex`·`claude`·`opencode`)은 생성 후 바꿀 수 없다. 한 Workspace는 한 번에 Run 하나를 실행한다.
- **유휴 시간**(`idleTtlSeconds`, 기본 1800초): 이 시간 동안 쓰지 않으면 `suspended`가 된다. 다음 `run_submit`이
  다시 시작하고 checkpoint를 복원한다. 유휴 시간은 Workspace 생성 때 정해지므로 profile을 바꿔도 기존 Workspace에는 적용되지 않는다.
- **Run**: 명령·native 코딩 작업·Git 단계. 상태는 `queued`·`running`·`succeeded`·`failed`·`cancelled`·`interrupted`다.
  `interrupted`는 외부 효과가 불확실하다는 뜻이며 자동으로 다시 실행하지 않는다. 기본 제한 시간 10분, 최대 1시간이다.
- **Workspace profile**: runtime·모델·검사(test/lint/build)·유휴 시간·허용 저장소 규칙(`repositoryMode`: `all`·`selected`·`owners`·`new`)을
  저장한 설정. revision이 있으며 생성·제출 때 `profileId`와 `profileRevision`을 함께 보낸다. 기본 profile은 자동 적용되지 않는다.
  `profile_list`의 `selection`이 사용자가 이름을 대지 않았을 때 쓸 profile이다. `source`가 `user`이면 사용자의 기본 선택,
  `organization`이면 Studio 관리자가 정한 조직 기본 profile이다.
  새 profile의 `repositoryMode` 기본값은 `all`이며 연결한 Git 계정이 접근할 수 있는 모든 저장소와 그 계정이 만들 수 있는 저장소의 생성을 허용한다.
  나머지 값은 profile의 목록으로 저장소 접근과 생성을 제한한다.
- **조직 profile**(`scope:organization`): 모든 구성원의 Sandbox에서 검사가 실행되므로 Studio 관리자만 AgentOps 화면에서 만들고 바꾼다.
  MCP로 조직 profile을 만들거나 바꾸거나 지우면 `console_required`로 거절되고 오류에 그 화면의 `consoleUrl`이 온다.
- **Git 호스트 연결**: 사용자가 프로필 → Git 계정(`/profile/git`)에서 Git 호스트마다 한 번 연결한다.
  Git 호스트는 GitHub(github.com·GitHub Enterprise Server), GitLab(GitLab.com·self-managed GitLab)과 Gitea다. `provider`가 `github`이고
  `origin`이 `https://github.com`이 아니면 GitHub Enterprise Server다. GitHub·Gitea 저장소 경로는 `owner/repo`(Gitea owner는 사용자 이름이나 조직),
  GitLab은 `group/subgroup/project`처럼 group 경로 전체다.
  Forge는 Git credential과 저장소 목록을 갖지 않으며, 저장소를 Forge에 등록하지 않는다. `git_connections`는 host마다
  `origin`·`status`(`connected`·`not_connected`·`reconnect_required`)·`account`·`connectUrl`을 준다. `connectUrl`이 사용자가 연결하는 주소다.
- **Git 단계**: `prepare`(Git 호스트 `origin`·저장소 경로 `repository`·작업 branch, 선택 base branch)·`review`·`commit`·`push`(`agent/` branch만)·`pull-request`는 요청 범위에서 실행한다.
  `prepare`의 base branch(`baseBranch`)를 생략하면 저장소의 기본 branch에서 시작한다. 결과의 `gitResult.baseBranch`가 실제로 쓴 branch다.
  연결한 계정이 Git 호스트에서 읽을 수 있는 저장소는 `prepare`하고, 쓸 수 있는 저장소에 커밋·게시한다.
  `publish-protected`·`merge`·`tag`·`release`·`deploy`는 **보호된 작업**이며 Workspace 소유자가 승인해야 실행된다. [승인](#보호된-git-작업-승인)
  `merge`는 저장소의 기본 branch로만 병합하므로 base branch가 기본 branch인 Workspace에서만 된다. 기본 branch는 `main`이 아닐 수 있다.
  `deploy`도 기본 branch에서만 workflow를 실행한다. `sourceRevision`으로 준비한 Workspace는 읽기 전용이며 `review` 밖의 Git 단계가 거절된다.
- **승인 상태**: `git_approval_get`의 `status`는 `pending`(결정 대기)·`approved`·`rejected`·`executing`(효과 시작)과,
  Run이 끝난 뒤의 `executed`·`failed`·`interrupted`·`expired`·`cancelled`다.
  결정 전에 Run이 끝나면 승인 요청도 끝난다. 승인 기한 뒤면 `expired`, 그 전이면 `cancelled`이며 대기 목록에 남지 않고 승인할 수 없다.
  승인을 소비한 Run이 끝나면 `executed`(승인한 단계가 실행됨, 결과는 Run의 `gitResult`), `failed`(결과 전에 중지·거절됨),
  `interrupted`(원격 반영 여부를 알 수 없음. 다시 요청하기 전에 Git 호스트를 확인한다)가 된다.
- **개발 데스크톱**: 설치가 켠 경우에만 있는 Windows 데스크톱(Azure Virtual Desktop)이다. 사용자가 풀에서 요청하고,
  풀의 `approval`이 `admin`이면 Studio 관리자가 승인한 뒤 만들어진다(약 15~30분).

## Helper가 쓸 수 있는 도구

| 영역 | 도구 | 주의 |
|---|---|---|
| 조회 | `profile_list`, `profile_get`, `profile_models`, `model_channels`, `workspace_list`, `workspace_get`, `run_list`, `run_get`, `run_result`, `run_events`, `run_usage`, `git_connections`, `git_approval_get`, `repository_get`, `repository_namespaces` | 읽기 전용. `repository_namespaces`(`origin`, 선택 `search`)는 연결한 계정이 그 Git 호스트에서 저장소를 만들 수 있는 namespace를 준다 |
| 응답 유실 복구 | `workspace_lookup_request`, `run_lookup_request`, `repository_lookup_request`, `workspace_deletion` | 같은 `requestKey`로 조회한다. 삭제 결과는 `workspace_deletion`으로 확인한다 |
| profile | `profile_save`, `profile_select`, `profile_delete` | `scope:user` profile만 다룬다. 저장은 revision 비교로 충돌을 거절한다. `profile_select`는 `profileId`와 `profileRevision`을 보내고 `profileId: null`로 기본 선택을 지운다. `profile_delete`(`profileId`, `revision`)는 사용자가 영구 삭제를 요청할 때만 쓴다. 소유자만 삭제하며 되돌릴 수 없다 |
| Workspace | `workspace_create`, `workspace_suspend`, `workspace_resume`, `workspace_close`, `workspace_delete` | 닫기·삭제는 되돌릴 수 없다. `workspace_delete`(`workspaceId`, `revision`)는 닫은 뒤 영구 삭제 요청에만 쓴다 |
| 실행 | `run_submit`, `run_cancel`, `run_retry` | `run_submit`은 접수다. 결과는 원래 Chat으로 돌아온다. `run_retry`는 사용자가 명시적으로 요청할 때만 |
| 저장소 | `repository_create` | 접수형 작업. `origin`(`git_connections`의 host)에 GitHub·Gitea 저장소나 GitLab 프로젝트를 만든다. namespace를 짐작하지 않고, 사용자가 정확히 정하지 않았으면 `repository_namespaces`로 고르게 한다. 결과가 `unknown`이면 다시 만들지 않는다 |
| 데스크톱 | `desktop_pools`, `desktop_list`, `desktop_get`, `desktop_lookup_request`, `desktop_request`, `desktop_start`, `desktop_stop`, `desktop_return` | 설치가 켠 경우에만 있다. `desktop_request`는 같은 `requestKey`를 재사용한다. `desktop_return`은 VM과 데이터를 지우며 되돌릴 수 없다. 사용자가 명시적으로 요청하고 데스크톱 이름을 입력했을 때만 그 이름을 `confirmation`으로 보낸다 |

승인을 결정하는 도구는 모델에게 없다. Chat의 승인 화면 버튼이 쓰는 `git_approval_decide`는 화면 전용이다.
Git 호스트 계정을 연결하거나 저장소를 등록하는 도구도 없다. Forge 결과의 `approvalUrl`·`runUrl`·`profileUrl`·`consoleUrl`은 AgentOps 화면 주소다. 그 값을 그대로 링크로 준다.

## 화면

| 경로 | 용도 |
|---|---|
| `/forge/workspaces` | Workspace 목록·상태(`?q=`, `?status=active`·`suspended`·`closed`). `?create=1`은 새 Workspace 대화 상자를 연다 |
| `/forge/workspaces/<workspaceId>`, `/forge/workspaces/<workspaceId>/runs/<runId>` | Workspace 하나와 그 Run, Run 하나의 출력 |
| `/forge/profiles`, `/forge/profiles/<profileId>` | Workspace profile 목록과 편집. `new`는 새 profile. 편집 화면에서 기본 선택과 삭제를 한다 |
| `/settings/forge/organization-profile` | 조직 기본 profile(Studio 관리자) |
| `/forge/git` | 사용자를 기다리는 보호된 Git 작업 목록 |
| `/forge/git/approvals/<approvalId>` | 보호된 Git 작업 하나의 승인 상세. 닫힌 화면이다. Helper는 이동하지 않고 링크를 준다 |
| `/forge/git/hosts` | Git 호스트와 연결 상태. 연결은 `/profile/git`에서 한다 |
| `/forge/git/repositories` | Forge가 만든 저장소 기록 |
| `/forge/desktops`, `/forge/desktops/<desktopId>` | 사용자의 개발 데스크톱 |
| `/forge/desktops/requests`, `/forge/desktops/all`, `/forge/desktops/pools` | 데스크톱 승인 요청(닫힌 화면), 전체 데스크톱, 데스크톱 풀(Studio 관리자) |

## 보호된 Git 작업 승인

승인·거절은 Workspace 소유자만 한다. 모델은 승인하지 않고, Chat 글로 승인을 요청하지 않는다.

1. `run_submit` 결과나 `run_get`의 `approval.id`로 `git_approval_get`을 호출한다. Studio Chat에서는 그 결과가 승인 화면으로 보인다.
2. 소유자에게 화면의 **승인**·**거절**을 누르고 Studio 승인 카드에서 확인하라고 안내한다.
   화면을 쓸 수 없으면 결과의 `approvalUrl`(`/forge/git/approvals/<approvalId>`)을 준다. 그 화면에서 **이 작업 승인**이나 **거절**을 누르고 확인 창에서 확인한다.
3. 승인 화면에서 확인할 것: `publish-protected`·`merge`·`tag`는 Workspace branch가 커밋한 변경(`prepare` 기준 커밋부터 승인할 HEAD까지의 diff)을 보여 준다.
   `merge`의 화면에는 Git 호스트의 PR/MR을 여는 링크가 있다. `release`·`deploy`의 화면은 diff 대신 승인 대상을 설명한다.
4. 기한은 Run 접수 후 24시간이다. 기한이 지나면 승인할 수 없고 Forge가 Run을 취소한다.
5. 결정 결과는 Run이 끝난 뒤 Chat으로 돌아온다. 반복 조회하지 않는다.

## 처음 설정

1. 사용자가 프로필 → Git 계정(`/profile/git`)에서 작업할 Git 호스트를 연결한다. `git_connections`에서 그 host의 `status`가
   `connected`인지 확인한다. 저장소는 등록하지 않는다. Tools의 GitHub MCP 연결과는 별개의 연결이다.
2. `/forge/profiles/new`에서 profile을 만들고 기본으로 선택한다. 조직 기본 profile이 있으면 그것이 대신 적용된다.
   `repositoryMode`의 기본값 `all`은 기존 저장소 작업과 새 저장소 생성을 모두 허용한다.
   저장소를 제한하려면 `selected`·`owners`·`new`를 고르고 허용 저장소를 지정한다.
   `selected` 모드에 저장소 목록이 비어 있으면 어떤 저장소도 허용하지 않으므로 `prepare`와 `repository_create`가 거절된다.
3. Studio에서 작업할 Agent의 `mcpList`에 `agent-forge`를 연결한다. [journeys](journeys.md#코딩-agent-준비)

## 오류

| 코드·증상 | 원인과 해결 |
|---|---|
| `git_connection_required` (409, Run `errorCode`) | 사용자가 그 Git 호스트를 연결하지 않았거나 다시 연결해야 한다. 오류나 Run의 `connectUrl`을 링크로 준다. 사용자가 연결한 뒤 다시 제출한다 |
| `git_repository_not_found` (404) | 저장소가 없거나, 이름이 바뀌었거나, 연결한 계정이 볼 수 없다. 다시 연결하게 하지 않는다. 저장소 이름과 그 계정의 권한을 확인한다 |
| `invalid_repository` (400) | `origin`이 이 설치의 Git 호스트가 아니거나 저장소 경로 형식이 틀렸다(GitHub·Gitea는 `owner/repo`, GitLab은 두 마디 이상). Forge는 Git 호스트 연결보다 먼저 이것을 검사한다. `git_connections`의 host `origin`과 경로를 확인한다 |
| 저장소 생성 `failed`(namespace) | 영수증의 `error`가 namespace(GitHub·Gitea owner, GitLab 사용자 이름·group 경로)가 없거나 그 계정이 만들 수 없다고 알리고, 비슷한 경로의 namespace가 있으면 붙인다. 사용자에게 어느 namespace인지 확인한 뒤 새 `requestKey`로 다시 요청한다. 같은 키로 입력을 바꾸면 `repository_creation_conflict`(409)다 |
| `git_account_changed` (403) | 연결된 Git 계정이 그 Workspace를 `prepare`한 계정과 다르다. 원래 계정을 다시 연결하거나 새 Workspace에서 `prepare`한다 |
| `repository_identity_changed` (403) | Workspace 저장소의 저장소 ID·공개 범위·주소가 바뀌었다. 대상을 확인하고 새 Workspace에서 `prepare`한다 |
| `git_host_removed` (409) | 운영자가 그 Git 호스트를 설치에서 제거했다. 현재 Git 호스트의 저장소로 새 Workspace에서 `prepare`한다 |
| `git_branch_exists` | `publish-protected`가 새로 만들려던 branch가 실행할 때 이미 있었다. 아무것도 바뀌지 않았다. 대상 branch를 확인한다 |
| `profile_repository_forbidden` (403) | profile의 저장소 규칙이 그 저장소를 허용하지 않는다. profile 소유자가 `/forge/profiles/<profileId>`에서 규칙을 바꿔야 한다 |
| `git_approval_invalid` (403), 승인 만료 | 승인이 거절·만료됐거나 승인한 대상이 바뀌었다. 승인 기한은 Run 접수 후 24시간이다. 보호된 작업의 Run은 요청한 `timeoutMs`와 관계없이 제한 시간이 24시간 10분이므로 `timeoutMs`를 바꿔도 기한은 바뀌지 않는다. 기한이 지나면 승인할 수 없고 Forge가 Run을 취소한다. `git_approval_get`의 `status`가 `expired`·`cancelled`이면 그 요청은 끝났다. 사용자가 다시 요청하면 새 Run을 제출하고 기한 안에 승인하게 안내한다 |
| `git_action_unsupported` (409) | 그 Workspace에서 실행할 수 없는 Git 단계다. `sourceRevision`으로 준비한 Workspace의 `review` 밖의 단계, base branch가 저장소의 기본 branch가 아닌 Workspace의 `merge`, `ref`가 기본 branch가 아닌 `deploy`, GitLab·Gitea 저장소의 `release`·`deploy`, 기본 branch로의 `publish-protected`다. 접수할 때 거절되며 승인과 Run은 만들어지지 않는다. `error`가 이유를 알린다. `merge`이면 사용자가 Git 호스트에서 그 PR을 병합한다 |
| `sandbox_outdated` (409) | Workspace의 Sandbox가 이전 Forge 이미지로 시작돼 승인에 기록할 커밋된 변경을 읽을 수 없다. Git `review`를 한 번 실행한 뒤 그 결과의 `headSha`·`fingerprint`로 보호된 작업을 다시 요청한다 |
| `workspace_profile_conflict` (409) | 읽은 뒤 profile이 바뀌었다. `profile_get`으로 다시 읽는다 |
| `console_required` (403) | 조직 profile의 생성·수정·범위 변경·삭제는 MCP로 할 수 없다. 오류의 `consoleUrl`을 주고 Studio 관리자가 AgentOps 화면에서 하도록 안내한다. 다시 시도하지 않는다 |
| `profile_in_use` (409) | 삭제하려는 profile을 닫지 않은 Workspace나 끝나지 않은 Run이 쓴다. `error`가 본인·다른 사용자의 Workspace 수와 Run 수를 알린다. 본인 Workspace를 닫고 Run이 끝난 뒤 다시 삭제한다. 다른 사용자의 Workspace가 쓰면 그 profile을 나만(`scope:user`)으로 바꿔야 하며, 조직 profile이면 Studio 관리자가 AgentOps 화면에서 바꾼다 |
| `profile_required`, `profile_input_conflict` (400) | `profileId`·`profileRevision`을 함께 보낸다 |
| `profile_runtime_mismatch` (409) | runtime이 다르다. 새 Workspace를 만든다 |
| `profile_model_unavailable` | profile에 활성 모델을 다시 고른다 |
| `timeout_exceeds_authorization` (400) | `timeoutMs`를 줄인다 |
| `work_authorization_invalid` | 다시 로그인하고 새 `requestKey`로 제출한다 |
| `reauthorization_required` (403, Run `errorCode`) | 이전 위임으로 접수된 작업은 계속할 수 없다. 사용자가 새 Run을 제출한다 |
| `model_gateway_unavailable` (503) | 운영 문제다. 무조건 다시 제출하지 않는다 |
| `delivery_variables_invalid` | dev Variable 이름이 Sandbox 예약 이름(예: `OPENAI_*`)과 겹친다. Runway에서 이름을 바꾼다 |
| `directory_account_required` | Studio가 사용자의 디렉터리 계정을 모른다. 관리자가 Studio의 profile 매핑을 고쳐야 데스크톱을 요청할 수 있다 |
| Run `succeeded`인데 `outputLoss=true` | 출력 일부가 영구 손실됐다. 결과 전체를 추정하지 않고 남은 검증 근거를 확인한다 |
