# PR·MR 자동 리뷰 Agent

GitHub pull request(PR)와 GitLab merge request(MR)를 Agent Studio의 Webhook으로 자동 리뷰한다.
한 Webhook은 GitHub PR 리뷰(`githubReview`)와 GitLab MR 리뷰(`gitlabReview`) 중 하나만 가진다.
다른 쪽으로 바꾸려면 같은 요청에서 기존 리뷰를 `null`로 보낸다(예: `{ githubReview: null, gitlabReview: { … } }`).

## Agent와 저장소 선택

[code-review-agent.md](prompts/code-review-agent.md) 프롬프트와 `code-review` Skill을 연결한다.
리뷰 게시 설정은 관리자가 활성화한다. 기본 Agent 공개 범위는 검토 자료의 접근 범위에 맞춘다.
두 리뷰 모두 Agent 정책에서 `ReviewSource`를 차단하거나 승인 대상으로 두지 않아야 한다.

**GitHub PR 리뷰**: Agent의 Webhook 동작에서 GitHub PR 리뷰를 선택하고, Agent의 GitHub MCP 계정이 접근 가능한
저장소 전체 또는 명시적 `owner/repo` 목록(최대 20개)을 설정한다.

- 호스트 앱의 `GITHUB_API_URL`·`GITHUB_WEB_URL`이 대상 GitHub authority를 가리킨다.
- Agent에 같은 authority의 OAuth를 쓰는 GitHub MCP 하나를 바인딩한다.

**GitLab MR 리뷰**: Agent의 Webhook 동작에서 GitLab MR 리뷰를 선택하고, `host`와 범위를 설정한다.

- `host`는 운영자가 Agent Studio의 `GIT_HOSTS`에 등록한 Git 호스트 중 provider가 `gitlab`인 호스트의 이름이다.
  gitlab.com과 self-managed GitLab이 모두 된다. 등록되지 않았거나 provider가 다른 이름은 400으로 거절된다.
- 범위는 호출자의 Git 계정이 접근 가능한 프로젝트 전체(`scope: "accessible"`) 또는 명시적 프로젝트 경로 목록
  (`scope: "repositories"`, `group/subgroup/project`, 최대 20개)이다.
- GitLab MCP는 필요 없다. GitLab MCP grant는 `mcp` scope만 가져 REST API를 쓸 수 없으므로, Studio는 호출자의 Git 계정 연결로
  MR을 읽고 노트를 게시한다.

## Webhook 연결

호출할 사용자는 본인의 Webhook 토큰을 발급받는다. 실행은 토큰 발급 사용자의 권한을 사용한다.
시크릿은 저장소 파일·Agent 프롬프트·PR/MR·로그에 넣지 않는다.

**GitHub**: 사용자는 Agent에 바인딩한 GitHub MCP를 본인 계정으로 연결한다. 그 GitHub 계정에는 대상 저장소의 Contents 읽기와
Pull requests 읽기·쓰기 권한이 필요하다. GitHub 저장소 Webhook에는 개인 토큰 화면에서 복사한 URL을 Payload URL로,
Content type은 `application/json`으로, 전체 Webhook 토큰을 Secret으로 지정하고 Pull requests 이벤트를 등록한다.

**GitLab**: 사용자는 Agent Studio의 프로필 → Git 계정(`/profile/git`)에서 그 GitLab 호스트를 본인 계정으로 연결한다.
그 GitLab 계정이 대상 프로젝트의 MR을 읽고 노트를 쓸 수 있어야 한다. GitLab 프로젝트 Webhook에는 Agent의 Webhook 주소
(`/api/webhook/<agent>`. `credential` 쿼리는 GitLab 전달에 쓰지 않는다)를 URL로, 전체 Webhook 토큰을 Secret token으로
지정하고 Merge request events를 구독한다. GitLab 17.4 이상이어야 한다. Studio는 GitLab이 17.4부터 보내는 delivery ID
(`webhook-id` 또는 `Idempotency-Key`)가 없는 전달을 400으로 거절한다.

## 리뷰 실행과 게시

호스트 앱이 인증·저장소·PR/MR·HEAD를 검증하고 리뷰 Agent를 백그라운드 작업으로 실행한다. 작업 공간은 만들지 않는다.
Agent는 Skill과 해당 PR/MR에 고정된 `ReviewSource`로 파일·patch·검사 결과를 읽는다. 코드나 테스트는 실행하지 않는다.
Agent가 게시 위치나 다른 저장소를 고르지 않으며 소스 수정·Git 게시·승인·merge·배포를 실행하지 않는다.
전달한 파일·diff 범위와 누락 여부는 실행 입력과 게시 본문에 표시된다.

- **GitHub**: 호스트가 head SHA에 고정한 COMMENT 리뷰 하나를 게시하고, 본문에 코드를 실행하지 않았다고 적는다.
- **GitLab**: 호스트가 MR에 일반 노트 하나를 게시한다. GitLab 노트는 commit에 연결되지 않으므로 본문이 검토한 커밋을 밝힌다.
  변경 목록이 완전하지 않으면(예: `1000+`) 전체 리뷰를 게시하지 않는다. 승인·merge·라벨 변경은 하지 않는다.
  게시된 노트의 작성자가 연결한 계정과 다르면 게시를 확인하지 않은 것으로 실패 처리한다.

## 이벤트와 결과 확인

리뷰를 요청하는 이벤트는 다음과 같다. 같은 HEAD는 중복 처리하지 않으며 실행 중 HEAD가 바뀌면 오래된 리뷰를 게시하지 않는다.

- **GitHub**: 열린 일반 PR의 `opened`, `synchronize`, `reopened`, `ready_for_review`. GitHub ping은 연결 검사일 뿐 리뷰 성공이 아니다.
- **GitLab**: 열린 MR의 `open`, `reopen`, 새 커밋이 있는 `update`, draft에서 ready로 바뀐 `update`.
  draft·closed·merge·승인 같은 다른 동작은 모델을 실행하지 않고 `ignored`로 끝난다.

필수 설정이 없으면 전달은 `409 review-not-ready`이고 Trigger 이력에 skipped로 남는다. GitLab에서는 `host`가 `GIT_HOSTS`에서
빠졌거나, 호출자가 그 호스트를 연결하지 않았거나, 연결이 `reconnect_required`일 때도 그렇다. 설정이나 연결을 고친 뒤
Git 호스트에서 같은 HEAD의 이벤트를 다시 전달한다.

Trigger 전달 이력의 `review.status`와 게시된 URL을 확인한다. GitHub는 그 리뷰의 commit_id를, GitLab은 노트 본문의 검토 커밋과
이력의 `review.provider`(`gitlab`)·`host`·게시한 계정(`account.login`)을 함께 확인한다. 실패한 외부 쓰기는 자동 재전송하지 않는다.

검증에는 실제 PR/MR 이벤트·본문 검토·댓글 또는 노트·같은 이벤트 중복 방지를 포함한다. 합성 diff로
Agent가 결함을 찾았다는 사실만으로 Webhook 연결이나 게시를 검증했다고 보고하지 않는다.
