# Helper Agent 프로필

Helper는 운영자가 관리하는 하나의 private Agent다. 사용자는 AgentOps 콘솔(Studio와 모든 Agent 서비스의 화면) 헤더의
**Helper** 버튼으로 오른쪽 dock을 연다. 사용자가 페이지를 옮겨도 같은 Chat이 이어진다.
Chat·도구 호출·승인·비용·기록은 일반 Agent와 같은 실행 경로를 사용한다.

## 구성

운영자가 설정의 Studio 서비스 section(`/settings/studio/service`)에서 기본 Helper를 만들면 Studio가 설치에 선택된 모델과
다음 Skill 중 사용 가능한 것을 연결한다. 같은 화면에서 운영자의 다른 private Agent를 Helper로 고를 수도 있다.

| Skill | 역할 |
|---|---|
| `agent-helper` | 플랫폼 지도, 요청 처리 순서, 화면 이동·조작, 사람의 결정 안내, Agent 생성·개선, 서비스 작업, 문제 해결 |
| `prompt-writer`, `skill-writer` | Agent 프롬프트와 전용 Skill 작성 |
| `simple-orchestration` | 하위 Agent 위임 |
| `workspace-task`, `app-delivery`, `audio-processing` | Forge 작업, 앱 개발·배포, 녹음 처리 절차 |

`agent-helper`는 `SKILL.md`에 플랫폼 지도와 공통 원칙을 두고, 서비스별 상세는 참고 파일로 나눈다. Helper는 요청에 필요한 파일만 읽는다.

| 참고 파일 | 내용 |
|---|---|
| `references/agent-settings.md` | Studio 단위, 설정 선택, 서비스 연결, 모델, Trigger·메신저, 비밀 값, 전용 Skill |
| `references/memory.md`, `knowledge.md`, `forge.md`, `delivery.md` | 서비스 개념, Helper가 쓸 수 있는 도구, AgentOps 화면, 사람이 화면에서 하는 작업, 오류 |
| `references/journeys.md` | 앱 개발·배포, 녹음→회의록, 문서 Q&A Agent, 기억하는 Agent, 코딩 Agent, 메신저 봇 |
| `references/troubleshooting.md` | 진단 순서, 증상별 확인·해결, 응답 유실 복구, 관리자 전달 |

서비스 참고 파일은 각 서비스의 MCP 도구 등록 코드와 AgentOps 화면 경로(agentops `docs/ROUTES.md`)에 맞춘다. 서비스의 도구·화면·오류
코드가 바뀌면 해당 파일을 함께 갱신한다. Agent Models는 MCP 서버가 없으므로 `agent-settings.md`에서 다룬다.

Studio는 실행마다 Studio 도구 사용 규칙과 콘솔 페이지 지도(Studio `src/domain/helper/consolePages.ts`의 `CONSOLE_PAGES`)를
Helper 안내문에 붙인다. 그래서 Skill은 페이지 지도 전체를 복제하지 않고 작업별 대표 경로만 적는다. 이 규칙은 Helper 프롬프트를 갱신하지 않아도 적용된다.

## Plugin sync와 기존 Helper

이 저장소의 `main`이 바뀌면 Studio의 Plugin sync가 Skill 내용을 갱신한다. `PLUGINS_REPO`를 설정한 배포는 schedule ticker의
`/api/plugins/sync/scan` 호출로 자동 동기화하고, 관리자는 `/studio/plugins`에서 결과를 확인한다.
기존 Helper의 `skillList`는 Skill 이름을 저장하므로, 연결된 Skill의 내용이 바뀌는 것만으로는 Agent 설정을 바꿀 필요가 없다.
Skill을 더하거나 빼려면 운영자가 Helper Agent의 Playground에서 `skillList`를 갱신한다. sync가 사용자 설정을 덮어쓰지 않는다.
Helper의 시스템 프롬프트는 Helper를 만들 때 저장된 값이다. 운영자가 고치지 않으면 바뀌지 않는다.

## 도구와 권한

