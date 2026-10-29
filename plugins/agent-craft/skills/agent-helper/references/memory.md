# Agent Memory

기억을 찾거나 남기거나 고칠 때, 작업 인계(handoff)를 다룰 때, Memory 콘솔을 안내할 때 읽는다.
실제 도구 schema와 서버 instructions가 이 문서보다 우선한다.

## 개념

- **기억(memory)**: `kind`는 `rule`·`experience`·`decision`·`preference`·`fact`다. `scope`는 `user`·`team`·`organization`이다.
  - `term=long`: 지속 기억. `term=short`: 개인 전용이며 14일 뒤 만료된다. 야간 정리(Dreaming)가 장기 기억으로 올릴 수 있다.
  - `repository`(`owner/repo`)를 지정한 기억은 그 저장소 작업에서만 나타난다.
  - 모든 변경은 version을 남긴다. `forget`은 보관(archive)이며 영구 삭제가 아니다.
- **handoff**: 끝나지 않은 작업의 `goal`·`summary`·`nextActions`·`blockers`·`references`. 기본 7일, 최대 30일 유지되고 닫으면 다시 열 수 없다.
- **Dreaming**: 계정별 야간 정리. 만료 단기 기억 보관, 주제별 병합, 장기 승격을 한다.

## Helper가 쓸 수 있는 도구

Studio 위임 token은 `memory:read`·`memory:write`·`handoff:read`·`handoff:write`만 가진다. 영구 삭제 도구는 없다.

| 도구 | 용도 | 주의 |
|---|---|---|
| `recall` | 접근 가능한 기억 검색. 결과에 ID와 version이 있다 | 읽기 전용. 결과 없음은 기억이 없다는 증거가 아니다 |
| `remember` | 기억 저장 | 사용자가 저장을 요청할 때만. `kind`·`title`·`content`·`scope`를 정한다. 결과가 `reinforced`면 같은 내용이 이미 있으므로 다시 저장하지 않는다. 기억 전체를 새 사실로 바꿀 때는 `supersedes`에 이전 기억의 ID·version을 넣어 같은 작업으로 보관한다 |
| `revise` | 새 version 저장(제목·본문·저장소), `term:"long"`으로 승격 | `recall`로 읽은 `memoryId`·`expectedVersion` 필요. `content`를 보내면 전체 새 본문이어야 한다 |
| `forget` | 기억 보관 | 읽은 version 필요. 복원은 콘솔에서 한다 |
| `handoff_create`·`handoff_list`·`handoff_get`·`handoff_update`·`handoff_close` | 작업 인계 | 생성은 `idempotencyKey` 필수, 갱신·닫기는 `expectedVersion` 필요 |

`memory_capture`는 Studio 런타임 전용이다. Helper가 호출하지 않는다.

권한 규칙: `user` scope는 본인만, `team`은 팀 구성원, `organization` 쓰기는 조직 admin·owner만 할 수 있다.
개인·팀 저장이 거절되면 조직 범위로 바꿔 저장하지 않는다. guest는 쓰기를 할 수 없다.

## 콘솔 페이지 (`agent-memory`)

| 경로 | 용도 |
|---|---|
| `/` | 기억 검색 |
| `/memories` | 기억 목록·편집·보관·복원·version 기록. 필터는 URL에 남는다 |
| `/handoffs` | 작업 인계 목록 |
| `/dreams` | 야간 정리 결과, 개인 정리 실행, 복원 |
| `/connect` | 코딩 Agent(Claude Code·Codex)·MCP 클라이언트 연결과 개인 token 발급 |
| `/onboarding`, `/profile`, `/guide` | 첫 사용 설정, 계정 정보, 사용법 |
| `/members`, `/teams`, `/settings` | 관리자 전용. 팀 삭제는 그 팀 범위의 기억과 인계를 영구 삭제한다 |

콘솔 전용 작업: 보관된 기억 복원, 일괄 보관·복원, Dreaming 실행·복원, 개인 token 발급·폐기, 공유 대상(grant) 편집,
영구 삭제, 회원·팀·AI 모델 설정.

## 자주 하는 요청

- **"이거 기억해 줘"**: 사실·선호·결정을 한 기억에 하나씩 `remember`한다. 기본 scope는 `user`다. 팀·조직 공유는 사용자가 요청할 때만 쓴다.
- **"내 기억을 찾아 줘"**: `recall`로 찾고 출처와 시점을 함께 보여 준다.
- **"Agent가 나를 기억하게 해 줘"**: 해당 Agent의 `mcpList`에 `agent-memory`를 연결하고 `memoryRecall`(필요하면 `memoryCapture`)을 켠다. [agent-settings](agent-settings.md#설정-선택)
- **"Claude Code에 Memory 연결"**: `/connect`를 연다. 설치 명령과 브라우저 승인 절차가 그 페이지에 있다.

## 오류

| 증상 | 원인과 해결 |
|---|---|
| `409` (revise·forget·handoff 갱신) | 읽은 version이 낡았다. 다시 읽고 사용자가 원한 대상과 같을 때만 재시도한다 |
| `remember`·`handoff_create` 응답 유실 | 같은 `idempotencyKey`로 다시 보낸다. 키 없이 새로 저장하지 않는다 |
| `403 Studio policy refused this request` | guest·계정 없음·비용 한도 등 Studio 정책 거절. 재시도해도 성공하지 않는다 |
| `Studio identity is temporarily unavailable` | Studio 인증 일시 장애. 안내된 시간 뒤 재시도한다 |
| 검색이 잘 안 맞음 | `recall`은 단어 하나만 맞아도 후보로 삼고 맞는 단어가 많을수록 순위가 높다. Embedding 모델이 없으면 의미 검색 없이 키워드로만 찾는다. 관리자에게 `/settings?section=ai` 설정을 요청한다 |
| 단기 기억이 사라짐 | 14일 만료. 유지하려면 `revise(term:"long")` 또는 콘솔에서 장기 기억으로 유지한다 |
