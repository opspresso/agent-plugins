# Agent Memory connection

Register the installation's `/api/mcp` endpoint separately in Tools; Agent Memory
is not a bundled server in this repository. Set its credential in the installing
side's encrypted header field, then bind the server to the intended Agent's
current configuration. Do not put credentials in descriptions or operator notes.

The following console text describes the current scoped Memory and document
ingestion contract. Confirm the deployed tools before using this example.
Neither the description nor the notes configure account access or permissions.

## Description

```text
현재 호출자의 권한으로 접근 가능한 Memory·문서·지식 그래프에서 결정·규칙·경험과 근거를 검색할 때 사용합니다. 사용자가 지정한 정보를 조직·팀·개인 범위의 Memory나 문서로 저장하며, 실제 범위는 서버의 인증·권한과 도구 schema를 따릅니다.
```

## Operator notes

```markdown
# Agent Memory 연결

## 접근 범위

X-User-Email 없는 조직 Agent token은 조직 범위에 한정됩니다.
검증된 활성 멤버의 X-User-Email을 전달하면 해당 멤버의 권한을 적용합니다.
Studio가 이 예약 헤더를 구성하므로 Agent 설정에서 신원을 임의로 덮어쓰지 않습니다.
X-Tenant-Id와 X-Conversation-Id는 접근 권한을 부여하지 않습니다.

## 도구와 완료 상태

| 도구 | 역할과 확인 조건 |
|---|---|
| recall | 장기 Memory 회상 |
| context_search | Memory·문서·지식 그래프 검색 |
| remember | 지정 scope에 Memory 저장 |
| forget | manage 권한과 현재 version으로 보관 처리(archive) |
| document_ingest | 텍스트 문서 처리 접수 |
| document_ingest_status | ready이면 검색 가능한 문서로 안내 |

실제 도구 목록과 schema가 기준입니다.

## 연결과 자동 회상

1. Test connection으로 도구 목록 조회를 확인합니다.
2. 사용할 Agent의 현재 설정에 서버를 연결하고 필요한 도구를 허용합니다.
3. 대표 요청을 실제 실행해 접근 범위를 확인합니다.
4. 자동 회상이 필요하면 memoryRecall을 켜고 recall을 명시적으로 바인딩합니다.

차단되거나 승인이 필요한 recall은 사전 회상에서 제외됩니다.
동적 검색으로 찾은 서버는 사전 회상 대상이 아닙니다.

## 인증값 교체

서버의 token을 재생성했으면 등록된 Authorization 헤더와 Agent별 헤더 오버라이드를
필요한 범위에서 갱신합니다. 인증값을 메모·예시·응답에 적지 않습니다.

이 본문은 운영자 메모이며 모델에 전달되지 않습니다. 저장·변경 권한과 응답 규칙은 Agent의 시스템 프롬프트 또는 연결 Skill에 둡니다.
```

Test connection checks discovery, not a read, write or worker run. Test a scoped
read through the Agent before claiming the connection works for its intended
user. Document ingestion is accepted work until `document_ingest_status` reports
ready; automatic recall searches Memory, not document chunks or graph nodes.
Agent Memory IDs are source identifiers, not Studio artifact IDs.
