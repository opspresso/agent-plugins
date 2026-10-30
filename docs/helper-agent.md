# Helper Agent profile

Helper는 운영자가 관리하는 하나의 private Agent다. 사용자는 Agent Studio와 Agent 서비스 콘솔(Memory·Knowledge·Forge·Runway)의
헤더 버튼으로 같은 Helper 패널을 연다. 대화·도구 호출·승인·비용·기록은 일반 Agent와 같은 실행 경로를 사용한다.

## 구성

운영자가 Settings에서 기본 Helper를 만들면 Studio가 설치에 선택된 모델과 다음 Skill 중 사용 가능한 것을 연결한다.

| Skill | 역할 |
|---|---|
| `agent-helper` | 플랫폼 지도, 요청 처리 순서, 화면 이동·조작, Agent 생성·개선, 서비스 작업, 문제 해결 |
| `prompt-writer`, `skill-writer` | Agent 프롬프트와 전용 Skill 작성 |
| `simple-orchestration` | 하위 Agent 위임 |
| `workspace-task`, `app-delivery`, `audio-processing` | Forge 작업, 앱 개발·배포, 녹음 처리 절차 |

`agent-helper`는 `SKILL.md`에 플랫폼 지도와 공통 원칙을 두고, 서비스별 상세는 참고 파일로 나눈다. Helper는 요청에 필요한 파일만 읽는다.

| 참고 파일 | 내용 |
|---|---|
| `references/agent-settings.md` | Studio 단위, 설정 선택, 서비스 연결, 모델, trigger·메신저, 비밀 값, 전용 Skill |
| `references/memory.md`, `knowledge.md`, `forge.md`, `delivery.md` | 서비스 개념, Helper가 쓸 수 있는 도구, 콘솔 페이지, 콘솔 전용 작업, 오류 |
| `references/journeys.md` | 앱 개발·배포, 녹음→회의록, 문서 Q&A Agent, 기억하는 Agent, 코딩 Agent, 메신저 봇 |
| `references/troubleshooting.md` | 진단 순서, 증상별 확인·해결, 응답 유실 복구, 관리자 전달 |

서비스 참고 파일은 각 서비스의 MCP 도구 등록 코드와 콘솔 페이지 지도(`helper-pages`)에 맞춘다. 서비스의 도구·페이지·오류
코드가 바뀌면 해당 파일을 함께 갱신한다. Agent Models는 MCP 서버와 Helper 패널이 없으므로 `agent-settings.md`에서 다룬다.

Plugin sync 이후 기존 Helper의 Skill 목록은 운영자가 Agent 설정에서 갱신한다. sync가 사용자 설정을 덮어쓰지 않는다.
Studio 도구 사용 규칙과 Studio 페이지 지도는 Studio가 실행마다 붙이므로 Helper 프롬프트를 갱신하지 않아도 적용된다.

## 도구와 권한

`StudioRead`, `StudioCreateAgent`, `StudioUpdateAgent`, `StudioSaveSkill`, `StudioDeleteSkill`, `StudioSaveTrigger`,
`StudioDeleteTrigger`, `StudioUpdateIntegration`, `StudioRequestCredential`은 Studio 내부 권한과 저장소를 사용하는 내장 도구다.
변경 도구는 Agent 정책과 관계없이 사용자 승인을 받는다. 비밀 값은 대화로 받지 않는다. 사용자가 승인 카드의 보안 입력이나
해당 화면에 직접 입력한다.

Helper 대화에서는 배포가 연결한 Agent 서비스의 Tools 항목이 자동으로 연결된다. 서비스가 읽기 전용으로 표시하지 않은 도구는
승인 후 실행한다. Forge GitHub 연결·보호된 Git 작업 승인, Runway secret 입력·삭제·prod 승인은 서비스 콘솔에서만 한다.

전용 Skill은 Studio에 직접 저장되며 이 저장소의 sync 대상이 아니다. 공유 Skill은 이 저장소에서 관리하고 이름에 `--`를 쓰지 않는다.
이 저장소에 별도 MCP 서버나 credentials를 만들지 않는다.

멤버는 Helper 전용 Chat으로 사용한다. 일반 Agent 목록과 설정 조회는 private 소유권 규칙을 유지한다. Helper의 관리 도구와
서비스 도구는 운영자 권한이 아니라 대화 요청자의 권한으로 실행된다.

## 화면

StudioScreen은 현재 화면 조회, 현재 화면의 페이지 지도 안 이동, 다른 서비스 콘솔을 여는 `open_console`을 수행한다.
StudioControl은 승인된 클릭·입력·선택·포커스와 페이지 전용 초안 편집을 수행한다. `agent_draft`는 폼 상태만 바꾸며
저장 API를 호출하지 않는다. 페이지나 콘솔이 바뀌어도 Helper는 같은 대화를 유지한다. 브라우저가 결과를 확인해 반환하기
전에는 Agent가 다음 작업으로 진행하지 않는다. Native WebMCP 지원이나 agent-browser 설치를 요구하지 않는다.

Helper의 현재 화면 공유를 끄면 화면 자료를 다음 메시지에 첨부하지 않는다. 앞선 대화의 자료는 기존 Chat 수명을 따른다.
입력값·비공개 영역은 화면 수집에서 제외되며 사용자가 직접 메시지로 보낸 자료는 일반 대화 입력으로 처리한다.

## 검증

`evals/helper-agent.json`의 요청을 실제 연결된 모델·도구로 실행하고 도구 응답, 저장 결과, 권한 거절, 충돌 처리,
서비스 작업 접수와 콘솔 안내를 확인한다. 정적 시나리오 검토는 모델 검증을 대신하지 않는다.
