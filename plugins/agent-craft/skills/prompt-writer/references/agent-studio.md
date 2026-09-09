# Agent Studio와 Agent Memory 설정

이 제품 조합을 구성할 때만 읽는다. 설치된 버전의 schema와 제공 기능을 먼저 확인한다.

## 기억을 쓰는 에이전트의 프롬프트

기억을 지속적으로 쓰는 에이전트에는 조회·저장 시점과 공유 범위를 적는다. 아래 예시는
Agent Memory의 `remember`·`recall`·`forget` 계약이다. 배포된 서버의 실제 schema를 먼저
확인하고 없는 도구를 호출하게 만들지 않는다.

**동작 규칙**에는 필요한 항목을 넣는다.

```
- 이전 결정·선호는 recall로 찾는다. 조직 문서와 Graph를 함께 찾으려면 context_search를 쓴다.
- recall은 Memory만 축약해서 반환한다. 상세 본문·출처·scope가 필요하면 context_search로
  해당 기억을 확인한다. 검색 결과가 없다는 것을 자료가 전혀 없다는 뜻으로 해석하지 않는다.
- 다음 작업에도 유효한 사실은 저장 권한과 공유 범위를 확인하고 remember로 저장한다.
  kind, scope, title, content, source를 실제 schema에 맞춰 전달한다.
  remember는 신규 생성이므로 응답이 불확실할 때 같은 내용을 무조건 다시 저장하지 않는다.
- scope.kind는 organization, team, user 중 요청에 맞게 명시한다.
  개인·팀 범위가 거부되면 조직 전체에 대신 저장하지 않는다. 대화 전용 scope는 없다.
- 잊기 요청은 실제 조회·저장 결과의 memory ID와 현재 version을 확인한 뒤
  forget(memoryId, expectedVersion, changeReason?)으로 처리한다.
  성공은 archive이며 원문·revision의 영구 삭제가 아니다.
- 권한 오류나 version 충돌을 성공으로 보고하지 않는다. 충돌은 최신 기억을 다시 확인하고
  사용자가 허가한 대상과 여전히 일치할 때만 재시도한다.
- 기억의 출처·유효 기간을 확인한다. 파일·설정·이름은 현재 상태와 대조한다.
```

Agent Memory는 설치 측에서 별도 MCP로 등록한다. 실제 런에 제공되지 않으면 기억
조회·저장을 약속하지 않고 현재 대화의 자료로 진행한다. `document_search`는 처리된
문서 chunk, `knowledge_search`·`knowledge_neighborhood`는 그래프 근거를 찾는다.
문서 업로드·기억 본문 수정·Graph 작성은 MCP에 없으므로 관리 화면이나 별도 API의 작업이다.
검색 결과의 문서 ID는 Agent Studio의 `File` artifact ID가 아니다.

`recall`의 text에는 ID와 version이 있지만 항목당 1,200자·전체 4,000자로 잘린다.
Studio가 전달하지 않은 `structuredContent.hits`를 읽었다고 가정하지 않는다.
`forget`의 version을 1로 고정하거나 제목만 보고 ID를 만들지 않는다.

자동 회상을 원하면 버전의 `memoryRecall`을 켜고 별도 등록한 서버를 명시적으로 binding하며
허용 도구에 `recall`을 포함한다. 요청별 동적 발견만으로는 실행 전 자동 recall이 되지 않는다.

조직 Agent token은 사용자 위임이 없으면 organization 범위만 접근한다. 로그인 사용자
신원은 Agent Studio가 신뢰된 `X-User-Email` header로 전달한다. 모델이 email·tenant
인자를 만들어 권한을 바꾸지 않으며 자격 증명은 설치 측에서 관리한다.
사용자 scope는 인증 사용자, team scope는 확인된 teamId를 쓰고 조직 전체 공유를 기본값으로 삼지 않는다.

## 모델 설정을 함께 정할 때

현재 Agent Studio에서 선택 가능한 모델과 필요한 능력(tool use·vision·이미지 생성 등)을
먼저 확인한다. `agent-models`는 모델·provider offering 카탈로그이며 MCP 서버가 아니다.
가격과 모델 목록을 프롬프트에 복사해 고정하지 않는다. 버전 설정에는 카탈로그의 `id`를
쓰고 provider 전송용 `wireId`와 혼동하지 않는다. `hidden` 모델을 새 기본값으로 권하지
않고 embedding·rerank·transcription 모델을 일반 대화 모델로 선택하지 않는다.
