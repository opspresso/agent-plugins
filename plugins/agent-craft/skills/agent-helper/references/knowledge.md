# Agent Knowledge

문서 검색·수집, 지식 그래프, ontology 객체, 녹음·전사·회의록, 오디오 profile을 다루거나 Knowledge 화면을 안내할 때 읽는다.
실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **문서(document)**: TXT·MD·CSV·JSON·XML·HTML·PDF·DOCX·PPTX·XLSX·XLS·EPUB. 원본 최대 10 MiB.
  상태는 `pending → processing → ready | failed`다. OCR·암호화 파일·.doc/.ppt·HWP는 지원하지 않는다.
- **지식 그래프**: 문서에서 추출한 node(개체)와 edge(관계). AI가 만든 후보 일부는 사람이 검토 화면(`/knowledge/review`)에서 결정한다.
- **ontology 객체**: `decision`·`action_item`·`risk` 같은 기록과 사람·팀·프로젝트·시스템 같은 개체. `status` 같은 편집 가능 속성이 있다.
- **녹음(recording)과 오디오 작업(job)**: MP3·WAV·FLAC·Ogg·M4A, 최대 512 MiB. 작업 `task`는 `import`·`transcribe`·`postprocess`·`process`다.
- **오디오 profile**: 전사·요약 모델, 언어, 보존 설정을 저장한 사용자 설정.
- **scope**: `user`·`team`·`organization`. 조직 범위는 누구나 읽고 admin·owner만 쓴다. 관리자도 다른 사용자의 개인 자료는 읽지 못한다.

## Helper가 쓸 수 있는 도구

| 영역 | 도구 | 주의 |
|---|---|---|
| 검색 | `context_search`(문서+그래프), `document_search`, `knowledge_search`, `knowledge_neighborhood` | 읽기 전용. 결과 ID는 Studio 파일 ID가 아니다 |
| 질문 해석 | `knowledge_resolve` | 새 질문에 먼저 호출한다. 질문이 가리키는 용어·객체 유형·지표와 다음에 쓸 도구를 준다. 범위(coverage)가 낮으면 `context_search`로 문서를 찾거나 사용자에게 묻는다 |
| 객체 조회 | `knowledge_object_types`, `knowledge_objects`, `knowledge_object`, `knowledge_object_aggregate`, `knowledge_metric`, `knowledge_quality` | 읽기 전용. 개수·합계는 검색 결과가 아니라 `knowledge_object_aggregate`·`knowledge_metric`으로 답한다 |
| 객체 수정 | `knowledge_object_update`, `knowledge_object_action`, `knowledge_ledger_import` | 수정과 action은 읽은 객체의 revision을 `expectedVersion`으로 보낸다. 결과에 `action`이 있어야 적용된 것이다. revision 충돌이면 다시 읽는다 |
| 문서 수집 | `document_ingest`, `document_ingest_status`, `document_ingest_retry`, `document_classify` | `idempotencyKey` 필수. 접수 뒤 `ready`를 확인한다. PDF·Office·EPUB은 `contentBase64`. `document_classify`는 읽은 문서 revision을 `expectedRevision`으로 보낸다 |
| 오디오 조회 | `audio_profile_list`, `audio_profile_get`, `audio_models`, `audio_status`, `audio_list`, `audio_request_status`, `audio_output_read` | 읽기 전용 |
| 오디오 작업 | `recording_import`, `audio_job_submit`, `audio_job_cancel`, `audio_job_retry`, `audio_profile_save`, `audio_profile_select` | 승인 필요. 작업 결과는 원래 Chat으로 돌아온다 |
| 직접 업로드 | `recording_reserve` | 예약 후 돌려받은 주소로 원본을 올린다. Chat 첨부는 `recording_import`를 쓴다 |
| 정리 | `recording_archive`, `audio_job_delete`, `recording_delete`, `recording_delete_status` | 되돌리기 어려운 작업이다. 사용자가 명시적으로 요청할 때만 쓴다. `recording_delete`는 `requestId`가 필수이며 응답이 유실되면 다시 삭제하지 말고 `recording_delete_status`로 확인한다 |

녹음 처리 절차는 `audio-processing` Skill이 있으면 그것을 따른다. 없을 때의 기본 흐름:

1. 사용자가 Chat에 녹음을 첨부한다(최대 512 MiB). 이미 올린 녹음은 `audio_list`로 찾는다.
2. `audio_profile_get`(id 없이)으로 기본 profile을 읽는다. 없으면 `audio_models`로 모델을 보여 주고 사용자가 고르게 하거나,
   오디오 프로필 화면(`/knowledge/recordings/profiles`)에서 profile을 만들게 한다.
3. `recording_import`에 Chat 파일 ID를 `source`로 넘긴다. 녹음이 `ready`가 되면 `audio_job_submit`을 한다.
4. 결과는 Studio가 원래 Chat으로 전달한다. 전사문·회의록은 `audio_output_read`로 읽는다.
   작업 결과의 `route`는 그 작업의 화면(`/knowledge/recordings/<recordingId>/jobs/<jobId>`)이다.

