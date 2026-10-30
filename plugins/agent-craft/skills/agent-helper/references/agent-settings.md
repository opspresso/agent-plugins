# Agent 설정

Studio의 Agent·Skill·trigger·메신저 연동을 만들거나 고칠 때 읽는다. 도구 계약은 실행마다 Studio가 붙이는
규칙과 도구 schema가 우선한다.

## Studio 단위

| 단위 | 뜻 | 페이지 |
|---|---|---|
| Agent | 모델·프롬프트·Skill·MCP 도구·하위 Agent·정책·한도를 저장한 실행 단위. private은 소유자만, public은 조직 전체가 쓴다 | `/agents`, `/agents/<name>` |
| Skill | 모델이 이름·설명으로 고른 뒤 본문을 읽는 작업 지침. 공유·Plugin·Agent 전용으로 나뉜다 | `/skills` |
| Tools | MCP 서버 레지스트리. 연결된 Memory·Knowledge·Forge·Runway가 각각 항목 하나(`agent-memory` 등)로 보인다 | `/tools`, `/tools/<name>` |
| Plugin | Skill·MCP 정의의 원본 묶음. 관리자가 동기화한다 | `/plugins` |
| Chat·Artifact | 개인 대화와 첨부·생성 파일 | `/chats`, `/artifacts` |

Playground(`/agents/<name>`)는 하나의 현재 설정을 저장한다. 실행은 저장된 설정을 쓰므로 초안은 저장해야 반영된다.
독립 실험은 Agent 복제본으로 한다.

## 설정 선택

`StudioCreateAgent`와 `StudioUpdateAgent`는 다음 설정을 받는다. 요청 목적과 근거가 있는 항목만 바꾼다.