`StudioRead`, `StudioCreateAgent`, `StudioUpdateAgent`, `StudioSaveSkill`, `StudioDeleteSkill`, `StudioSaveTrigger`,
`StudioDeleteTrigger`, `StudioUpdateIntegration`, `StudioRequestCredential`은 Studio 내부 권한과 저장소를 사용하는 내장 도구다.
변경 도구는 Agent 정책과 관계없이 사용자 승인을 받는다. 비밀 값은 대화로 받지 않는다. 사용자가 승인 카드의 보안 입력이나
해당 화면에 직접 입력한다.

Helper Chat에서는 배포가 연결한 Agent 서비스의 도구 항목이 자동으로 연결된다. 서비스가 읽기 전용으로 표시하지 않은 도구는
승인 후 실행한다. 사람의 결정은 Helper가 하지 않는다.

- Forge의 보호된 Git 작업은 Workspace 소유자가 Chat의 승인 화면과 승인 카드, 또는 `/forge/git/approvals/<approvalId>`에서 승인한다.
- Runway의 소유자 배포 승인은 소유자가 Chat의 배포 화면과 승인 카드, 또는 `/runway/projects/<slug>/deployments/<deploymentId>`에서 한다.
- Runway secret 값은 사용자가 `/runway/projects/<slug>/secrets/new`에서 입력한다.
- Runway의 서비스·리소스·Project 삭제, `push_enable`, `host_move`는 MCP 도구로 요청하며 Studio가 호출마다 사람의 승인을 받는다.
- Forge와 Runway가 쓰는 Git 호스트 계정은 사용자가 프로필 → Git 계정(`/profile/git`)에서 연결한다.
- 결정을 기다리는 항목은 받은 일(`/inbox`)에 모인다.

전용 Skill은 Studio에 직접 저장되며 이 저장소의 sync 대상이 아니다. 공유 Skill은 이 저장소에서 관리하고 이름에 `--`를 쓰지 않는다.
이 저장소에 별도 MCP 서버나 자격 증명을 만들지 않는다.

구성원은 Helper 전용 Chat으로 사용한다. 일반 Agent 목록과 설정 조회는 private 소유권 규칙을 유지한다. Helper의 관리 도구와
서비스 도구는 운영자 권한이 아니라 Chat 요청자의 권한으로 실행된다.

## 화면

`StudioScreen`은 두 동작을 한다. `inspect`는 현재 화면을 읽고, `navigate`는 콘솔 페이지 지도의 경로(query 허용)로 이동한다.
서비스마다 다른 콘솔을 여는 동작은 없다. 지도에 없는 경로는 Studio와 AgentOps가 거절한다.
`StudioControl`은 승인된 클릭·입력·선택·포커스와 페이지 전용 초안 편집을 수행한다. `agent_draft`는 폼 상태만 바꾸며
저장 API를 호출하지 않는다. 브라우저가 결과를 확인해 반환하기 전에는 Agent가 다음 작업으로 진행하지 않는다.
Native WebMCP 지원이나 agent-browser 설치를 요구하지 않는다.

AgentOps는 Helper가 읽거나 조작할 수 없는 영역을 정한다(`data-helper-private`).

- 닫힌 화면: 로그인, 메신저 연결 확인, 코딩 클라이언트 연결 승인, 작업 공간 삭제 추적, Forge Git 승인 상세,
  데스크톱 승인 요청, Runway 배포. Helper는 이 화면으로 이동하지 않고 링크를 준다.
- 열린 화면 안의 결정 컨트롤: 확인 대화 상자, 영구 삭제 확인, 승인 카드, 비밀 입력, 승인·거절 버튼, 비밀·token 보기와 폐기,
  구성원 등급 변경. Helper는 그 화면을 열고 사용자가 무엇을 확인하고 누르면 되는지 말한다.

Helper의 **현재 화면 참고**를 끄면 화면 자료를 다음 메시지에 첨부하지 않고 화면 동작 요청에도 응답하지 않는다.
앞선 대화의 자료는 기존 Chat 수명을 따른다. 입력값·비공개 영역은 화면 수집에서 제외되며 사용자가 직접 메시지로 보낸 자료는
일반 대화 입력으로 처리한다.

## 검증

`evals/helper-agent.json`의 요청을 실제 연결된 모델·도구로 실행하고 도구 응답, 저장 결과, 권한 거절, 충돌 처리,
서비스 작업 접수와 화면 안내를 확인한다. 정적 시나리오 검토는 모델 검증을 대신하지 않는다.
