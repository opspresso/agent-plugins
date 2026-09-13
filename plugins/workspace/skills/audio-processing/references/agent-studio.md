# Studio 도구

현재 제공된 schema가 기준이다. AudioJob 인수는 `request` 객체 하나이며, operation에 맞는 형태만
선택한다. 선택 항목은 필요 없으면 null로 지정한다. 빈 문자열, "none", 임의 날짜·모델·retention을
채워 넣지 않는다. 서로 다른 작업의 필드를 섞지 않는다.

## 짧은 사용자 요청으로 시작한다

"Plaud 최신 녹음을 전사하고 요약해 줘"처럼 대상과 결과만 받아도 아래 절차를 수행한다.
스킬이 처리 순서를, MCP가 실제 출처 조회를, 프로젝트 설정이 모델·후처리·보존 기간을 담당한다.

```json
{"request":{"operation":"list","cursor":null,"limit":20}}
```

같은 녹음의 진행 중인 작업은 ID와 상태를 재사용하고, 완료된 같은 녹음은 결과를 재사용한다.
list에 nextCursor가 있으면 필요 범위까지 이어 조회한다. 실패·차단은 원인을 보고하고 임의 재처리하지 않는다.

```json
{"request":{"operation":"config"}}
```

enabled·revision·model·retention·postprocess를 확인한다. 설정이 없거나 요청과 맞지 않으면 필요한
설정만 알린다. 외부 기록을 요청하지 않았으면 destination이 없는 설정을 사용한다.
연결된 출처 MCP에서 목록과 상세를 조회한다. source_ref는 서버가 발급한 참조이며 외부 파일 ID나 URL이 아니다.
Plaud plugin의 기본 파일 매핑이 적용되면 get_file 응답에서 source_ref를 받는다.
복수 녹음은 maxActive(대기+진행)와 maxPerOccurrence가 허용하는 만큼 각각 submit한다.
worker는 프로젝트별 접수 순서대로 한 건씩 실행하므로 처리 완료를 기다렸다가 다음 녹음을 제출할 필요가 없다.
접수 한도를 바꾸거나 우회하지 않는다. 한도가 1이면 한 건만 접수하고 나머지는 미접수로 보고한다.

## 새 녹음은 통합 작업 하나로 처리한다

```json
{"request":{"operation":"submit","source":{"kind":"source","id":"<source_ref>"},"config_revision":12,"processing_revision":null}}
```

revision은 실제 config 응답으로 바꾼다. 이 형태에는 model·retention·postprocess·destination·task를
넣지 않는다. worker가 원본 보관 → 전사 → 설정된 후처리를 이어가며 각 결과를 Artifacts에 저장한다.
이미 보관된 원본은 source의 kind를 artifact로, id를 원본 Artifact ID로 지정한다.
사용자가 명시적으로 재처리할 때만 processing_revision에 새 값을 쓰고 같은 요청의 재전송에서는 유지한다.
앞 작업이 완료돼도 발생당 접수 한도는 복원되지 않으므로 ImportFile·TranscribeAudio로 작업을 분리하지 않는다.

## 일부 단계만 처리한다

원본 보관만 필요할 때 ImportFile을 사용한다.

```json
{"source":{"kind":"source","id":"<source_ref>"},"retention":{"unit":"months","value":3,"timezone":"Asia/Seoul"},"processing_revision":null}
```

전사만 필요하면 TranscribeAudio에 source·model·retention·language·processing_revision을 전달한다.
source는 `{kind:"artifact"|"file"|"source",id:"<해당 참조>"}`이며 language는 선택하지 않으면 null이다.
모델·보존 기간은 config 또는 사용자 요청에서 가져온다.

이미 전사된 Artifact는 AudioJob postprocess로 요약한다. 오디오 입력으로 다시 제출하지 않는다.

```json
{"request":{"operation":"postprocess","artifact_id":"<전사 Artifact ID>","postprocess":{"projectName":"<후처리 Agent>","versionName":"published"},"retention":{"unit":"months","value":3,"timezone":"Asia/Seoul"},"processing_revision":null}}
```

후처리 대상과 retention은 실제 config의 값을 사용한다. 별도 Agent를 만들 필요는 없다.
config_revision·전사 model·language·destination은 이 형태에 없다.
설정 대신 명시적 처리 옵션이 필요한 경우에만 operation process를 사용하고 해당 schema를 따른다.

## 상태와 결과

```json
{"request":{"operation":"status","job_id":"<실제 작업 ID>"}}
```

접수 응답의 accepted/duplicate는 job.status와 다르다. queued/running/waiting이면 실제 ID를 보고하고
남은 요청 대상의 접수를 마친 뒤 종료한다. 한 실행에서 반복 polling하지 않는다. completed라면 마지막 stage가 importing이나 cleaning이어도
끝난 작업이다. 원본·전사·요약 Artifact 링크를 안내한다. 처리되지 않은 단계는 완료로 보고하지 않는다.

```json
{"request":{"operation":"read","job_id":"<실제 작업 ID>","result_kind":"processed","cursor":null,"limit":12000}}
```

transcript는 전사문, processed는 후처리 본문이다. nextCursor가 있으면 이어 읽는다.
원문에 없는 화자·시각·결정은 만들지 않는다. 이 도구에 없는 retry/cancel operation을 만들지 않는다.
occurrence_limit은 현재 실행의 접수 한도 소진이다. 기다리거나 반복 제출해도 풀리지 않는다.
active_limit은 대기·진행을 합친 접수 한도다. 기존 작업 ID와 미접수 대상을 보고하고 종료한다.
연결 변경·OAuth 오류는 설정을 확인하며 새 revision으로 우회하지 않는다.
