---
name: personal-records
description: >
  사용자가 지정한 Artifact나 오디오 결과를 Librio 개인 Document 또는 Memory 장기 기억에 기록한다.
  문서로 저장해 달라는 요청이나 장기 기억에 남겨 달라는 요청에 사용한다.
compatibility: >
  Artifact를 읽는 File 도구 또는 AudioJob read, 그리고 개인 scope·멱등 키를 지원하는 기록 MCP가 필요하다.
---

# 요청한 개인 기록

사용자가 기록할 대상(Artifact 또는 오디오 작업 결과)과 Memory 또는 Document를 지정한 경우에만 수행한다.
정기 작업, 다운로드, 전사, 요약 요청만으로 기록하지 않는다.

오디오 보관 도구인 ImportFile·TranscribeAudio·AudioJob은 개인 Document/Memory 기록 도구가 아니다.

## 공통 규칙

- 실제 연결 도구의 schema와 서비스 소유권을 확인한다. 문서는 Librio, 장기 기억은 Memory의 연결을 사용한다.
  개인 scope `{kind:"user"}`와 서버가 전달한 사용자 문맥을 사용한다.
- email·토큰을 인수로 요구하거나 임의의 userId·조직 scope를 지정하지 않는다.
- 요청한 범위의 본문을 끝까지 확인하지 못했다면 미확인 범위를 알리고 기록하지 않는다.
- Memory에는 요청된 범위에서 근거가 분명한 항목만 `remember`로 기록한다. 같은 대상의 재시도에서는 source.uri와 idempotencyKey를 유지한다.

## Artifact를 기록하는 경우

1. `File read`로 선택한 Artifact를 읽고 사용자가 요청한 기록 범위를 대조한다. 부분 추출이나 잘림으로 그 범위를 확인하지 못했다면 저장하지 않는다.
   `File read`는 이어 읽기를 지원하지 않는다. `from`을 추가하거나 같은 호출을 반복하지 않는다.
2. Librio Document는 `document_ingest`에 선택한 본문과 확인된 제목을 전달한다.
   mimeType은 본문 형식에 맞는 `text/plain` 또는 `text/markdown`으로 지정한다.
   sourceUri는 `urn:agent-studio:artifact:<artifact_id>`, idempotencyKey는 `<artifact_id>:document`다.
   같은 Artifact 재시도에서는 제목·본문·mimeType·scope와 키를 유지한다.
   File 편집은 새 Artifact ID를 반환하므로 편집본은 그 새 ID로 기록한다.
   `document_ingest_status`로 실제 상태를 확인하고 접수와 ready를 구분한다.
3. Memory는 source.uri `urn:agent-studio:artifact:<artifact_id>`와 idempotencyKey `<artifact_id>:memory:<항목번호>`를 사용한다.

## 오디오 작업 결과를 기록하는 경우

전사문과 회의록은 Librio가 이미 개인 검색 문서로 발행한다. Document로 다시 기록하지 않는다. 이 경우에는 Memory만 기록한다.

1. `AudioJob status`로 작업이 completed이고 해당 `outputs.<kind>`가 `available`인지 확인한다. kind는 `transcript` 또는 `summary`다.
2. `AudioJob read`로 해당 결과를 읽는다. `next_cursor`가 있으면 그 값을 바꾸지 않고 cursor로 보내, 요청한 범위를 모두 읽을 때까지 이어 읽는다.
3. `remember`에 source.uri `urn:agent-studio:audio-job:<job_id>:<kind>`와 idempotencyKey `<job_id>:<kind>:memory:<항목번호>`를 사용한다.

## 결과 보고

반환된 ID와 상태를 보고한다. 오류·충돌을 피하려고 새 키나 조직 scope로 바꾸지 않는다.

원본 Artifact는 그대로 보존한다. 기록된 Document·Memory에는 수신 서비스의 보존 정책이 적용된다.

단기 진행 상황의 인수인계를 요청한 경우에만 Memory의 발견된 handoff_create/get/update/close를 사용한다. 실제 목표·진행·다음 할 일·참조를 저장하고 idempotencyKey와 expectedVersion을 지킨다. native Session·checkpoint·원본 전사 파일이나 자격증명을 handoff에 복사하지 않는다. email 헤더로 사용자 권한을 위임하지 않는다.
