---
name: personal-records
description: >
  사용자가 지정한 Artifact를 개인 Document 또는 Memory에 기록한다.
  문서로 저장해 달라는 요청이나 장기 기억에 남겨 달라는 요청에 사용한다.
compatibility: >
  Artifact를 읽는 File 도구와 개인 scope·멱등 키를 지원하는 기록 MCP가 필요하다.
---

# 요청한 개인 기록

사용자가 기록할 Artifact와 Memory 또는 Document를 지정한 경우에만 수행한다.
정기 작업, 다운로드, 전사, 요약 요청만으로 기록하지 않는다.

오디오 보관 도구인 ImportFile·TranscribeAudio·AudioJob은 개인 Document/Memory 기록 도구가 아니다.

1. `File read`로 선택한 Artifact를 읽는다. 잘린 응답이면 나머지를 읽고, 전체를 얻지 못하면 저장을 중단한다.
2. 실제 연결 도구의 schema를 확인한다. 개인 scope `{kind:"user"}`와 서버가 전달한 사용자 문맥을 사용한다.
   email·토큰을 인수로 요구하거나 임의의 userId·조직 scope를 지정하지 않는다.
3. Document는 `document_ingest`에 선택한 본문을 그대로 전달한다.
   sourceUri는 `urn:agent-studio:artifact:<artifact_id>`, idempotencyKey는 `<artifact_id>:document`다.
   `document_ingest_status`로 실제 상태를 확인하고 접수와 ready를 구분한다.
4. Memory는 요청된 범위에서 근거가 분명한 항목만 `remember`로 기록한다.
   source.uri에 같은 Artifact URI를 기록하고 idempotencyKey `<artifact_id>:memory:<항목번호>`를 유지한다.
5. 반환된 ID와 상태를 보고한다. 오류·충돌을 피하려고 새 키나 조직 scope로 바꾸지 않는다.

원본 Artifact는 그대로 보존한다. 기록된 Document·Memory에는 수신 서비스의 보존 정책이 적용된다.
