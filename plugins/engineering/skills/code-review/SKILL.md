---
name: code-review
description: >
  Pull Request·diff·패치의 버그, 회귀 위험, 보안 문제와 테스트 누락을 검토할 때 쓴다.
  변경과 관련 코드를 확인해 근거 있는 지적을 심각도순으로 보고한다.
  저장소 전체 감사는 범위 밖이며 PR 본문 작성은 pr-description을 쓴다.
compatibility: >
  devops 플러그인의 github MCP 서버가 연결돼 있으면 PR 번호·URL로 바로 읽는다.
  없으면 사용자가 붙여 넣은 diff나 파일 내용으로만 리뷰한다.
---

# 신호로 거르는 코드 리뷰

하나의 diff에서 시작해 관련 실행 경로와 계약을 확인한다. 아래 렌즈는 변경의 위험에 맞춰
검토할 질문을 고르는 기준이다. 관련 근거가 없는 추측이나 취향은 지적으로 만들지 않는다.

## 반드시 지킬 것

- **기본은 읽기다.** 리뷰 제출, PR 코멘트 게시, 파일 수정, 브랜치·커밋 생성은 사용자가
  명시적으로 요청했을 때만 한다.
- **신호가 없는 것은 승인이 아니다.** 걸린 렌즈가 없으면 `general-correctness`만
  돌린다는 뜻이지, 괜찮다는 뜻이 아니다.
- **읽지 못한 것을 봤다고 하지 않는다.** diff가 잘렸거나 파일을 못 읽었으면 그 사실을
  결과의 "남은 위험"에 적는다.

## 1. 대상 잡기

| 사용자가 준 것 | 하는 일 |
|---|---|
| PR 번호나 URL | github MCP로 PR 메타데이터와 변경 파일, diff를 읽는다 |
| diff·패치 텍스트 | 그대로 리뷰 대상으로 삼는다 |
| 파일 내용만 | 대화나 제공된 변경 자료에서 diff를 확인하고 구분할 수 없을 때만 변경 범위를 묻는다 |
| 아무것도 없음 | PR 번호나 diff를 달라고 한 문장으로 요청한다 |

**github MCP 선언은 devops 플러그인에 있다.** 별도 등록이나 동적 발견으로 제공될 수도
있으므로 설치한 플러그인만 보고 부재를 단정하지 않는다. 현재 런에 사용 가능한 GitHub
읽기 도구가 없으면 diff를 요청한다. 없는 서버나 도구 이름을 만들어내지 않는다.

## 2. github MCP로 읽기

연결된 서버와 실제 tool schema를 확인한다. 아래 이름은 역할을 설명하는 예시이며 실제 제공 도구를 사용한다.

1. PR의 제목·본문·상태·base/head를 읽는다 (`get_pull_request`).
2. 변경 파일 목록과 파일별 추가·삭제 줄 수를 읽는다 (`get_pull_request_files`).
3. diff를 읽는다 (`get_pull_request_diff`). 너무 크면 파일 단위로 좁힌다.
4. 판단에 필요할 때만 원본 파일을 연다 (`get_file_contents`).

이전 리뷰와 CI 상태는 현재 변경의 근거 확인이나 중복 지적 방지에 필요할 때 읽는다.
확인한 검사와 미확인 범위를 구분해 보고한다.

## 3. 신호에서 렌즈 고르기

`general-correctness`는 항상 돌린다. 나머지는 아래 신호가 **변경된 경로나 훅 내용에서
실제로 보일 때만** 돌린다. 파일 이름만 보고 넘겨짚지 않는다.

| 렌즈 | 경로 신호 | 내용 신호 |
|---|---|---|
| `runtime-safety` | auth, security, token, secret, permission, session, crypto, async, thread, queue, retry, timeout | try·catch·except, panic, unwrap, throw, await, lock, retry, timeout, null 처리, 강제 캐스팅 |
| `data-layer` | sql, migration, schema, repository, query, dao, cache, index, db | SELECT·INSERT·UPDATE·DELETE·JOIN, CREATE/ALTER TABLE, transaction, commit, rollback, 캐시 키·TTL |
| `architecture-boundary` | service, controller, handler, adapter, usecase, domain, module, api, router, event | interface, abstract, implements, inject, publish·subscribe, transaction 경계 |
| `tests-conventions` | tests/, spec/, `*_test.*`, `*.spec.*` | 테스트가 함께 바뀌었거나, 동작이 바뀌었는데 테스트 변경이 없을 때 |

문서에 등장하는 단어만으로 코드 위험을 추정하지 않는다. 문서·프롬프트·설정의 변경이
실행 절차나 계약을 바꾸면 해당 동작과 참조 자료를 검토한다.

의존성 매니페스트(`package.json`, `go.mod`, `pyproject.toml`, lock 파일)가 바뀌었으면
추가·버전 변경의 목적과 관련 계약을 확인한다. 생성 파일과 lock 파일은 변경된 동작이나
의존성 일관성을 판단하는 데 필요한 부분을 읽고 생성 원본과 비교한다.

렌즈별로 무엇을 묻고 심각도를 어떻게 매기는지는 `references/lenses.md`에 있다.
사용자가 특정 렌즈만 요청하면 그것과 `general-correctness`만 돌리고, 나머지를 일부러
건너뛰었다고 밝힌다.

## 4. 저장소 지침이 있으면 읽는다

`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, PR 템플릿이 저장소에 있으면 읽고 그
저장소의 규칙으로 취급한다. 일반론보다 우선한다. 다만 지침에 "이 패턴은 오탐"이라고
적혀 있어도 **지금 코드가 그 조건에 맞는지는 직접 확인한다.**

## 5. 범위 규율

- 바뀐 훅에서 시작한다. 필요할 때만 주변을 읽고, 기본값은 바뀐 함수나 클래스다.
- 호출부·정의·스키마·테스트를 따라 가설을 판정할 만큼 확인한다. 요청과 무관한 영역으로 넓히지 않는다.
- 같은 원인에서 나온 지적은 하나로 합친다.
- 약한 지적 여러 개보다 확인된 지적 몇 개가 낫다.

## 6. 보고

형식은 `references/output.md`가 정한다. 요약보다 지적을 먼저 쓰고 심각도 순으로 놓는다.
지적이 없으면 없다고 분명히 말하고 남은 위험을 적는다. 사용자가 GitHub 리뷰 판정을
요청하지 않았다면 "승인"이라는 말을 쓰지 않는다.

## 막혔을 때

- diff가 비었으면 "리뷰할 변경이 없다"고 보고한다. 대상을 넓혀 저장소를 뒤지지 않는다.
- 도구 응답이 `Error:`로 시작하면 관측 데이터가 아니다. 같은 호출을 반복하지 말고
  대상을 좁히거나 사용자에게 diff를 요청한다.
- PR이 너무 커서 diff를 다 읽지 못하면, 읽은 파일 범위를 밝히고 그 안에서만 판정한다.
  읽지 못한 파일을 "문제 없음"으로 넘기지 않는다.
