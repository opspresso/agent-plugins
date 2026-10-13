# 직접 Forge HTTP/MCP를 사용할 때

이 문서는 독립 Forge 도구가 실제로 발견된 클라이언트용이다. Studio의 `Workspace`
wrapper가 제공되면 그 wrapper의 options/start/run/status 계약을 사용한다.
서비스 endpoint와 현재 사용자 credential은 클라이언트 설정에 있어야 한다. 조직·owner·email
인수를 만들어 신원을 바꾸거나 모델 지시에 토큰을 넣지 않는다.

## 접수와 관측

| Forge MCP 도구 | HTTP 경계 | 역할 |
|---|---|---|
| `workspace_create` | `POST /v1/workspaces` | 작업 공간 접수. 명령을 실행하지 않음 |
| `workspace_lookup_request` | `GET /v1/workspaces/by-request-key?key=...` | 생성 receipt 읽기 |
| `run_submit` | `POST /v1/workspaces/:id/runs` | 명령·native 작업·Git 작업 접수 |
| `run_lookup_request` | `GET /v1/workspaces/:id/runs/by-request-key?key=...` | 실행 receipt 읽기 |
| `run_get`, `run_events` | Run 상태·events 조회 | 실행하지 않고 결과를 관측 |
| `run_cancel` | `POST /v1/runs/:id/cancel` | 실행 취소 요청 |
| `workspace_suspend/resume/close` | 동일 이름의 수명 관리 endpoint | checkpoint와 실행 자원 관리 |
| `model_channels` | `GET /v1/model-channels` | 현재 caller에게 허용된 채널만 조회 |

MCP `requestKey`는 HTTP `Idempotency-Key`에 대응한다. 같은 키·입력은 같은 접수이며
다른 입력의 재사용은 충돌이다. 응답이 유실되면 같은 caller·키의 읽기 receipt를 확인한다.
null은 확인된 부재이고 통신 오류는 부재가 아니다. 부재가 확인되고 현재 권한이 유효할 때만
같은 입력·키로 접수한다. 불명확한 실행을 새 키로 반복하지 않는다.

`queued/running`은 완료가 아니다. `run_events`의 `nextCursor`로 다음 페이지를 읽고
terminal 상태와 `hasMore:false`를 함께 확인한다. `outputLoss:true`는 영구 출력 유실이다.
`interrupted`는 실행 효과를 확정하지 못한 상태이며 자동 재실행하지 않는다. 모델·Git 결과와
원격 저장소 상태를 확인하기 전에 게시를 반복하지 않는다.

일반 `command`는 모델 없이 실행한다. native 작업은 발견한 허용 채널의 id와 runtime을
사용하며 provider wire ID·endpoint·장기 키를 직접 고르지 않는다. Workspace당 실행은 한 번에
하나이고, 연결이 끊겨도 접수된 작업은 유지된다. run timeout은 대기·준비·검사까지 포함한다.

## 소유권과 재개

Memory handoff는 목표·진행·다음 할 일·참조를 전달한다. 실제 native Session과 파일 checkpoint는
Forge가 유지한다. Studio의 원래 Chat 재개와 GitHub PR·merge·release·배포는 Studio가 조율한다.
직접 Forge가 대화를 자동 재개하거나 PR을 만들 것이라고 약속하지 않는다.
