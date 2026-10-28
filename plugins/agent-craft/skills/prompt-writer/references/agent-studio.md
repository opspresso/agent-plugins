# 호스트 앱과 Agent Memory 설정

이 제품 조합을 구성할 때만 읽는다. 설치된 버전의 schema와 제공 기능을 먼저 확인한다.

## 기억을 쓰는 에이전트의 프롬프트

기억을 지속적으로 쓰는 에이전트에는 조회·저장 시점과 공유 범위를 적는다. 아래 예시는
Agent Memory의 `remember`·`recall`·`revise`·`forget` 계약이다. 배포된 서버의 실제 schema를 먼저
확인하고 없는 도구를 호출하게 만들지 않는다.

**동작 규칙**에는 필요한 항목을 넣는다.

```
- 이전 결정·선호는 Agent Memory의 recall로 찾는다. 조직 문서와 Graph는 Agent Knowledge의 context_search로 찾는다.
- recall은 Memory만 검색한다. 결과에는 기억 ID·버전과 본문·출처·scope가 함께 있다.
  검색 결과가 없다는 것을 자료가 전혀 없다는 뜻으로 해석하지 않는다.
- 다음 작업에도 유효한 사실은 저장 권한과 공유 범위를 확인하고 remember로 저장한다.
  kind, scope, title, content, source를 실제 schema에 맞춰 전달한다.
  idempotencyKey가 제공되면 같은 저장 요청의 키와 입력을 유지한다. 키 없는 신규 생성의
  응답이 불확실할 때 같은 내용을 무조건 다시 저장하지 않는다.
- scope.kind는 organization, team, user 중 요청에 맞게 명시한다.
  개인·팀 범위가 거부되면 조직 전체에 대신 저장하지 않는다. 대화 전용 scope는 없다.
- 기억의 일부가 틀리면 recall 결과의 memory ID와 version으로 revise(memoryId, expectedVersion, title?, content?)를 호출한다.
  기억 전체를 새 사실로 바꿀 때는 remember의 supersedes에 이전 기억의 ID와 version을 넣는다.
- 잊기 요청은 실제 조회·저장 결과의 memory ID와 현재 version을 확인한 뒤
  forget(memoryId, expectedVersion, changeReason?)으로 처리한다.
  성공은 archive이며 원문·revision의 영구 삭제가 아니다.
- 권한 오류나 version 충돌을 성공으로 보고하지 않는다. 충돌은 최신 기억을 다시 확인하고
  사용자가 허가한 대상과 여전히 일치할 때만 재시도한다.
- 기억의 출처·유효 기간을 확인한다. 파일·설정·이름은 현재 상태와 대조한다.
```

Agent Memory와 Agent Knowledge는 설치 측에서 서로 다른 MCP로 등록한다. 실제 런에 제공되지 않으면 기억
조회·저장을 약속하지 않고 현재 대화의 자료로 진행한다. Agent Knowledge의 `document_search`는 처리된
문서 chunk, `knowledge_search`·`knowledge_neighborhood`는 그래프 근거를 찾는다.
Agent Knowledge의 문서 수집 도구가 제공되면 `document_ingest`로 개인·팀·조직 scope의 텍스트를 저장하고
`document_ingest_status`로 ready를 확인한다. 수집에는 idempotencyKey가 필수이며 접수와
처리 완료를 구분한다. 문서 수집 도구가 제공되지 않으면 Agent Knowledge 관리 화면이나 API를 사용한다.
기억 본문 수정은 Memory의 `revise` 도구나 관리 화면, Graph 작성은 Agent Knowledge의 관리 화면이나 API에서 수행한다.
검색 결과의 문서 ID는 호스트 앱의 `File` artifact ID가 아니다.

`recall`의 text에는 ID와 version이 있지만 항목당 1,200자·전체 4,000자로 잘린다.
호스트 앱이 전달하지 않은 `structuredContent.hits`를 읽었다고 가정하지 않는다.
`forget`의 version을 1로 고정하거나 제목만 보고 ID를 만들지 않는다.

자동 회상을 원하면 버전의 `memoryRecall`을 켜고 별도 등록한 서버를 명시적으로 binding하며
허용 도구에 `recall`을 포함한다. 요청별 동적 발견만으로는 실행 전 자동 recall이 되지 않는다.

Studio는 정확히 설정된 service URL에 현재 caller의 짧은 signed delegation을 전달한다.
Memory/Agent Knowledge는 issuer·subject의 명시적 로컬 사용자 binding과 현재 멤버십을 검사한다.
`X-User-Email`·display email·같은 UUID는 사용자 권한의 근거가 아니다. 모델이 email·tenant·owner
인자를 만들어 권한을 바꾸지 않으며 자격 증명은 설치 측에서 관리한다.
사용자 scope는 인증 사용자, team scope는 확인된 teamId를 쓰고 조직 전체 공유를 기본값으로 삼지 않는다.

## 모델 설정을 함께 정할 때

현재 호스트 앱에서 선택 가능한 모델과 필요한 능력(tool use·vision·이미지 생성 등)을
먼저 확인한다. `agent-models`는 모델·provider offering 카탈로그이며 MCP 서버가 아니다.
가격과 모델 목록을 프롬프트에 복사해 고정하지 않는다. 서비스의 공개 연결 ID와 catalogId·wireId는 다르다. 미지정 가격은 unknown이고 명시된 0만 무료다. 버전 설정에는 카탈로그의 `id`를
쓰고 provider 전송용 `wireId`와 혼동하지 않는다. `hidden` 모델을 새 기본값으로 권하지
않고 embedding·rerank·transcription 모델을 일반 대화 모델로 선택하지 않는다.

단기 작업 인수인계는 Memory의 handoff_create/list/get/update/close를 명시적으로 연결한다. 목표·진행·다음 할 일·blocker와 metadata 참조를 전달하며 native Session이나 checkpoint는 Forge가 보존한다. 만료·종료된 handoff를 진행 중 작업으로 취급하지 않는다.
