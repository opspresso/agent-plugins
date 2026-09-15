# Workspace 작업 Agent 구성

Agent Studio의 프로젝트 이름과 관계없이 적용하는 공용 프로필이다. 프로젝트는 요청을 조율하고,
Workspace의 코딩 Runtime 또는 command가 파일 작업을 실행한다. Sandbox는 별도 MCP 서버가 아니다.
Agent Version에서 워크스페이스 도구를 활성화한다. 모델은 Models에서 Runtime별로 선택하고
프로젝트의 워크스페이스 도구 탭에서 소유자·관리자가 저장소와 기본 Runtime을 관리한다.
기본 저장소는 없으며 접근 모드 기본은 등록 + 신규다. 계정·Worker·이미지는 설치 측 설정이다.
저장소 고정·소유자 지정·모든 저장소·신규 자동 허용을 지원한다. 신규 모드는 Workspace 도구가
실제로 생성한 저장소를 자동 등록하며, 기존 저장소는 소유자·관리자가 명시적으로 등록한다.

## 설명과 시스템 프롬프트

설명 예시:

> Workspace와 Sandbox에서 코드·파일·데이터 작업을 수행하는 공용 에이전트. PR 리뷰, Issue 수정, 기능 구현, 리팩토링, 의존성 업그레이드, CI 실패 조사, 보안 수정과 프로젝트 생성을 지원하고 실제 검증·승인된 게시 결과를 제공한다.

시스템 프롬프트는 [workspace-agent.md](prompts/workspace-agent.md)를 그대로 사용한다.
작업별 상세 지침과 Git 예제는 연결 Skill에서 읽는다. 시스템 프롬프트에 특정 계정·저장소·Issue를 넣지 않는다.

## Skills 바인딩

| 작업 | Skill | 기본 완료 범위 |
|---|---|---|
| Review Pull Request | code-review | 해당 HEAD의 근거 있는 리뷰; 게시·수정은 요청된 경우만 |
| Fix Issue | fix-issue | 원인 수정과 회귀 검증 |
| Implement Feature | implement-feature | 관찰 가능한 요구 동작과 검사 |
| Refactor | refactor-code | 보존할 계약과 전후 동등성 검증 |
| Dependency Upgrade | dependency-upgrade | 대상 버전·manifest·lockfile·이관·검사 |
| CI Failure Investigator | ci-failure-investigator | 실패 run/attempt/SHA와 원인; 수정·재실행은 요청된 경우만 |
| Security Remediation | security-remediation | 지정된 문제의 수정·안전한 회귀 검증·남은 운영 조치 |
| Project Generator | project-generator | 실행 가능한 초기 프로젝트와 검증·사용법 |
| 실행 공간과 게시 조율 | workspace-task | 같은 Workspace/Session 재사용, 접수·완료·승인 구별 |
| 일반 파일·데이터·자동화 | sandbox-task | 원본 보존·변환·집계·스크립트와 결과 검사 |
| PR 제목·본문 | pr-description | 실제 변경과 검사에 근거한 설명 |

위 11개를 명시적으로 연결하면 동적 발견에 의존하지 않는다. 모든 Skill의 본문을 미리 읽거나
한 요청에 8개 개발 작업을 모두 적용하지 않는다. 모델과 최대 턴은 작업 규모·서비스 정책에 맞춘다.
긴 native 작업은 부모의 상태 조회 한도를 늘려 유지하지 않고, 동일 Workspace에서 후속 확인한다.

## GitHub MCP 프로필

`devops`의 github 선언은 유지하며 MCP 서버를 중복 등록하지 않는다. 같은 연결의 비밀이 아닌
version header를 `X-MCP-Toolsets: context,repos,issues,pull_requests,actions`로 설정하고 재발견한다.
모델·도구 선택을 수정해도 이 헤더를 유지한다. mcp.json 동기화가 소유하지 않는 설치 설정이다. 계정·토큰·OAuth scope는 복사하거나 확대하지 않는다.

