# PR 자동 리뷰 Agent

## Agent와 저장소 선택

[code-review-agent.md](prompts/code-review-agent.md) 프롬프트와 `code-review` Skill을 연결한다.
Agent의 Webhook 동작에서 GitHub PR 리뷰를 선택하고, Agent의 GitHub MCP 계정이 접근 가능한
저장소 전체 또는 명시적 `owner/repo` 목록(최대 20개)을 설정한다. 리뷰 게시 설정은 관리자가 활성화한다.
기본 Agent 공개 범위는 검토 자료의 접근 범위에 맞춘다.

필수 조건:

- 호스트 앱의 `GITHUB_API_URL`·`GITHUB_WEB_URL`이 대상 GitHub authority를 가리킨다.
- Agent에 같은 authority의 OAuth를 쓰는 GitHub MCP 하나를 바인딩한다.
- Agent 정책에서 `ReviewSource`를 차단하거나 승인 대상으로 두지 않는다.

## GitHub Webhook 연결

호출할 사용자는 본인의 Webhook 토큰을 발급받고, Agent에 바인딩한 GitHub MCP를 본인 계정으로 연결한다.
실행은 토큰 발급 사용자의 개인 OAuth 권한을 사용한다. 그 GitHub 계정에는 대상 저장소의 Contents 읽기와
Pull requests 읽기·쓰기 권한이 필요하다. GitHub 저장소 Webhook에는 개인 토큰 화면에서 복사한 URL을 Payload URL로,
Content type은 `application/json`으로 지정하고 Pull requests 이벤트를 등록한다.
시크릿은 저장소 파일·Agent 프롬프트·PR·로그에 넣지 않는다.

## 리뷰 실행과 게시

호스트 앱이 서명·저장소·PR·HEAD를 검증하고 리뷰 Agent를 백그라운드 작업으로 실행한다. Workspace는 만들지 않는다.
Agent는 Skill과 해당 PR에 고정된 `ReviewSource`로 PR의 파일·patch·검사 결과를 읽는다. 코드나 테스트는 실행하지 않는다.
호스트가 head SHA에 고정한 COMMENT 리뷰 하나를 게시하고, 본문에 코드를 실행하지 않았다고 적는다.
Agent가 게시 위치나 다른 저장소를 고르지 않으며 소스 수정·Git publication·PR 승인·merge·배포를 실행하지 않는다.
전달한 파일·diff 범위와 누락 여부는 실행 입력과 게시 본문에 표시된다.

## 이벤트와 결과 확인

`opened`, `synchronize`, `reopened`, `ready_for_review`가 열린 일반 PR의 리뷰를 요청한다.
같은 HEAD는 중복 처리하지 않으며 실행 중 HEAD가 바뀌면 오래된 리뷰를 게시하지 않는다.
GitHub ping은 연결 검사일 뿐 리뷰 성공이 아니다. Trigger 전달 이력의 `review.status`와
게시된 URL, GitHub의 해당 commit_id를 함께 확인한다. 실패한 외부 쓰기는 자동 재전송하지 않는다.

검증에는 실제 PR 이벤트·본문 검토·댓글·같은 이벤트 중복 방지를 포함한다. 합성 diff로
Agent가 결함을 찾았다는 사실만으로 Webhook 연결이나 게시를 검증했다고 보고하지 않는다.