## 화면

| 경로 | 용도 |
|---|---|
| `/knowledge` | 통합 검색과 그래프(`?q=`) |
| `/knowledge/nodes/<nodeId>` | 지식 node와 이웃 그래프. node·edge 삭제, 중복 병합 |
| `/knowledge/objects`, `/knowledge/objects/<objectId>` | ontology 객체 목록·필터·속성 편집·되돌리기 |
| `/knowledge/documents`, `/knowledge/documents/<documentId>` | 문서 업로드·상태·본문 보기·재시도·보관·삭제 |
| `/knowledge/recordings`, `/knowledge/recordings/<recordingId>` | 녹음 업로드·전사·요약·결과 보기·보관·삭제. `?at=<초>`는 그 시각부터 재생한다 |
| `/knowledge/recordings/<recordingId>/jobs/<jobId>` | 처리 작업 하나의 상태와 출력 |
| `/knowledge/recordings/profiles` | 오디오 프로필 |
| `/knowledge/review` | AI 후보 검토와 처리 내역(`?tab=groups`·`meetings`·`chunks`·`history`) |
| `/knowledge/quality` | 객체 수, 중복 후보, 검토 대기, 질문 범위 |
| `/knowledge/ontology` | ontology 형식(객체·관계·지표·용어) 보기와 편집 |
| `/settings/knowledge/<section>` | 관리자 전용 설정. section은 `general`·`ai`·`document`·`auth`·`storage`·`observability` |

MCP 주소와 연결 방법은 `/guide/connect`에 있다.

사람이 화면에서 하는 작업: AI 후보·회의 제안 승인·거절, 그래프 node·edge 삭제와 병합, ontology 형식 편집, 문서 보관·영구 삭제·scope 변경,
객체 편집 되돌리기, Knowledge 설정. 검토 화면의 결정 버튼과 삭제 확인은 Helper가 읽거나 누를 수 없다.

## 오류

| 증상 | 원인과 해결 |
|---|---|
| 문서가 `pending`에 머묾 | 문서 worker가 동작하지 않는다. 운영자 확인이 필요하다 |
| 문서 `failed` | 형식·암호화·크기를 확인하고 `document_ingest_retry` 또는 문서 화면에서 재시도 |
| `ready`인데 그래프가 비어 있음 | AI 추출은 별도로 진행된다. 추출 모델이 설정돼 있어야 하고(`/settings/knowledge/ai`) 후보는 `/knowledge/review`에 나타난다 |
| 의미 검색이 안 됨 | Embedding 모델이 없으면 어휘 검색만 동작한다. 관리자가 `/settings/knowledge/ai`에서 설정한다 |
| 녹음 작업 응답 유실 | `audio_request_status(operation, idempotencyKey)`로 조회한다. `operation`은 `recording.reserve`·`audio.submit`·`audio.retry`다. 다시 제출하지 않는다 |

도구 오류는 `<code>: <문장>` 형식이다. 문장을 그대로 인용하고 code로 행동을 정한다.

| code | 원인과 해결 |
|---|---|
| `studio_unauthorized` | Studio 위임이 거절됐다. 사용자가 다시 로그인한 뒤 다시 시도한다 |
| `studio_forbidden` | Studio 정책 거절(사용자 등급·한도). 재시도해도 성공하지 않는다 |
| `studio_unavailable`, `ai_rate_limited` | 일시 장애나 AI 요청 한도다. 문장이 알려 주는 시간 뒤에 다시 시도한다 |
| `conflict` | 읽은 뒤 대상이 바뀌었다. 다시 읽고 사용자가 원한 대상과 같을 때만 다시 요청한다 |
| `idempotency_conflict` | 같은 `idempotencyKey`에 다른 입력을 보냈다. 새 요청이면 새 키를 쓴다 |
| `access_denied`, `object_write_denied`, `team_not_current` | 권한이 없거나 그 팀의 구성원이 아니다. 우회하지 않는다 |
| `organization_storage_exceeded`, `pending_documents_exceeded`, `user_rate_exceeded` | 문서 저장·대기·업로드 한도다. 관리자가 한도를 바꾸거나 나중에 다시 올린다 |
| `invalid_input` | 입력이 틀렸다(ontology 규칙 위반 포함). 문장이 알려 주는 항목을 고친다 |
| `*_not_found` | 대상이 없거나 사용자가 볼 수 없다. ID를 확인한다 |
| 문서 재시도 거절 | `failed`인 문서만 다시 시도할 수 있다. `document_ingest_status`로 상태를 확인한다 |
| 녹음 영구 삭제 거절 | 녹음을 먼저 보관하고, 진행 중인 작업과 결과가 정해지지 않은 모델 요청이 끝난 뒤 삭제한다. 문장이 이유를 알려 준다 |
