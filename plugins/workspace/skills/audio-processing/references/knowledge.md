# Agent Knowledge 도구

연결된 Agent Knowledge MCP의 현재 schema가 기준이다. 도구는 호출자 권한(`audio:read`, 쓰기는 `audio:write`)이 있을 때만 목록에 나온다.
선택 항목은 필요할 때만 넣는다. 빈 문자열, `"none"`, 임의 날짜·모델·보존 기간을 채워 넣지 않는다.
조직·사용자 신원, 서비스 URL, credential은 서버가 정한다. 인수로 만들지 않는다.

## 도구 목록

| 단계 | 도구 | 주요 입력 |
| --- | --- | --- |
| 설정 읽기 | `audio_profile_get` | `id` 생략 시 사용자의 기본 선택 `{profileId, profile}` |
| 설정 목록 | `audio_profile_list` | `limit`, `offset` |
| 모델 목록 | `audio_models` | 없음 |
| 원본 가져오기 | `recording_import` | `title`, `filename`, `mimeType`, `scope`, `profileId`+`profileRevision` 또는 `retention`, `idempotencyKey`, `source` |
| 작업 제출 | `audio_job_submit` | `recordingId`, `task`, `processingRevision`, `profileId`+`profileRevision` 또는 명시 모델, `idempotencyKey` |
| 상태 | `audio_status` | `resource:"recording"\|"job"`, `id` |
| 목록 | `audio_list` | `resource:"recordings"\|"jobs"`, 선택 `recordingId`, `limit`, `offset`; `mine`은 `jobs`에만 사용 |
| 접수 확인 | `audio_request_status` | `operation:"recording.reserve"\|"audio.submit"\|"audio.retry"`, `idempotencyKey` |
| 결과 읽기 | `audio_output_read` | 작업 `id`, `kind:"transcript"\|"summary"`, 선택 `cursor`, `limit` |
| 취소·재시도·삭제 | `audio_job_cancel`, `audio_job_retry`, `audio_job_delete` | `id`, `expectedRevision`(재시도는 `idempotencyKey`도 필요) |

`audio_profile_save`·`audio_profile_select`는 사용자가 설정 저장·선택을 명시적으로 요청한 경우에만 쓴다.
`recording_archive`, `recording_delete`는 보관·영구 삭제 요청에만 쓴다. `recording_delete`는 되돌릴 수 없다.

## 설정을 읽는다

```json
{"tool":"audio_profile_get","arguments":{}}
```

응답 `{profileId, profile}`에서 `profile.id`와 `profile.revision`을 사용한다. 둘 다 `null`이면 선택이 없다.
`profileId`만 있고 `profile`이 `null`이면 선택한 profile에 더 이상 접근할 수 없다.
두 경우 모두 접수하지 않고 Agent Knowledge 콘솔에서 설정을 선택하도록 안내한다.
`profile.settings`에는 `transcriptionModelId`, 선택 `summary`(회의록 모델), `language`, `retention`, `maxActive`, `maxPerOccurrence`가 있다.

## Studio 파일을 가져온다

```json
{"tool":"recording_import","arguments":{"title":"<녹음 제목>","filename":"<파일 이름>","mimeType":"audio/mpeg","scope":"user","profileId":"<profile.id>","profileRevision":3,"idempotencyKey":"<이 파일의 고정 키>","source":"<Studio 파일 ID>"}}
```

- `source`에는 Chat 첨부 파일 ID 또는 MCP `get_file`이 반환한 `file_id`를 넣는다. Studio가 호출 직전에 `{url, checksum, sizeBytes, expiresAt}` 참조로 바꾼다.
- 파일 이름과 MIME은 첨부 또는 MCP 응답의 실제 값을 쓴다. 지원 형식은 MP3, WAV, FLAC, Ogg, MP4/M4A, QuickTime Audio이며 최대 512 MiB, 6시간이다.
- `scope`는 사용자가 팀·조직 공유를 요청하지 않으면 `user`다. `team`은 `teamId`가 필요하다.
- `profileId`·`profileRevision`과 `retention` 중 하나만 보낸다.
- 같은 파일의 재전송에는 같은 `idempotencyKey`와 입력을 유지한다. 같은 키에 다른 입력을 보내면 충돌이다.

