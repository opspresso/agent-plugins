# Plaud 오디오 조회

Plaud가 실제 녹음 출처이고 해당 MCP가 연결된 경우에만 사용한다. 연결 설정은 운영자의 영역이다.

## Librio로 전달할 수 없는 이유

Studio의 Plaud `get_file` 매핑은 임시 다운로드 URL을 숨기고 `source_ref`를 반환한다.
현재 `source_ref`를 입력으로 받는 Studio 도구나 Librio 도구는 없다. `recording_import`의 `source`는 Studio 파일 ID만 받는다.
따라서 Plaud 녹음을 Chat에서 바로 Librio로 가져올 수 없다.

- `source_ref`, Plaud 녹음 ID, `presigned_url`을 `recording_import`의 `source`로 보내지 않는다.
- 사용자가 녹음 파일을 Chat에 첨부하면(문서 첨부 한도 10 MiB 이하) 그 파일 ID로 처리한다.
- 더 큰 녹음은 사용자가 Librio 콘솔에서 올린다. 그 뒤 `audio_list`로 `recordingId`를 찾아 작업을 제출한다.
- 정기 실행에서 Plaud 녹음을 자동으로 가져와 처리한다고 약속하지 않는다.

## 녹음 찾기

- `list_files`의 실제 schema를 사용한다. `date_from`·`date_to`는 `YYYY-MM-DD`, `query`는 이름 검색이다.
  필터가 있으면 pagination이 무시된다. page만 늘려 새 후보를 얻었다고 가정하지 않는다.
  현재 서버의 `page_size` 최솟값은 10이다.
- 반환된 `data`의 실제 ID·제목·시각을 확인한다. `duration`은 밀리초다. 필터 조회는 최신 500건을 탐색하는 예산이며
  일치 결과 500건을 보장하지 않는다. `complete=false`이면 `note`가 알려 주는 실제 탐색 범위를 보고한다.
- 도구 오류와 빈 목록을 구분한다. 적용한 기간과 시간대를 결과에 밝힌다.

## Plaud의 기존 결과

`get_file`·`get_transcript`·`get_note`의 전사·요약은 Plaud가 만든 기존 결과다. Librio 전사를 요청했다면 이 결과로 대신하지 않는다.
대체가 필요하면 사용자의 허가를 받고 출처를 Plaud로 명시한다.

공식 계약: [Plaud MCP](https://docs.plaud.ai/plaud-mcp-cli/mcp).
