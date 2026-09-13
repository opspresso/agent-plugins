# Plaud 오디오 조회

Plaud가 실제 녹음 출처이고 해당 MCP가 제공되는 경우에만 사용한다. 연결 설정은 운영자의
영역이며, 이미 연결된 계정에서 읽을 수 있는 녹음은 추가 계정 정보나 다운로드 URL을 요구하지 않는다.

## 요청 범위와 목록

- "최근 일주일 녹음을 가져와서 전사하고 요약해"는 실행 시각 기준 최근 7일의 녹음을 조회하고
  기존 완료 결과를 재사용하며 미처리 녹음을 프로젝트 설정으로 접수하는 요청이다.
  적용한 기간과 시간대를 결과에 밝힌다. 없는 시간대를 추정해 정확한 시각으로 단정하지 않는다.
- `list_files`의 실제 schema를 사용한다. `date_from`·`date_to`는 `YYYY-MM-DD`, `query`는 이름 검색이다.
  필터가 있으면 pagination이 무시되므로 page만 증가시켜 새 후보를 얻었다고 가정하지 않는다.
  현재 서버의 `page_size` 최솟값은 10이다. 한 건만 처리하더라도 목록은 허용 크기로 읽고 그 안에서 선택한다.
- 반환된 `data`의 실제 ID·시각을 확인한다. `duration`은 밀리초다. `truncated`가 참이거나
  탐색 상한에 도달했으면 확인된 후보만 처리하고 전체 조회를 완료했다고 보고하지 않는다.
  도구 오류와 빈 목록은 구분한다.
- 기존 `AudioJob list`의 `sourceIdentity.itemId`로 같은 녹음의 작업을 찾는다.
  완료된 process 작업은 재사용하며 import·transcribe만 끝났으면 필요한 후속 단계만 수행한다.
  기간 내 여러 후보가 있어도 프로젝트의 작업 한도를 바꾸거나 우회하지 않는다.

## 파일 참조와 접수

실제 녹음 ID로 `get_file(file_id=...)`을 호출한다. Studio의 workspace plugin 기본 매핑은
`presigned_url`·`id`·`name`을 다음과 같은 도구 결과로 변환한다.

```json
{"source_ref":"<서버가 발급한 참조>","filename":"<녹음 이름>","mime_type":"audio/mpeg","source":"plaud","external_id":"<녹음 ID>"}
```

`source_ref`가 있으면 정상이며 추가 매핑이나 URL 조회가 필요하지 않다.
[Studio 도구](agent-studio.md)의 config → submit에 `source.kind="source"`, `source.id=source_ref`를 넣는다.
외부 녹음 ID는 중복 확인·상세 조회용이며 source_ref나 Artifact ID를 대신하지 않는다.
원본 임시 URL과 같은 녹음 ID의 갱신은 Studio가 처리한다. 매핑 실패는 정확한 오류를 보고한다.

요청한 전사·요약은 Studio의 설정된 모델과 worker가 수행한다. Plaud의 기존 transcript·note를
새로 전사한 결과로 대신하지 않는다. 조회 성공·작업 접수·전사 완료·요약 완료를 구분한다.

공식 계약: [Plaud MCP](https://docs.plaud.ai/plaud-mcp-cli/mcp).
