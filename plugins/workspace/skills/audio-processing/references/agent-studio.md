# 앱 도구

Studio의 현재 제공된 schema가 기준이다. ImportFile·TranscribeAudio·AudioJob 이름은 유지되며 전사와 회의록은 Agent Librio가 실행한다.
AudioJob 인수는 `request` 객체 하나이며, operation에 맞는 형태만 선택한다. 선택 항목은 필요 없으면 null로 지정한다.
빈 문자열, "none", 임의 날짜·모델·retention을 채워 넣지 않는다. 서로 다른 작업의 필드를 섞지 않는다.

## 짧은 사용자 요청으로 시작한다

"Plaud 최신 녹음을 전사하고 요약해 줘"처럼 대상과 결과만 받아도 아래 절차를 수행한다.
스킬이 처리 순서를, MCP가 실제 출처 조회를, Agent 설정이 모델·회의록·보존 기간을 담당한다.

```json
{"request":{"operation":"list","cursor":null,"limit":20}}
```

같은 녹음의 진행 중인 작업은 ID와 상태를 재사용하고, 완료된 같은 녹음은 결과가 `available`일 때만 재사용한다.
list에 nextCursor가 있으면 필요 범위까지 이어 조회한다. 실패·차단은 원인을 보고하고 임의 재처리하지 않는다.

```json
{"request":{"operation":"config"}}
```

enabled·revision·model·summary·retention을 확인한다. `summary`가 있으면 Librio가 회의록을 함께 만든다.
설정이 없거나 요청과 맞지 않으면 필요한 설정만 알린다.
연결된 출처 MCP에서 목록과 상세를 조회한다. source_ref는 서버가 발급한 참조이며 외부 파일 ID나 URL이 아니다.
Plaud plugin의 기본 파일 매핑이 적용되면 get_file 응답에서 source_ref를 받는다.
복수 녹음은 maxActive(대기+진행)와 maxPerOccurrence가 허용하는 만큼 각각 submit한다.
worker는 Agent별 접수 순서대로 한 건씩 실행하므로 처리 완료를 기다렸다가 다음 녹음을 제출할 필요가 없다.
접수 한도를 바꾸거나 우회하지 않는다. 한도가 1이면 한 건만 접수하고 나머지는 미접수로 보고한다.

## 새 녹음은 통합 작업 하나로 처리한다

```json
{"request":{"operation":"submit","source":{"kind":"source","id":"<source_ref>"},"config_revision":12,"processing_revision":null}}
```

revision은 실제 config 응답으로 바꾼다. 이 형태에는 model·retention·summary·task를 넣지 않는다.
Studio가 원본을 Librio로 보내고, Librio가 전사와 설정된 회의록을 만든다.
이미 보관된 원본은 source의 kind를 artifact로, id를 원본 Artifact ID로 지정한다.
사용자가 명시적으로 재처리할 때만 processing_revision에 새 값을 쓰고 같은 요청의 재전송에서는 유지한다.
앞 작업이 완료돼도 발생당 접수 한도는 복원되지 않으므로 ImportFile·TranscribeAudio로 작업을 분리하지 않는다.

설정 대신 명시적 처리 옵션이 필요한 경우에만 operation process를 사용한다.

```json
{"request":{"operation":"process","source":{"kind":"source","id":"<source_ref>"},"model":"<Librio 전사 모델 ID>","language":null,"retention":{"unit":"months","value":3,"timezone":"Asia/Seoul"},"summary":{"model":"<Librio 회의록 모델 ID>","instructions":null},"processing_revision":null}}
```

`summary.model`은 Librio의 summary 모델 공개 ID다. `instructions`는 회의록의 중점만 조정하며 최대 4,000자다.
회의록이 필요 없으면 summary를 null로 지정한다.

## 일부 단계만 처리한다

원본 보관만 필요할 때 ImportFile을 사용한다. Librio를 호출하지 않는다.

```json
{"source":{"kind":"source","id":"<source_ref>"},"retention":{"unit":"months","value":3,"timezone":"Asia/Seoul"},"processing_revision":null}
```

전사만 필요하면 TranscribeAudio에 source·model·retention·language·processing_revision을 전달한다.
source는 `{kind:"artifact"|"file"|"source",id:"<해당 참조>"}`이며 language는 선택하지 않으면 null이다.
모델·보존 기간은 config 또는 사용자 요청에서 가져온다. model은 Librio의 허용된 transcription 공개 ID이며 provider wireId나 catalogId를 직접 넣지 않는다.

## 상태와 결과

```json
{"request":{"operation":"status","job_id":"<실제 작업 ID>"}}
```

접수 응답의 accepted/duplicate는 job.status와 다르다. queued/running/waiting이면 실제 ID를 보고하고
남은 요청 대상의 접수를 마친 뒤 종료한다. 한 실행에서 반복 polling하지 않는다.
completed 작업은 `outputs.transcript`와 `outputs.summary`의 상태를 본다.

| 상태 | 뜻 |
| --- | --- |
| `available` | Librio에서 읽을 수 있다 |
| `not_produced` | 이 작업이 만들지 않았다. 예: 회의록 설정 없음 |
| `expired`·`deleted` | Librio의 보존 기간이 끝났거나 보관 해제됐다 |

원본 오디오는 `source.href`가 있을 때만 안내한다. `source.unavailable`이면 원본 파일이 없다고 보고한다.
`artifact:`나 `sandbox:` 링크를 만들어내지 않는다. 과거 작업의 모델·완료 시각을 현재 설정으로 새로 실행한 결과와 구분한다.

```json
{"request":{"operation":"read","job_id":"<실제 작업 ID>","result_kind":"summary","cursor":null,"max_bytes":null}}
```

result_kind는 `transcript`(전사문) 또는 `summary`(회의록)다. 응답은 `{text, next_cursor}`이다.
next_cursor가 있으면 그 값을 바꾸지 않고 cursor로 보내 이어 읽는다. max_bytes는 4–65,536이며 null이면 16,384다.
읽기 오류가 "no longer available"이면 Librio에서 결과가 사라진 것이다. 재전사로 대신하지 않고 보고한다.

이 도구에 없는 retry/cancel operation을 만들지 않는다.
occurrence_limit은 현재 실행의 접수 한도 소진이다. 기다리거나 반복 제출해도 풀리지 않는다.
active_limit은 대기·진행을 합친 접수 한도다. 기존 작업 ID와 미접수 대상을 보고하고 종료한다.
연결 변경·OAuth 오류는 설정을 확인하며 새 revision으로 우회하지 않는다.

서비스간 HTTP request key·signed principal·org는 Studio가 관리한다. 이 값들을 AudioJob request에 추가하지 않는다.
job의 `librio.recordingId`·`librio.jobId`는 Librio MCP의 `audio_status`·`audio_output_read`에 쓰는 ID다. AudioJob 인수로 보내지 않는다.

## 회의 내용 검색과 장기 기억

Librio는 전사문과 회의록을 사용자 범위의 검색 문서로 발행한다. 과거 회의를 찾을 때는 연결된 Librio MCP의
검색 도구를 사용한다. 결정이나 사실을 장기 기억에 남겨 달라는 명시적 요청만 `personal-records`로 처리한다.
AudioJob에는 외부 기록 옵션이 없다.
