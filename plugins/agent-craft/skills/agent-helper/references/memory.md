# Agent Memory

기억을 찾거나 남기거나 고칠 때, 작업 인계(handoff)를 다룰 때, Memory 화면을 안내할 때 읽는다.
실제 도구 schema와 서버 instructions가 이 문서보다 우선한다.

## 개념

- **기억(memory)**: 다음 세션에 필요한 문장 하나다. `kind`는 `rule`(사용자가 정한 규칙·선호·결정)·`fact`(환경·프로젝트의 확인된 사실)·`lesson`(실패에서 배운 것)이다.
  `scope`는 `user`·`team`·`organization`이다.
  - `repository`(`owner/repo`)를 지정한 기억은 그 저장소 작업에서만 나타난다.
  - **주제**: 기억은 범위마다 제품·프로젝트·작업 절차 같은 주제에 들어간다. 큰 주제는 section으로 나뉜다. 주제 없이 저장한 기억은 수집함(inbox)에 있고 Dreaming이 분류한다.
  - `expiresAt`을 지정한 기억은 그 시각이 지나면 회상에서 빠지고 다음 Dreaming이 휴지통으로 옮긴다.
  - 모든 변경은 version을 남긴다. `forget`은 휴지통으로 옮기며, 사람이 AgentOps 화면에서 30일 동안 복원할 수 있다.
- **handoff**: 끝나지 않은 작업의 `goal`·`summary`·`nextActions`·`blockers`·`references`. 기본 7일, 최대 30일 유지되고 닫으면 다시 열 수 없다.
- **Dreaming**: 일정에 따라 실행되는 기억 정리. 만료된 기억을 휴지통으로 옮기고, 세션 기록에서 기억을 모으고, 수집함의 기억을 주제에 넣고,
  같은 내용의 기억을 합친다. 지운 기억은 휴지통으로 가며 복원할 수 있다.

## Helper가 쓸 수 있는 도구

Studio 위임 token은 `memory:read`·`memory:write`·`handoff:read`·`handoff:write`만 가진다. 영구 삭제(`forget`의 `permanent`, `handoff_delete`)는 없다.

| 도구 | 용도 | 주의 |
|---|---|---|
| `recall` | 질문에 답하는 기억 검색. 결과에 ID·version·kind·topic이 있다 | 읽기 전용. 결과 없음은 기억이 없다는 증거가 아니다. 잘린 본문은 고치기 전에 `memory_get`으로 전체를 읽는다 |
| `memory_get` | 기억 하나의 전체 본문과 변경 이력 | 읽기 전용 |
| `memory_topic` | 인자 없이 주제 색인, `topic`(주제 slug·ID 또는 section slug)으로 그 주제의 설명·section·기억 | 읽기 전용. 한 주제의 작업 전에 그 주제를 읽는다. 큰 주제는 작업에 해당하는 section을 읽는다 |
| `remember` | 기억 저장 | 사용자가 저장을 요청할 때만. `kind`·`title`·`content`와 필요하면 `scope`·`repository`·`topic`을 정한다. 결과의 `outcome`이 `existing`이면 같은 내용이 이미 있으므로 다시 저장하지 않는다. 기존 기억을 새 문장으로 바꿀 때는 `replaces`에 그 ID를 넣는다. 그 기억은 같은 작업으로 휴지통에 간다. `related`가 오면 `revise`나 `replaces`로 정리할지 검토한다 |
| `revise` | 기억의 `kind`·`title`·`content`·`repository`·`topic` 변경 | `memoryId` 필요. `expectedVersion`을 보내면 낡은 version일 때 저장하지 않는다. `content`는 전체 새 본문이어야 한다. 휴지통의 기억은 고칠 수 없다 |
| `forget` | 기억을 휴지통으로 옮긴다 | 복원은 사람이 `/memory/memories`에서 한다 |
| `dream` | 개인 Dreaming 시작(`action: start`)이나 최근 실행 조회(`action: status`) | 사용자가 지금 실행이나 최근 결과를 물을 때만. 실행은 background에서 계속되므로 완료를 기다리지 않는다 |
| `handoff_create`·`handoff_list`·`handoff_get`·`handoff_update`·`handoff_close` | 작업 인계 | 생성은 `idempotencyKey` 필수, 갱신·닫기는 `expectedVersion` 필요 |

