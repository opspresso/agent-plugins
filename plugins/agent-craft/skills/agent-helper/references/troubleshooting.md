# 문제 해결

사용자가 오류·실패·"동작하지 않음"을 말할 때 읽는다. 추측으로 설정을 바꾸지 않는다. 근거를 읽고 원인을 좁힌 뒤,
고칠 수 있으면 승인 후 고치고, 사용자나 관리자가 해야 하면 정확한 위치와 조치를 알린다.

## 진단 순서

1. **증상과 위치.** 어느 서비스·페이지·Agent·Chat에서, 어떤 오류 문구와 함께 일어났는지 확인한다.
   화면 자료가 있으면 먼저 읽는다. 오류 코드와 메시지는 그대로 인용한다.
2. **근거 읽기.** Agent 실행 문제는 Trace(`/agents/<name>/traces`), 설정은 `StudioRead`, 서비스 작업은 해당 서비스의
   조회 도구(`run_get`·`project_status`·`deployment_get`·`deployment_logs`·`audio_status`·`document_ingest_status`)를 읽는다.
3. **분류.** 설정 누락, 권한·연결 누락, 사용자 작업 대기(승인·secret·OAuth), 한도, 운영 장애 중 무엇인지 정한다.
4. **조치.** 설정 문제는 승인 후 변경하고, 대기 작업은 콘솔 페이지를 열어 주고, 운영 장애는 관리자에게 전달할 정보를 정리한다.
5. **확인.** 고친 뒤 같은 요청을 다시 시도하게 하거나 상태를 다시 읽는다. 확인하지 못했으면 미확인으로 보고한다.

## Studio

| 증상 | 확인 | 해결 |
|---|---|---|
| Agent가 도구·Skill을 안 씀 | `StudioRead(resource="agent")`의 `skillList`·`mcpList`·`tools`, Trace의 도구 호출 | 연결·도구 선택을 고친다. 프롬프트에 사용 조건을 적는다 |
| 바꾼 설정이 반영 안 됨 | Playground 저장 여부, `updatedAt` | 초안은 저장해야 실행에 쓰인다. 진행 중 실행은 시작 시점 설정을 쓴다 |
| MCP 도구 호출이 인증 오류 | `/tools/<name>`의 OAuth 연결 상태, Agent의 MCP header 설정 | `StudioRequestCredential(kind="mcpOAuth"|"mcpHeader")` |
| 모델을 선택할 수 없음 | `StudioRead(resource="models")` | 목록에 없으면 Agent Models 관리자가 모델을 선택해야 한다 |
| "cost limit"·실행 차단 | Agent `costLimits`, 사용자 tier 한도(`/profile`) | Agent 한도는 소유자가 바꾼다. tier 한도는 관리자(`/settings/access`)가 바꾼다 |
| 턴·출력 제한으로 답이 끊김 | Trace의 종료 이유 | `maxTurn`·`maxTokens`를 늘리거나 작업을 나눈다 |
| Slack·Telegram·Teams 무응답 | `StudioRead(resource="integrations")`의 활성화·credential 상태, Trace | credential을 다시 받고 활성화한다. Slack은 이벤트 URL, Teams는 messaging URL 설정을 확인하게 한다 |
| schedule이 실행 안 됨 | `StudioRead(resource="triggers")`의 `enabled`·cron·timezone | 외부 schedule ticker가 동작해야 한다. 없으면 운영자 문제다 |
| 서비스 작업 결과가 Chat에 안 옴 | 해당 서비스의 상태 도구 | 결과 전달도 schedule tick이 한다. 서비스에서 끝났는데 안 오면 운영자에게 알린다 |
| 승인 카드가 안 보임·거절됨 | Chat의 승인 대기 | 승인은 사용자만 한다. 거절된 변경은 반복하지 않는다 |
| Helper 화면 조작 실패 | 화면 공유 켜짐 여부, 같은 탭 여부 | 다시 inspect한다. 다른 탭·만료된 요청은 새 요청이 필요하다 |

## 서비스

| 증상 | 서비스 | 확인과 해결 |
|---|---|---|
| 서비스 도구가 없음 | 전체 | 배포에 연결되지 않았거나 사용자가 쓸 수 없다. `/tools`에 항목이 있는지 확인한다. guest는 쓰기 도구를 쓸 수 없다 |
| `403 Studio policy refused this request` | 전체 | guest·계정 없음·비용 한도 등 Studio 정책 거절이다. 재시도로 해결되지 않는다 |
| 401 (`Studio authorization required` 등) | 전체 | 다시 로그인하고 요청을 다시 시도한다 |
| `reauthorization_required` (403) | Forge | 이전 위임으로 접수된 Run은 계속할 수 없다. 새 Run을 제출한다 |
| GitHub 관련 403 | Forge | [forge](forge.md#오류) — `/git`에서 연결·저장소 등록 |
| Git merge 승인 대기·만료 | Forge | [forge](forge.md#오류) — 승인은 Run 제한 시간과 함께 만료된다 |
| 배포 실패 | Runway | `deployment_get`의 `errorCode`와 `deployment_logs`. [delivery](delivery.md#오류) |
| `environment_not_ready` | Runway | secret 입력 링크와 리소스 `ready` 확인 |
| 문서 처리 멈춤·실패 | Knowledge | [knowledge](knowledge.md#오류) |
| 녹음 작업 결과 불명 | Knowledge | `audio_request_status`로 영수증 확인. 다시 제출하지 않는다 |
| 기억 검색이 안 맞음 | Memory | [memory](memory.md#오류) |

## 응답이 유실됐거나 결과가 불확실할 때

- 같은 요청을 새로 보내지 않는다. 같은 키로 조회한다: `run_lookup_request`·`workspace_lookup_request`·`repository_lookup_request`(Forge),
  `deployment_lookup_request`(Runway), `audio_request_status`·`recording_delete_status`(Knowledge), `remember`·`handoff_create`의 같은 `idempotencyKey`(Memory).
- Studio 변경 도구가 실패하거나 시간 초과되면 `StudioRead`로 저장 상태를 먼저 확인한다.
- Forge `interrupted` Run은 자동으로 다시 실행하지 않는다. 결과를 확인하고 사용자에게 다음 행동을 묻는다.

## 관리자에게 넘길 때

운영자만 고칠 수 있는 문제(서비스 장애, 모델 미등록, 문서 worker 정지, schedule ticker 없음, 소유권 이전)는
서비스·시각·오류 코드·관련 ID(Agent 이름, Run·Runway·문서 ID)를 한 번에 정리해 준다. 비밀 값은 넣지 않는다.
