# Workspace 작업 Agent 구성

호스트 앱의 Agent 이름과 관계없이 적용하는 공용 프로필이다. Agent는 요청을 조율하고,
Agent Forge의 Workspace와 코딩 Runtime 또는 command가 파일 작업을 실행한다. Studio는 Forge MCP 연결을 전담 specialist로 제공하고
Chat에서 접수한 실행의 결과를 원래 Chat에 전달한다. Forge는 Workspace profile·실행·Git 연결·보호 작업 승인·이력을 소유한다.
Sandbox는 Forge 내부의 일시 실행 자원이다.

## 실행 환경 설정

1. 설치 측에서 Studio의 Forge 연결(`FORGE_URL`, `FORGE_OIDC_CLIENT_ID`, `FORGE_ORGANIZATION_ID`)과 Forge worker·Sandbox·모델 gateway를 설정한다.
2. Agent에 Agent Forge Tools 항목을 연결한다. Studio는 MCP 요청마다 현재 사용자에게 위임한 단기 token을 보낸다.
   실행 도구에는 Agent 실행이 가능한 사용자 등급이 필요하다.
3. 사용자는 Forge 콘솔에서 Workspace profile(Runtime·중앙 모델·저장소 규칙·검사·배포 workflow)을 만들고 기본 profile을 선택한다.
4. 사용자는 Forge 콘솔의 Git 설정에서 GitHub 계정을 연결하고 사용할 `owner/repository`를 등록한다.
   Studio Tools의 Forge 상세 화면에 설정·이력 링크가 있다.

profile의 저장소 규칙 기본값은 `selected`(등록한 저장소만)이다. `owners`, `all`, `new`(새 이름의 저장소 생성 허용)도 있다.
규칙은 Git 권한을 넓히지 않는다. 보호 branch 게시·merge·tag·release·deploy는 Forge 콘솔에서 Workspace 소유자가 승인한다.

## 설명과 시스템 프롬프트

설명 예시:

> Workspace와 Sandbox에서 코드·파일·데이터 작업을 수행하는 공용 에이전트다.
> PR 리뷰, Issue 수정, 기능 구현, 리팩토링, 의존성 업그레이드, CI 실패 조사, 보안 수정과 프로젝트 생성을 지원한다.
> 구현·수정 작업은 검증과 작업 브랜치 PR까지 제공한다. 병합·태그·릴리즈·배포는 요청된 범위에서 조율한다.

시스템 프롬프트는 [workspace-agent.md](prompts/workspace-agent.md)를 그대로 사용한다.
코딩 요청의 기본 완료 범위는 새 작업 브랜치의 구현·검증·커밋·푸시·PR이다.
main 반영·태그·릴리즈·배포는 별도 사용자 요청과 확인을 따른다. 조회·리뷰나 게시 제한 요청은 그 범위를 지킨다.
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
Agent의 MCP 바인딩 헤더를 `X-MCP-Toolsets: context,repos,issues,pull_requests,actions`로 설정하고 재발견한다.
Forge가 Git 게시·배포를 담당하는 기본 프로필에는 `X-MCP-Readonly: true`도 설정한다.
모델·도구 선택을 수정해도 이 헤더를 유지한다. mcp.json 동기화가 소유하지 않는 설치 설정이다. 계정·토큰·OAuth scope는 복사하거나 확대하지 않는다.

