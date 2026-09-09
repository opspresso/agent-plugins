# Studio 도구

현재 제공된 schema가 기준이다. `artifact_id`, `file_id`, `source_ref` 중 정확히 하나를 전달한다.
`artifact_id`는 사용자가 소유한 비공개 Artifact, `file_id`는 업로드·완료된 import 파일,
`source_ref`는 연결 도구가 발급한 원본 참조다. 외부 녹음 ID·URL·인증 값을 이 인수로 대체하지 않는다.

## 새 녹음을 한 작업으로 처리한다

`AudioJob {operation: "config"}`로 enabled, revision, model, retention, postprocess를 확인한다.
후처리 대상은 같은 Agent의 고정 버전으로 설정할 수 있다. 별도 Agent로 위임하는 과정이 아니다.
자동 처리에서는 destination이 없어야 한다. 설정이 없거나 요청과 맞지 않으면 필요한 설정을 알린다.

```json
{"operation":"submit","source_ref":"<조회된 참조>","config_revision":1}
```

revision은 실제 config 응답을 사용한다. config_revision과 model·retention·postprocess·destination
덮어쓰기를 섞지 않는다. 기본 task는 process이며 source, transcript, processed, structured, dialogue
Artifact가 작업의 진행에 따라 만들어진다. config 변경 자체는 기존 녹음을 재처리할 이유가 아니다.

## 일부 단계만 처리한다

- 보관만: `ImportFile {source_ref, retention}`.
- 이미 보관된 원본 전사: `TranscribeAudio {artifact_id, model, language, retention}`.
- 기존 전사 후처리: `AudioJob {operation:"submit", task:"postprocess", artifact_id, postprocess, retention}`.
  postprocess는 config의 projectName/versionName을 사용한다. model·language·destination·config_revision은 생략한다.
- `retention`은 `{unit:"days"|"months", value:양의 정수, timezone:IANA 시간대}`이며 months는 달력 월이다.

`processing_revision`은 같은 요청 재전송에서 유지한다. 사용자가 명시적으로 재처리를 요청했을 때만
새 값을 사용한다. accepted는 접수, duplicate는 기존 작업 재사용, busy는 새 작업 미접수다.
제출 응답의 status와 job.status를 구분한다. duplicate라도 job.status가 completed이면 이미 완료된 작업이다.
stage는 마지막 단계 이름이므로 cleaning이나 importing이라는 값만으로 진행 중이라고 판단하지 않는다.

## 상태와 결과

`AudioJob {operation:"status", job_id}`로 확인한다. queued/running/waiting이면 worker에 맡기고 종료한다.
다음 정기 실행에서 같은 작업을 확인한다. 이 도구에 없는 retry/cancel operation을 만들지 않는다.
list는 nextCursor를 사용하며 한 페이지의 결과만으로 전체 작업이 없다고 단정하지 않는다.

전사 본문은 `AudioJob {operation:"read", job_id}`로 읽고 nextCursor가 있으면 이어 읽는다.
`result_kind:"processed"`는 후처리 본문이다. `File read`는 결과의 Artifact ID를 사용한다.
화자·시각은 전사 도구가 제공한 정보만 사용하고, 누락·불명확한 내용은 추측으로 채우지 않는다.

원본 조회의 source_ref가 만료되어도 접수된 작업은 등록된 refresh recipe를 사용할 수 있다.
OAuth 재인증·계정·endpoint·binding 변경 오류는 연결을 확인하고 새 revision으로 우회하지 않는다.
