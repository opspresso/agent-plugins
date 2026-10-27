# Git 게시와 확인

Forge의 Git 실행 계약이다. Git 단계마다 `run_submit`에 `input.kind="git"`과 `action`을 보낸다. 실제 제공된 schema가 우선한다.
코딩 요청의 기본 완료 범위는 새 작업 브랜치의 구현·검증·커밋·푸시·PR이다.
사용자가 게시를 금지하거나 로컬 수정만 요청하면 그 범위를 따른다. 조회·리뷰 요청에는 게시를 추가하지 않는다.

## 동작과 필수 입력

| 요청 | `action` | 필수 입력 | 승인 |
|---|---|---|---|
| 저장소 준비 | `prepare` | `connectionId`, `baseBranch`, `branch`(`agent/`로 시작), 선택 `sourceRevision` | 없음 |
| 변경 검토 | `review` | 없음 | 없음 |
| 커밋 | `commit` | `fingerprint`, `message` | 없음 |
| 작업 브랜치 푸시 | `push` | `headSha` | 없음 |
| PR 생성·갱신 | `pull-request` | `headSha`, `fingerprint`, `title`, `body`, `draft` | 없음 |
| 보호 branch 직접 게시 | `publish-protected` | `targetBranch`, `expectedHeadSha`, `headSha`, `fingerprint` | Forge 콘솔 |
| PR을 main에 병합 | `merge` | `pullRequestNumber`, `headSha`, `fingerprint` | Forge 콘솔 |
| 태그 | `tag` | `tag`, `message`, `headSha`, `fingerprint` | Forge 콘솔 |
| 릴리즈 | `release` | `tag`, `headSha`, `fingerprint`, `title`, `body`, `draft`, `prerelease` | Forge 콘솔 |
| 배포 | `deploy` | `workflow`, `ref:"main"`, `inputs`, `headSha`, `fingerprint` | Forge 콘솔 |

`connectionId`는 `git_connections`의 `repositories[].id`다. `headSha`·`fingerprint`는 직전 `review`·`commit` 실행의
`run_result.gitResult`에서 받은 실제 값이다. 값을 추측하거나 다른 실행의 값을 섞지 않는다.

## 작업 브랜치 게시

1. 파일 수정과 검사를 마친 뒤 `review`를 실행한다. `gitResult`의 `diff`·`truncated`로 요청 밖 변경이 없는지 확인한다.
2. `commit`에 review의 `fingerprint`와 실제 변경을 설명하는 `message`를 보낸다.
3. `push`에 commit 결과의 `headSha`를 보낸다. Forge는 `agent/` 브랜치에 정확한 HEAD만 non-force push한다.
4. `pull-request`에 같은 `headSha`·`fingerprint`와 실제 결과를 담은 제목·본문을 보낸다. 같은 브랜치의 열린 PR은 갱신된다.

```json
{"tool":"run_submit","arguments":{"workspaceId":"<id>","input":{"kind":"git","action":"commit","fingerprint":"<review fingerprint>","message":"fix: return 400 for empty input"},"profileId":"<profile id>","profileRevision":3,"requestKey":"<고정 키>"}}
```

이 네 단계는 별도 승인 없이 실행한다. 각 단계의 실제 결과(`gitResult.headSha`, PR `url`)를 확인한 뒤 다음 단계로 간다.
PR 설명 형식이 필요하고 `pr-description`이 연결됐으면 해당 Skill을 사용한다.
`sourceRevision`으로 고정한 검토 Workspace에서는 commit·push·보호 게시·tag가 거절된다. 다른 도구로 우회하지 않는다.

## 보호 작업과 승인

- 보호 작업은 사용자가 그 동작을 요청한 경우에만 제출한다. PR 생성이 main 병합·태그·릴리즈·배포 요청을 포함하지 않는다.
- 제출하면 Run은 `queued`에서 승인을 기다린다. 응답의 `approvalUrl`을 링크로 전달하고 Forge 콘솔에서 Workspace 소유자가 승인해야 한다고 알린다.
  MCP에는 승인 결정 도구가 없다. `git_approval_get`은 승인 상태를 읽기만 한다.
- 승인 대기도 Run의 `timeoutMs`에 포함된다. 거절·만료·취소는 효과를 막는다.
- Studio Chat에서 제출한 보호 작업의 terminal 결과는 원래 Chat에 전달된다. 승인 여부를 반복 조회하지 않는다.
- 여러 단계를 요청했으면(예: PR 생성 후 main 병합) 각 단계를 순서대로 진행한다. 한 단계의 성공을 전체 요청 완료로 표현하지 않는다.

## 병합·태그·릴리즈·배포

- `merge`는 main 대상 PR의 현재 HEAD와 CI를 확인한 뒤 GitHub head SHA 조건으로 병합한다. 사용자가 PR 병합을 요청했으면 `publish-protected`로 대체하지 않는다.
- `tag`는 검토한 HEAD에 annotated tag를 만든다. 기존 tag를 덮어쓰지 않는다.
- `release`는 이미 있는 tag가 가리키는 승인 commit과 CI를 확인한다. tag 성공 뒤에만 준비한다.
- `deploy`는 profile의 `deploymentWorkflows`에 있는 workflow만 허용한다. `inputs`는 이름→값 object다.
  Forge는 workflow run이 끝날 때까지 `running`을 유지하고 provider 결론을 결과에 남긴다. dispatch 접수만으로 배포 완료라고 하지 않는다.
  실제 서비스 상태를 확인한 뒤 배포 완료를 보고한다.

## 오류와 재시도 경계

- 외부 응답 유실·5xx·불명확한 결과는 `interrupted`다. 같은 게시를 새 키·새 Workspace·다른 API로 반복하지 않는다.
- `failed`는 원인을 확인하고 수정한 뒤 새 review부터 다시 준비한다. 성공한 단계를 다시 실행하지 않는다.
- `run_retry`는 사용자가 재시도를 명시적으로 요청한 failed·cancelled 실행에만 쓴다. 이미 dispatch한 Git 효과나 interrupted 실행은 재시도할 수 없다.
- native 작업에 git add·commit·push·merge를 시키거나 GitHub MCP 쓰기·임시 index로 Forge의 Git 경계를 우회하지 않는다.
- GitHub token은 Forge가 서버에서만 사용한다. 작업 지시·Sandbox·로그에 credential을 넣지 않는다.
