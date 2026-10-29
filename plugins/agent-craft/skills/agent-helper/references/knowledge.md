# Agent Knowledge

문서 검색·수집, 지식 그래프, ontology 객체, 녹음·전사·회의록, 오디오 profile을 다루거나 Knowledge 콘솔을 안내할 때 읽는다.
실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **문서(document)**: TXT·MD·CSV·JSON·XML·HTML·PDF·DOCX·PPTX·XLSX·XLS·EPUB. 원본 최대 10 MiB.
  상태는 `pending → processing → ready | failed`다. OCR·암호화 파일·.doc/.ppt·HWP는 지원하지 않는다.
- **지식 그래프**: 문서에서 추출한 node(개체)와 edge(관계). AI가 만든 후보 일부는 사람이 `/review`에서 검토한다.
- **ontology 객체**: `decision`·`action_item`·`risk` 같은 기록과 사람·팀·프로젝트·시스템 같은 개체. `status` 같은 편집 가능 속성이 있다.
- **녹음(recording)과 오디오 작업(job)**: MP3·WAV·FLAC·Ogg·M4A, 최대 512 MiB. 작업 `task`는 `import`·`transcribe`·`postprocess`·`process`다.
- **오디오 profile**: 전사·요약 모델, 언어, 보존 설정을 저장한 사용자 설정.
- **scope**: `user`·`team`·`organization`. 조직 범위는 누구나 읽고 admin·owner만 쓴다. 관리자도 다른 사용자의 개인 자료는 읽지 못한다.

## Helper가 쓸 수 있는 도구

| 영역 | 도구 | 주의 |
|---|---|---|
| 검색 | `context_search`(문서+그래프), `document_search`, `knowledge_search`, `knowledge_neighborhood` | 읽기 전용. 결과 ID는 Studio Artifact ID가 아니다 |
| 객체 | `knowledge_object_types`(먼저 호출), `knowledge_objects`, `knowledge_object`, `knowledge_object_update` | 수정은 `expectedVersion` 필요. 결과에 `action`이 있어야 적용된 것이다 |
| 문서 수집 | `document_ingest`, `document_ingest_status`, `document_ingest_retry` | `idempotencyKey` 필수. 접수 뒤 `ready`를 확인한다. PDF·Office·EPUB은 `contentBase64` |
| 오디오 조회 | `audio_profile_list`, `audio_profile_get`, `audio_models`, `audio_status`, `audio_list`, `audio_request_status`, `audio_output_read` | 읽기 전용 |
| 오디오 작업 | `recording_import`, `audio_job_submit`, `audio_job_cancel`, `audio_job_retry`, `audio_profile_save`, `audio_profile_select` | 승인 필요. 작업 결과는 원래 Chat으로 돌아온다 |
| 직접 업로드 | `recording_reserve` | 예약 후 돌려받은 주소로 원본을 올린다. Chat 첨부는 `recording_import`를 쓴다 |
| 정리 | `recording_archive`, `audio_job_delete`, `recording_delete`, `recording_delete_status` | 되돌리기 어려운 작업이다. 사용자가 명시적으로 요청할 때만 쓴다. `recording_delete`는 `requestId`가 필수이며 응답이 유실되면 다시 삭제하지 말고 `recording_delete_status`로 확인한다 |

녹음 처리 절차는 `audio-processing` Skill이 있으면 그것을 따른다. 없을 때의 기본 흐름:

1. 사용자가 Chat에 녹음을 첨부한다(최대 512 MiB). 더 큰 파일은 콘솔 `/recordings`에서 올린다.
2. `audio_profile_get`(id 없이)으로 기본 profile을 읽는다. 없으면 `audio_models`로 모델을 보여 주고 사용자가 고르게 한다.
3. `recording_import`에 Chat 파일 ID를 `source`로 넘긴다. 녹음이 `ready`가 되면 `audio_job_submit`을 한다.
4. 결과는 Studio가 원래 Chat으로 전달한다. 전사문·회의록은 `audio_output_read`로 읽는다.

## 콘솔 페이지 (`agent-knowledge`)

| 경로 | 용도 |
|---|---|
| `/` | 통합 검색(전체·문서·그래프) |
| `/objects` | ontology 객체 목록·필터·속성 편집·되돌리기 |
| `/knowledge` | 그래프 탐색, node·edge 삭제, 중복 병합 |
| `/documents` | 문서 업로드·상태·본문 보기·재시도·보관·삭제 |
| `/recordings` | 녹음 업로드·전사·요약·결과 보기·보관·삭제 |
| `/recordings/settings` | 오디오 profile |
| `/review` | AI 후보 검토와 처리 내역 |
| `/connect` | MCP 주소 |
| `/onboarding`, `/profile`, `/guide` | 첫 사용 설정, 계정 정보, 사용법 |
| `/members`, `/teams`, `/maintenance`, `/settings` | 관리자 전용 |

콘솔 전용 작업: AI 후보 승인·거절, 그래프 node·edge 삭제와 병합, ontology 형식 편집, 문서 보관·영구 삭제·scope 변경,
유지보수 일정, 회원·팀·설정, 객체 편집 되돌리기.

## 오류

| 증상 | 원인과 해결 |
|---|---|
| 문서가 `pending`에 머묾 | 문서 worker가 동작하지 않는다. 운영자 확인이 필요하다 |
| 문서 `failed` | 형식·암호화·크기를 확인하고 `document_ingest_retry` 또는 콘솔 재시도 |
| `ready`인데 그래프가 비어 있음 | AI 추출은 별도로 진행된다. 추출 모델이 설정돼 있어야 하고 후보는 `/review`에 나타난다 |
| 의미 검색이 안 됨 | Embedding 모델이 없으면 어휘 검색만 동작한다 |
| 녹음 작업 응답 유실 | `audio_request_status(operation, idempotencyKey)`로 조회한다. `operation`은 `recording.reserve`·`audio.submit`·`audio.retry`다. 다시 제출하지 않는다 |
| `Studio authorization required`(401) | 다시 로그인하거나 grant를 확인한다 |
| 409 / 412·428 / 413 / 422 / 429 | version·상태 충돌 / `If-Match` 문제 / 크기 초과 / ontology 규칙 위반 / 사용 한도 |
| 영구 삭제 거절 | 녹음을 먼저 보관하고 진행 중인 작업을 멈춰야 한다 |