`memory_capture`는 Studio 런타임 전용이다. Helper가 호출하지 않는다.

권한 규칙: `user` scope는 본인만, `team`은 팀 구성원, `organization` 쓰기는 조직 admin만 할 수 있다.
개인·팀 저장이 거절되면 조직 범위로 바꿔 저장하지 않는다. 쓰기 권한이 없는 사용자 등급은 쓰기를 할 수 없다.

## 화면

| 경로 | 용도 |
|---|---|
| `/memory` | 개요. 기억 검색, 활성·수집함·휴지통 기억 수, 큰 주제, 최근 Dreaming, 열린 작업 인계 |
| `/memory/memories`, `/memory/memories/<memoryId>` | 기억 목록·필터·작성·편집, 수집함, 휴지통과 복원, 기억마다 변경 이력 |
| `/memory/topics`, `/memory/topics/<topic>` | 주제 색인, 주제 하나의 설명과 기억, 주제 수정 |
| `/memory/handoffs`, `/memory/handoffs/<handoffId>` | 작업 인계 목록과 상세 |
| `/memory/dreams` | Dreaming 일정, 최근 실행 결과와 복원, 사용자의 세션 기록 |
| `/guide/connect` | MCP 주소와 코딩 클라이언트(Claude Code 등) 연결 방법 |
| `/profile/clients` | 코딩 클라이언트 token(Memory 개인 token) 발급·폐기 |
| `/settings/memory/<section>` | 관리자 전용 Memory 설정. section은 `general`·`ai`·`auth`·`observability` |

사람이 화면에서 하는 작업: 휴지통 복원, 일괄 이동·복원, Dreaming 결과 복원, 개인 token 발급·폐기, 영구 삭제, 주제 수정, Memory 설정.
token 값과 영구 삭제 확인은 Helper가 읽거나 누를 수 없다. 코딩 클라이언트 연결 승인 화면(`/memory/connect/cli`)은 연결 명령이 연 일회용 화면이므로 Helper가 열지 않는다.

## 자주 하는 요청

- **"이거 기억해 줘"**: 규칙·사실·교훈을 한 기억에 하나씩 `remember`한다. 기본 scope는 `user`다. 팀·조직 공유는 사용자가 요청할 때만 쓴다.
- **"내 기억을 찾아 줘"**: `recall`로 찾고 출처와 시점을 함께 보여 준다. 목록 화면이 필요하면 `/memory/memories`로 이동한다.
- **"Agent가 나를 기억하게 해 줘"**: 해당 Agent의 `mcpList`에 `agent-memory`를 연결하고 `memoryRecall`(필요하면 `memoryCapture`)을 켠다. [agent-settings](agent-settings.md#설정-선택)
- **"Claude Code에 Memory 연결"**: `/guide/connect`를 연다. 설치 명령과 브라우저 승인 절차가 그 화면에 있다. 발급한 token은 `/profile/clients`에서 관리한다.

## 오류

| 증상 | 원인과 해결 |
|---|---|
| version 충돌(`revise`·`forget`·handoff 갱신) | 읽은 version이 낡았다. 다시 읽고 사용자가 원한 대상과 같을 때만 재시도한다 |
| `remember`·`handoff_create` 응답 유실 | 같은 `idempotencyKey`로 다시 보낸다. 키 없이 새로 저장하지 않는다 |
| `Studio policy refused this request` | 사용자 등급·계정·비용 한도 등 Studio 정책 거절. 재시도해도 성공하지 않는다 |
| `Studio identity is temporarily unavailable` | Studio 인증 일시 장애. 안내된 시간 뒤 재시도한다 |
| `Agent Memory needs a new sign-in; sign in to the AgentOps console again` | Memory가 쓰는 사용자의 Studio 로그인이 끝났다. 사용자가 AgentOps에 다시 로그인한 뒤 요청을 다시 시도한다 |
| 검색이 잘 안 맞음 | `recall`은 단어 하나만 맞아도 후보로 삼고 맞는 단어가 많을수록 순위가 높다. Embedding 모델이 없으면 의미 검색 없이 키워드로만 찾는다. 관리자에게 `/settings/memory/ai` 설정을 요청한다 |
| 기억이 회상에 나오지 않음 | `expiresAt`이 지났거나 휴지통에 있다. `/memory/memories`에서 상태를 확인하고 필요하면 사용자가 복원한다 |
