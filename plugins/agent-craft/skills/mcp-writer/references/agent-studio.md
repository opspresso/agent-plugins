# Agent Studio 연결 계약

Agent Studio에 등록할 때만 적용한다. 다른 클라이언트의 기능이나 제한으로 일반화하지 않는다.

## Agent Studio에 등록할 때

- remote 서버는 `streamable-http`를 사용한다. 공유 공급자 endpoint만 `mcp.json`에 두고
  설치별 서비스·주소는 설치 측에서 별도 등록한다. `/mcp`를 임의로 덧붙이지 않는다.
  AWS Knowledge처럼 루트에서 응답하는 서버도 있다.
- secret이 들어갈 `headers`는 저장소에 넣지 않고 설치 측에서 설정한다.
- 번들 서버 description은 같은 plugin의 `org.opspresso.agent-studio/mcp/<name>.md`에 둔다.
  별도 등록한 서버는 실제 노출 도구와 권한에 맞춰 설치 측 description을 설정한다.
- extension의 frontmatter `description`만 모델에게 전달된다. 본문은 운영자용이므로
  등록·인증·배포 설정·진단 절차를 적는다. 모델의 호출 조건은 description이나 연결된 스킬에 둔다.
- `content`가 있으면 Agent Studio는 그 블록을 모델에게 전달하고 별도
  `structuredContent`는 함께 전달하지 않는다. 완전성·잘림·검증 결과처럼 판단에 필요한
  메타데이터를 text 블록에도 담는다. 바이너리는 사용자 파일로 전달되지만 bytes/base64는
  모델 문맥에 넣지 않는다. 저장 후 대화에 실제 파일 ID가 제공되면 `File`로 읽거나 편집할 수
  있다. MCP 응답의 파일명·resource URI를 file_id로 쓰거나 같은 호출 결과에 ID가 있다고
  가정하지 않는다. bytes 입력 도구에는 별도의 실제 전달 경로가 필요하다.
- 스킬과 서버 이름은 저장소 전체에서 중복되지 않아야 한다.
- 스킬 런타임에는 shell·filesystem·network가 없다. 구현·검증 스크립트를 스킬 attachment로
  운반하지 말고 실제 서버 저장소나 개발 도구에서 실행한다.