GitHub는 원격 증거와 요청된 협업을 담당한다. Workspace 파일의 Git 게시와 역할이 겹치는
create_repository, create_branch, push_files, create_pull_request, merge_pull_request는 이 프로필에서 제외한다.
Issue·PR 읽기, 파일·commit·release 읽기와 검색을 연결하고 CI 조사에는 Actions의
actions_list, actions_get, get_job_logs 읽기 도구를 연결한다. workflow 실행/재실행 도구는 조사에 필요하지 않다.
새 저장소 생성에는 Workspace.create_repository를 사용하고 계정·저장소 조회를 위해 get_me와 조회 도구를
연결한다. 생성 전에 check_repository_access의 allowed·creation_allowed를 구분하고 서버 생성 결과의
base_branch를 검사한다. 이름이 허용 목록에 있다는 이유로 바로 clone하지 않는다.
사용자가 이미 사용하는 리뷰·Issue 피드백 도구는 요청 범위를 지키며 제공할 수 있다.

보안 경고 API는 별도 toolset·권한이 있을 때만 연결한다. 접근이 없으면 사용자 제공 advisory·스캔 결과와
현재 코드·의존성으로 대응한다. 접근 거절을 보안 문제가 없다는 뜻으로 해석하지 않는다.
코드·GitHub 자료는 [github MCP 운영 지침](../plugins/devops/org.opspresso.agent-studio/mcp/github.md)을 따른다.

## 실제 가능한 실행 범위

- 새 Workspace를 만들기 전에 options.current_workspace를 확인한다. 후속 요청은 run 또는 prepare_git다.
- Runtime 지정이 없는 자연어 작업은 허용된 codex 또는 다른 코딩 Runtime을 사용한다.
  이미 주어진 셸 스크립트·검증된 짧은 명령에는 command를 사용한다. CLI 프로젝트 생성도 자연어 코딩 작업이다.
- PR 리뷰·CI 조사만으로 충분한 작업에는 Sandbox를 만들지 않는다. 재현이 필요하면 실제 HEAD를 확인한다.
- start는 branch 기반 clone이다. 임의 SHA checkout, 허용되지 않은 fork, 다른 Runtime으로 전환하는 기능은 없다.
- Git-free 프로젝트 생성은 가능하다. 생성한 파일이 있는 공간에 저장소를 뒤늦게 attach할 수는 없다.
  게시할 프로젝트는 생성 전에 저장소 또는 소유자가 허용되는지 확인한다. GitHub 연결 자체가 Workspace 정책을 바꾸지는 않는다.
- CSV·JSON·로그 분석, 파일 변환, 일괄 처리와 보고서 재료 생성도 같은 공간에서 수행한다.
  첨부·Artifact의 자동 mount, 공개 미리보기, 다운로드 export, 호스트 접근은 제공되지 않는 한 약속하지 않는다.
- Chat 승인 응답에 source_chat_url이 있으면 승인 결과가 원래 채팅에 전달되고 같은 SDK 이력으로 재개된다.
  다단계 요청은 각 성공 후 다음 검토로 이어가며, 실패·거절·결과 불명인 동작을 자동 반복하지 않는다.
  PR 검사 pending은 ci_watch로 최대 30분 관찰하고 검사 결과가 같은 채팅을 재개한다.
  Playground·직접 Workspace 요청에는 원래 Chat을 임의로 지정하지 않는다.
- Workspace checks, 직접 실행한 검사와 GitHub CI를 구분한다. Git 게시·CI·릴리스·배포도 서로 다른 결과다.

## GitHub Webhook

프로젝트 Settings의 Webhook URL을 GitHub Payload URL로 사용하고 Content type은 application/json으로
설정한다. 프로젝트가 발급한 시크릿을 GitHub Secret에 넣으면 서명으로 인증하므로 커스텀 헤더가 필요 없다.
202는 접수 결과이며 실제 응답은 Trigger 이력에서 확인한다. Webhook은 machine actor로 실행되며
개인 사용자 Workspace 실행 권한이나 Git 승인 권한을 자동으로 얻지 않는다.

## 검증

저장소 정적 검사와 [행동 평가](../evals/engineering-workflows.json)를 사용한다. 시나리오 검토와
실제 모델·도구 실행 결과를 구분한다. 운영 확인은 읽기 작업과 격리된 Git-free fixture로 시작하고,
원격 게시·보안 설정 변경을 테스트 부작용으로 실행하지 않는다.
