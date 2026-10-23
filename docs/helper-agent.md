# Helper Agent profile

Agent Studio의 상단 헤더의 Helper는 운영자가 관리하는 하나의 private Agent다. 대화·도구 호출·승인·비용·기록은
일반 Agent와 같은 실행 경로를 사용한다. 운영자가 Settings에서 기본 Helper를 만들면 Studio가 설치에 선택된 모델과
사용 가능한 `agent-helper`, `prompt-writer`, `skill-writer`, `simple-orchestration`을 연결한다.

`agent-helper`는 화면 설명, Agent 생성·개선과 Agent 전용 Skill 작성 절차를 소유한다. `StudioRead`,
`StudioCreateAgent`, `StudioUpdateAgent`, `StudioSaveSkill`, `StudioDeleteSkill`은 Studio 내부 권한과
저장소를 사용하는 내장 도구다. 변경 도구는 Agent 정책과 관계없이 사용자 승인을 받는다.
전용 Skill은 Studio에 직접 저장되며 이 저장소의 sync 대상이 아니다. 공유 Skill은 이 저장소에서 관리한다.
이 저장소에 별도 MCP 서버나 credentials를 만들지 않는다. Plugin sync 이후 기존 Helper의
Skill 목록은 운영자가 Agent 설정에서 갱신한다. sync가 사용자 설정을 덮어쓰지 않는다.

Helper의 현재 화면 공유를 끄면 화면 자료를 다음 메시지에 첨부하지 않는다. 앞선 대화의
자료는 기존 Chat 수명을 따른다. 입력값·비공개 영역은 화면 수집에서 제외되며 사용자가
직접 메시지로 보낸 자료는 일반 대화 입력으로 처리한다.

검증 시 `evals/helper-agent.json`의 요청을 실제 연결된 모델·도구로 실행하고 도구 응답,
저장 결과, 권한 거절과 충돌 처리를 확인한다. 정적 시나리오 검토는 모델 검증을 대신하지 않는다.

멤버는 Helper 전용 Chat으로 사용한다. 일반 Agent 목록과 설정 조회는 private 소유권 규칙을
유지한다. Helper의 관리 도구는 운영자 권한이 아니라 대화 요청자의 권한으로 실행된다.

## 화면 제어

StudioScreen은 현재 화면 조회와 내부 페이지 이동을, StudioControl은 승인된 클릭·입력·선택·
포커스와 페이지 전용 초안 편집을 수행한다. `agent_draft`는 폼 상태만 바꾸며 저장 API를
호출하지 않는다. 별도의 저장 성공을 확인하기 전에는 영구 저장된 상태가 아니다.
페이지가 바뀌어도 Helper는 같은 대화를 유지한다.
브라우저가 결과를 확인해 반환하기 전에는 Agent가 다음 작업으로 진행하지 않는다.
요청은 대화·탭·실행에 묶이며, 이미 처리한 클릭은 재연결로 다시 실행하지 않는다.
Native WebMCP 지원이나 agent-browser 설치를 요구하지 않는다.