| 설정 | 선택 기준 |
|---|---|
| `model`, `fallbackModel` | `StudioRead(resource="models")`의 모델 `id`만 쓴다. 구조화 출력·추론·이미지 입력 등 필요한 기능이 있는 모델을 고른다 |
| `skillList` | 반복 절차가 공유 Skill과 맞으면 연결한다. 맞는 Skill이 없으면 [전용 Skill](#전용-skill)을 만든다 |
| `mcpList` | 필요한 서버만 `{ name, tools? }`로 연결한다. 도구가 많으면 `StudioRead(resource="tool", name=...)`로 이름을 읽고 필요한 도구만 고른다. `tools` 생략은 현재 선택 유지, `[]`는 모든 도구 |
| `subagentList` | 독립된 전문 작업을 다른 접근 가능한 Agent에 위임할 때만 연결한다 |
| `parameters` | 바꿀 키만 보내고 `null`은 기본값으로 되돌린다. 주요 키는 아래 표 |
| `maxTurn` | 도구 호출이 많은 작업만 늘린다(최대 100) |
| `costLimits` | 일(UTC)·월(UTC) 알림과 차단 기준(USD). 바꿀 값만 보내고 `null`은 그 기준을 제거한다. 알림 기준은 차단 기준 이하로 둔다 |
| `displayName`, `description`, `departmentCode` | 목록·검색·비용 집계에 보인다 |
| `visibility` | 새 Agent는 항상 private이다. `public` 전환은 `StudioUpdateAgent`로 하며 조직 전체에 Agent와 프롬프트를 공개하므로 사용자가 요청할 때만 바꾼다. Helper로 지정된 Agent는 public으로 바꿀 수 없다 |

| `parameters` 키 | 효과 |
|---|---|
| `temperature`, `maxTokens`, `presencePenalty`, `reasoningEffort` | 생성 방식 |
| `structuredOutput`, `jsonSchema` | JSON Schema 출력 강제 |
| `urlFetch` | `FetchUrl`로 외부 주소 읽기. 접근 범위가 넓어지므로 이유를 설명한다 |
| `slackWorkspace` | 활성 Slack 봇 권한으로 Slack 기록 읽기 |
| `imageGeneration`, `imageModel` | `GenerateImage`·`EditImage` 제공 |
| `dynamicCapabilities` | 요청마다 맞는 Skill·MCP 도구를 찾아 추가한다. 등록된 Embedding 모델이 필요하다 |
| `memoryRecall` | 실행 전 자동 회상. `agent-memory`를 `mcpList`에 명시적으로 연결하고 `recall`을 허용해야 한다. 동적 탐색만으로는 자동 회상이 되지 않는다 |
| `memoryCapture` | 로그인한 사용자가 시작한 실행이 끝나면 요청과 답변을 Memory의 `memory_capture`로 보내 단기 기억으로 남긴다. 명시적으로 연결한 Memory 서버가 `memory_capture`를 허용해야 한다. 실패는 로그에만 남는다 |
| `modelRouting` | 설정의 자동 모델 라우팅 정책 사용 |
| `reasoningTrace` | 화면에 모델 추론 과정 표시 |
| `callerContext`, `piiFiltering` | 호출자 정보 전달, 인식된 PII 패턴 치환(완전한 익명화가 아님) |
| `policy` | `maxInputChars`, `blockedTools`, `approvalTools`. 전달하면 정책 전체를 교체한다 |
| `studioTools` | 그 Agent에 Studio 관리 권한을 준다. 사용자가 명시적으로 요청할 때만 켠다. 승인 화면에 경고가 표시된다 |

## 서비스 연결

일반 Agent가 Agent 서비스를 쓰려면 그 서비스의 Tools 항목을 `mcpList`에 연결한다. Helper만 서비스가 자동 연결된다.

| 목적 | 연결 | 함께 연결할 Skill(있으면) |
|---|---|---|
| 기억 회상·저장, 작업 인계 | `agent-memory` | — |
| 문서 검색·수집, 지식 그래프 | `agent-knowledge` | `workspace-search`, `personal-records` |
| 녹음 전사·회의록 | `agent-knowledge` | `audio-processing`, `meeting-minutes` |
| 코드·파일 작업, 저장소 생성, PR | `agent-forge` | `workspace-task`, `sandbox-task` 등 |
| 앱 리소스·배포 | `agent-delivery`와 `agent-forge` | `app-delivery` |

연결은 접근을 열 뿐 권한을 만들지 않는다. 서비스 도구는 호출한 사용자의 권한으로 실행되며, 사용자는 각 서비스에서
필요한 준비(예: Forge의 GitHub 연결과 Workspace profile)를 마쳐야 한다. 준비 절차는 [journeys](journeys.md)를 따른다.

## 모델

Agent Models가 공급자 연결·승인된 모델 선택·라우팅·사용량을 소유한다. Studio는 승인된 목록을 읽기만 한다.

- 새 모델이 필요하면 Agent Models 관리자가 공급자를 등록하고 모델을 선택해야 한다. Helper는 이 작업을 할 수 없다.
- `/models`는 모든 사용자가 등록된 모델의 기능·문맥·가격을 보는 페이지다. `/settings/models`는 관리자에게 Agent Models
  콘솔 링크를, `/settings/model-usage`는 기본·결정·Embedding·Rerank 역할과 라우팅 정책을 보여 준다.
- 설정에는 모델 `id`를 쓴다. 가격이 비어 있으면 미지정이며 무료라는 뜻이 아니다.

## Trigger와 메신저 연동

- 정기 실행은 `StudioSaveTrigger(mode="create", kind="schedule", cron, timezone, message)`로 만든다. cron은 다섯 필드,
  timezone은 IANA 이름(예: `Asia/Seoul`)이다. 결과를 메신저로 보내려면 `deliveries`에 플랫폼별 대상 하나씩을 넣는다.
- 기존 trigger는 `StudioRead(resource="triggers", name=...)`로 읽고 `mode="update"`로 바꿀 필드만 보낸다.
- webhook trigger 호출 권한은 사용자의 개인 webhook token이 정한다.
- Slack·Telegram·Teams의 활성화, Slack 추천 프롬프트·채널 키워드, Teams tenant는 `StudioUpdateIntegration`으로 바꾼다.
  현재 상태는 `StudioRead(resource="integrations", name=...)`로 읽는다. 활성화에는 저장된 credential이 필요하다.
  Telegram 활성화에는 배포의 공개 기본 URL이 필요하다.
- 일정 실행 성공과 메신저 전달 성공은 다르다. 결과는 Trace와 대상 채널에서 확인한다.

## 비밀 값

bot token, signing secret, app password, MCP header 값, MCP OAuth 연결, 개인 API·webhook token은 대화로 받지 않는다.

1. `StudioRequestCredential`이 있으면 호출한다. `kind`는 `slack`·`telegram`·`teams`·`mcpHeader`(`server`, `header` 필요)·
   `mcpOAuth`(`server` 필요)·`apiToken`·`webhookToken` 중 하나다. 사용자가 승인 카드에서 입력하거나 연결·발급한다.
2. 결과의 `completed`가 false이면 저장되지 않았다고 알린다. 값은 결과에 없으며 묻지 않는다.
3. 이미 설정된 값을 교체하거나 token을 다시 발급하면 기존 값이 폐기되어 기존 연동이 끊긴다. 호출 전에 이 영향을 설명한다.
4. 도구가 없으면 입력 화면을 안내한다.

| 비밀 값 | 입력 화면 |
|---|---|
| MCP header 값 | Agent 화면(`/agents/<name>`)의 MCP 서버 설정 |
| MCP OAuth 연결, Slack·Telegram·Teams credential, 개인 API·webhook token | 연동 화면(`/agents/<name>/integrations`) |
| Runway 앱 secret | Runway 콘솔. [delivery](delivery.md#secret) |

MCP OAuth 연결은 사용자·MCP 서버 단위이며 여러 Agent가 함께 쓴다. Agent 서비스(`agent-*` Tools)는 OAuth 연결 없이
Studio 로그인으로 위임된다.

## 전용 Skill

공유 Skill로 해결할 수 없는 그 Agent만의 반복 절차·판단 기준·참고 자료가 있을 때 만든다.
상시 적용할 역할과 말투는 시스템 프롬프트에 둔다.

1. `StudioRead(resource="skills")`로 비슷한 공유 Skill이 있는지 확인한다.
2. `skill-writer`가 연결돼 있으면 읽고 description과 본문을 작성한다.
3. 이름은 `<agentName>--<용도>`다. `<용도>`는 `--`가 없는 slug다. 예: `review-agent--checklist`.
4. `StudioSaveSkill(agentName, name, description, content, expectedUpdatedAt=null)`을 호출한다. 새 Agent의 Skill은
   `StudioCreateAgent` 결과를 받은 다음 턴에 저장한다. 긴 표·템플릿은 `files`의 참고 파일로 나눈다.
   새 Skill은 해당 Agent에 자동으로 연결된다.
5. 고칠 때는 `StudioRead(resource="skill", name=...)`로 본문과 `updatedAt`을 읽고 `expectedUpdatedAt`과 함께 저장한다.
   `files`를 생략하면 기존 참고 파일을 유지한다.
6. 쓰지 않는 전용 Skill은 `StudioDeleteSkill`로 연결 해제와 삭제를 함께 한다.

전용 Skill은 소유 Agent에만 연결되고 그 Agent에 접근할 수 있는 사용자만 읽는다. 다른 Agent의 전용 Skill은
연결할 수 없다. 공유·Plugin Skill은 관리자와 Plugin 원본이 관리하므로 Helper로 수정하지 않는다.