## 작업을 제출한다

```json
{"tool":"audio_job_submit","arguments":{"recordingId":"<recording.id>","task":"process","processingRevision":"<새 처리 요청의 고정 값>","profileId":"<profile.id>","profileRevision":3,"idempotencyKey":"<고정 키>"}}
```

| `task` | 용도 | 추가 입력 |
| --- | --- | --- |
| `process` | 전사와 회의록(profile에 `summary`가 있을 때) | 없음 |
| `transcribe` | 사용자가 회의록 없이 전사만 요청 | 없음 |
| `postprocess` | 완료된 전사로 회의록만 다시 작성 | `transcriptJobId`, `summary:{modelId, instructions?}` |
| `import` | 원본 decoding·길이 검증만 | 없음 |

- `processingRevision`은 새 처리 요청마다 새 값이다. 같은 요청의 재전송에서는 바꾸지 않는다.
- `postprocess`는 profile과 함께 쓸 수 없다. `summary.modelId`는 profile의 `settings.summary.modelId` 또는 `audio_models`의 회의록 모델 ID다.
  형식·중점 변경은 `summary.instructions`(최대 10,000자)에 담는다.
- 정기 실행 한 번에 제출한 작업을 묶으려면 같은 `occurrenceId`를 쓴다. 생략하면 요청마다 독립으로 센다.
- Studio Chat 실행은 `audio_job_submit`·`audio_job_retry`의 `idempotencyKey`를 도구 호출마다 고정한 값으로 바꿔 보낸다.
  응답의 `work.requestKey`가 실제 키다. 접수 확인에는 이 값을 쓴다.

응답 `structuredContent.work`는 작업 참조다. `id`, `status`, `terminal`, `observe`(`audio_status` 호출), `outputs`를 담는다.
`terminal`은 `completed`·`failed`·`cancelled`일 때 true다. `blocked`는 결과가 불확실한 상태이며 terminal이 아니다.

## 상태와 결과를 읽는다

```json
{"tool":"audio_status","arguments":{"resource":"job","id":"<작업 ID>"}}
```

작업 상태는 `waiting`, `queued`, `running`, `completed`, `failed`, `blocked`, `cancelled`다.
`outputs.<kind>.availability`가 `available`인 출력만 읽는다.

```json
{"tool":"audio_output_read","arguments":{"id":"<작업 ID>","kind":"summary"}}
```

`kind`는 `transcript`(전사문) 또는 `summary`(회의록)다. 한 번에 최대 65,536 bytes를 읽는다.
응답은 `{content, nextCursor, hasMore}`이다. `hasMore`가 true이면 `nextCursor`를 바꾸지 않고 `cursor`로 보내 이어 읽는다.

## 오류를 처리한다

| 상황 | 행동 |
| --- | --- |
| profile revision 불일치(409) | `audio_profile_get`으로 현재 revision을 다시 읽는다. 응답 유실 뒤라면 먼저 `audio_request_status`로 원래 요청을 확인한다 |
| 활성·발생당 한도 초과(409) | 새 작업은 없다. 남은 녹음을 미접수로 보고한다 |
| `blocked`(`effect_uncertain`) | 모델 호출 결과가 불확실하다. 재시도하지 않고 상태를 보고한다. 관리자가 Agent Knowledge 콘솔에서 확정한다 |
| `failed` | 원인을 보고한다. 사용자가 요청하면 `audio_job_retry`로 재시도한다 |
| 권한 거절(403)·인증 오류 | 연결과 권한 문제를 보고한다. 다른 credential이나 범위로 바꾸지 않는다 |

재시도·취소·삭제의 `expectedRevision`은 `audio_status`가 반환한 작업의 `revision`이다.
재시도는 저장된 설정 snapshot을 쓴다. 새 설정으로 처리하려면 새 `audio_job_submit`을 보낸다.
