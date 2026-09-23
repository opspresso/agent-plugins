# PR 자동 리뷰 Agent

[code-review-agent.md](prompts/code-review-agent.md) 프롬프트와 `code-review` Skill을 연결한다.
프로젝트의 Webhook 동작에서 GitHub PR 리뷰를 선택하고 설치의 GitHub 계정이 접근 가능한
저장소 전체 또는 명시적 `owner/repo` 목록을 설정한다. 공유 GitHub 연결로 댓글을 쓰는
설정이므로 관리자가 활성화한다. 기본 프로젝트 공개 범위는 검토 자료의 접근 범위에 맞춘다.

GitHub 저장소에서 Payload URL을 `/api/webhook/{project}`로, Content type을
`application/json`으로 지정하고 해당 프로젝트 Webhook Secret과 Pull requests 이벤트를
등록한다. 시크릿은 저장소 파일·Agent 프롬프트·PR·로그에 넣지 않는다.
저장소를 읽을 수 있어도 Pull requests 쓰기 권한이 없으면 댓글 게시가 실패한다.

Studio가 서명·저장소·PR·HEAD를 검증하고 제공한 변경 내용으로 Agent를 실행한 후
해당 커밋에 COMMENT 리뷰를 게시한다. Agent가 댓글 도구나 게시 위치를 고르지 않으며
이 모드에는 Skill 읽기만 제공된다. 변경 코드 실행·PR 승인·merge·배포는 포함하지 않는다.
최대 파일 수·diff 문맥 한도와 누락 여부는 실제 실행 입력과 게시 본문에 표시된다.

`opened`, `synchronize`, `reopened`, `ready_for_review`가 열린 일반 PR의 리뷰를 요청한다.
같은 HEAD는 중복 처리하지 않으며 실행 중 HEAD가 바뀌면 오래된 리뷰를 게시하지 않는다.
GitHub ping은 연결 검사일 뿐 리뷰 성공이 아니다. Trigger 전달 이력의 `review.status`와
게시된 URL, GitHub의 해당 commit_id를 함께 확인한다. 실패한 외부 쓰기는 자동 재전송하지 않는다.

검증에는 실제 PR 이벤트·본문 검토·댓글·같은 이벤트 중복 방지를 포함한다. 합성 diff로
Agent가 결함을 찾았다는 사실만으로 Webhook 연결이나 게시를 검증했다고 보고하지 않는다.