GitHub는 원격 증거와 요청된 협업을 담당한다. Workspace 파일의 Git 게시와 역할이 겹치는
create_repository, create_branch, push_files, create_pull_request, merge_pull_request는 이 프로필에서 제외한다.
Issue·PR 읽기, 파일·commit·release 읽기와 검색을 연결하고 CI 조사에는 Actions의
actions_list, actions_get, get_job_logs 읽기 도구를 연결한다. workflow 실행/재실행 도구는 조사에 필요하지 않다.
새 저장소 생성에는 Forge `repository_create`를 사용하고 계정·저장소 조회를 위해 get_me와 조회 도구를
연결한다. 생성 전에 profile의 저장소 규칙이 그 이름을 허용하는지 확인하고, 생성 결과의 실제
`defaultBranch`로 Git `prepare`를 실행한다. 이름이 허용 목록에 있다는 이유로 저장소가 있다고 판단하지 않는다.
리뷰·Issue 피드백 게시까지 필요한 별도 프로필은 요청 범위에 맞는 쓰기 도구만 명시적으로 연결한다.
읽기 전용 기본 프로필은 해당 게시를 지원한다고 약속하지 않는다.

보안 경고 API는 별도 toolset·권한이 있을 때만 연결한다. 접근이 없으면 사용자 제공 advisory·스캔 결과와
현재 코드·의존성으로 대응한다. 접근 거절을 보안 문제가 없다는 뜻으로 해석하지 않는다.
코드·GitHub 자료는 [github MCP 운영 지침](../plugins/devops/org.opspresso.agent-studio/mcp/github.md)을 따른다.

## 실제 가능한 실행 범위

- 새 Workspace를 만들기 전에 `workspace_list`로 재사용할 공간을 확인한다. 후속 요청은 같은 Workspace의 `run_submit`이다.
- Runtime은 Workspace profile 또는 사용자의 명시적 지정을 따른다. 생성 뒤 Runtime은 바꿀 수 없다.
  이미 주어진 셸 스크립트·검증된 짧은 명령에는 command를 사용한다. CLI 프로젝트 생성도 자연어 코딩 작업이다.
- PR 리뷰·CI 조사만으로 충분한 작업에는 Workspace를 만들지 않는다. 재현이 필요하면 실제 HEAD를 확인한다.
- 저장소는 Git `prepare`로 `agent/` 작업 브랜치에 준비한다. 선택 `sourceRevision`으로 고정한 검토 Workspace는 게시할 수 없다.
- Git-free 프로젝트 생성은 가능하다. 게시할 프로젝트는 생성 전에 저장소가 profile 규칙에 맞는지 확인한다.
  GitHub 연결 자체가 profile 규칙을 바꾸지는 않는다.
- CSV·JSON·로그 분석, 파일 변환, 일괄 처리와 보고서 재료 생성도 같은 공간에서 수행한다.
  Chat 첨부의 자동 mount, 공개 미리보기, 다운로드 export, 호스트 접근은 제공되지 않는 한 약속하지 않는다.
  현재 Forge 도구에는 파일 인자가 없다.
- Studio Chat에서 접수한 실행은 terminal 결과가 원래 Chat에 한 번 전달된다. 보호 작업은 Forge 콘솔 승인 뒤 실행되고
  그 결과도 같은 방식으로 전달된다. 실패·거절·결과 불명인 동작을 자동 반복하지 않는다.
  CI 완료를 기다렸다가 자동으로 재개하는 기능은 없다.
- Run checks, 직접 실행한 검사와 GitHub CI를 구분한다. Git 게시·CI·릴리스·배포도 서로 다른 결과다.

## GitHub Webhook

Agent Settings의 Webhook URL을 GitHub Payload URL로 사용하고 Content type은 application/json으로
설정한다. Agent가 발급한 시크릿을 GitHub Secret에 넣으면 서명으로 인증하므로 커스텀 헤더가 필요 없다.
202는 접수 결과이며 실제 응답은 Trigger 이력에서 확인한다. Webhook은 machine actor로 실행되며
개인 사용자의 Forge 실행 권한이나 Git 승인 권한을 자동으로 얻지 않는다.

## 검증

저장소 정적 검사와 [행동 평가](../evals/engineering-workflows.json)를 사용한다. 시나리오 검토와
실제 모델·도구 실행 결과를 구분한다. 운영 확인은 읽기 작업과 격리된 Git-free fixture로 시작하고,
원격 게시·보안 설정 변경을 테스트 부작용으로 실행하지 않는다.
