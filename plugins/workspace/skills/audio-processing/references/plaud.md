# Plaud 녹음 가져오기

Plaud가 실제 녹음 출처이고 해당 MCP가 연결된 경우에만 사용한다. 연결 설정은 운영자의 영역이다.

## 녹음 찾기

- `list_files`의 실제 schema를 사용한다. `date_from`·`date_to`는 `YYYY-MM-DD`, `query`는 이름 검색이다.
  필터가 있으면 pagination이 무시된다. page만 늘려 새 후보를 얻었다고 가정하지 않는다.
  현재 서버의 `page_size` 최솟값은 10이다.
- 반환된 `data`의 실제 ID·제목·시각을 확인한다. `duration`은 밀리초다. 필터 조회는 최신 500건을 탐색하는 예산이며
  일치 결과 500건을 보장하지 않는다. `complete=false`이면 `note`가 알려 주는 실제 탐색 범위를 보고한다.
- 도구 오류와 빈 목록을 구분한다. 적용한 기간과 시간대를 결과에 밝힌다.

## Agent Knowledge로 가져온다

1. 사용자의 기본 profile과 같은 녹음의 기존 작업을 [처리 절차](../SKILL.md)에 따라 확인한다.
2. 선택한 Plaud 녹음 ID로 `get_file`을 호출한다. Studio의 파일 매핑이 원본을 다운로드해 사용자 소유 Studio 파일로 저장한다.
   결과는 `file_id`, `filename`, `mime_type`, `size_bytes`, `source`, `external_id`다. 임시 다운로드 URL과 원본 bytes는 모델에 전달되지 않는다.
3. `recording_import`의 `source`에 반환된 `file_id`를 그대로 넣는다. `filename`과 `mimeType`은 각각 `filename`과 `mime_type`을 쓴다.
   제목은 확인한 녹음 제목을 쓰며, profile·scope·고정 `idempotencyKey`는 [Agent Knowledge 도구](knowledge.md)를 따른다.
4. `recording.status`가 `ready`이면 반환된 `recording.id`로 `audio_job_submit`의 `process` 작업을 접수한다.
   접수 상태와 작업 ID를 보고한다. 완료된 전사문·회의록은 Studio가 원래 Chat에 전달한다.

- 한 실행에서 이미 받은 `file_id`는 재사용한다. 가져온 파일 ID가 있는데 `get_file`을 다시 호출하지 않는다.
- `source`에 Plaud 녹음 ID(`external_id`), `presigned_url`, 이전 `source_ref`를 넣지 않는다. 임시 URL을 모델 문맥이나 답변에 복사하지 않는다.
- `get_file`이 오류를 반환하면 가져오기에 실패한 것이다. 파일 ID를 만들거나 작업을 제출하지 않는다. 실제 오류를 보고한다.
- 응답에 `file_id`가 없으면 Studio의 파일 매핑 지원·plugin 동기화 상태를 운영자가 확인해야 한다. 원본 URL을 다른 도구로 우회하지 않는다.
- 원본 전송은 최대 512 MiB다. Agent Knowledge 원본 한도도 같으므로 콘솔 업로드로 한도를 우회할 수 없다.
- 자동 실행도 현재 사용자 연결·권한과 profile 한도를 따른다. 연결되지 않은 계정의 녹음을 처리한다고 약속하지 않는다.

## Plaud의 기존 결과

`get_transcript`·`get_note`는 Plaud가 만든 기존 전사·요약을 읽는다. Agent Knowledge 전사를 요청했다면 이 결과로 대신하지 않는다.
대체가 필요하면 사용자의 허가를 받고 출처를 Plaud로 명시한다.

공식 계약: [Plaud MCP](https://docs.plaud.ai/plaud-mcp-cli/mcp).
