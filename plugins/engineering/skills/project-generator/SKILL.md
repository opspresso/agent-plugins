---
name: project-generator
description: >
  새 웹 앱·API·CLI·라이브러리·자동화 프로젝트의 실행 가능한 초기 구조를 만들 때 쓴다.
  목적과 스택·실행 환경을 확인하고 최소 기능·설정 예시·실행 방법을 생성해 검증한다.
  기존 프로젝트 기능 추가는 implement-feature이며 새 원격 저장소 생성·공개 배포는 별도 요청이다.
metadata:
  org.opspresso.agent-studio.icon: folder-plus
---

# 새 프로젝트 생성

사용할 수 있는 프로젝트를 만든다. 디렉터리와 빈 파일만 만든 것을 구현 완료라고 하지 않는다.

## 생성 위치와 입력

목적·핵심 기능·사용 형태·언어/스택·실행 환경과 결과 위치를 확인한다. 사용자가 고른 기술을 유지하고,
필요 없는 인증·결제·클라우드·외부 서비스를 기본으로 추가하지 않는다. 중요한 정보가 없으면
짧게 확인하고, 이미 정해진 부분은 진행한다.

호스트 앱에서는 Agent Forge MCP로 실행한다. 연결된 `workspace-task`가 있으면 Workspace 준비 절차를 읽는다.
사용자 지정 Runtime을 우선하고, 미지정이면 사용자가 선택한 Forge Workspace profile을 따른다. native Runtime에는
완결된 자연어 작업을 전달하며 command인 경우 실제 실행할 셸 스크립트를 구성한다.
CLI·명령행 도구를 만든다는 뜻과 command Runtime에서 이미 작성된 셸을 실행한다는 뜻을 구분한다.

- 기존 저장소에 생성·게시할 요청이면 그 저장소의 Git 호스트 `origin`과 저장소 경로(`repository`)로 Git `prepare`를 먼저 실행한다.
  저장소를 Forge에 등록하는 단계는 없다.
- Git 없이 생성할 요청이면 `prepare` 없이 시작한다. 사용자가 지정하지 않은 저장소를 임의로 선택하지 않는다.
- 현재 Workspace가 있으면 파일 목록을 확인하고 같은 Workspace에서 이어간다. 기존 파일을 덮지 않는 상대 경로를 사용한다.
- Git 준비는 기존 작업 파일을 덮어쓰지 않는다. Git 없는 공간에 먼저 생성한 파일을 나중에 저장소로
  자동 게시할 수 있다고 약속하지 않는다. Git 게시가 필요하면 생성 전에 대상을 정한다.

## 원격 저장소 준비

profile의 저장소 규칙이 이름을 허용해도 원격 저장소가 존재하거나 clone 가능하다는 뜻은 아니다. 새 저장소 생성이
요청됐으면 파일 작업 전에 아래 순서를 완료한다.

1. 요청한 owner/name과 GitHub 연결을 확인한다. Forge에서는 `git_connections`의 `hosts`에서 `origin`이 `https://github.com`인
   host의 `status`와 `account`를 읽는다. `status`가 `connected`가 아니면 그 host의 `connectUrl`을 사용자에게 주고,
   사용자가 Agent Studio에서 연결한 뒤 이어간다. 연결을 피하려고 다른 계정·token·생성 도구를 쓰지 않는다.
   Forge는 GitHub에만 저장소를 만든다. GitLab 프로젝트는 사용자가 GitLab에서 만든다.
2. 생성에 쓸 Workspace profile이 그 이름을 허용하는지 확인한다. `repositoryMode`가 `new`이면 유효한 모든 이름,
   `selected`는 `repositories`, `owners`는 그 owner의 이름, `all`은 모든 이름을 허용한다. 허용되지 않으면
   profile 소유자가 Forge 콘솔에서 profile을 바꿔야 한다고 알린다. 다른 이름의 저장소를 만들거나 profile을 임의로 넓히지 않는다.
3. 제공된 조회 도구로 같은 이름의 저장소를 확인한다.
   404는 비공개 저장소 접근 거절일 수도 있다. 다른 이름·fork·공개 전환으로 우회하지 않는다.
4. Forge `repository_create`에 `origin: "https://github.com"`, `profileId`, `profileRevision`, `repository: "owner/name"`,
   선택 `description`, `private`, `requestKey`를 보낸다. 공개 범위는 사용자 요청을 따르고 정해지지 않았으면 `private: true`다. 단, Agent Runway로 배포할 앱은 `app-delivery` 절차에 따라 `private: false`다. Runway는 Studio 관리자가 Project의 비공개 checkout을 허용한 저장소만 인증해서 clone한다.
   - 오류 `git_connection_required`와 503은 영수증을 남기지 않는다. `git_connection_required`이면 오류의 `connectUrl`을 사용자에게 주고
     사용자가 연결한 뒤에, 503이면 `retryAfterSeconds` 뒤에 같은 `requestKey`로 다시 요청한다.
   - `status:"created"`이면 Forge가 초기 commit을 만들었다. 저장소를 따로 등록하지 않는다. 영수증의 `result.origin`·`result.repository`를
     Git `prepare`의 `origin`·`repository`로, 실제 `result.defaultBranch`를 `baseBranch`로 쓴다.
   - `created`인데 `allowed:false`이면 현재 profile이 그 저장소를 허용하지 않는다. 다시 만들지 않는다.
     profile 소유자가 profile의 `repositories`에 추가해야 한다고 알린다.
   - `failed`는 생성이 거절된 것이다. 영수증의 `error`로 원인을 확인한다.
   - `unknown`이거나 응답을 잃었으면 생성을 반복하지 않는다. `repository_lookup_request`·`repository_get`으로 영수증을 읽는다.
     `requiresUserDecision`이면 사용자가 대상을 확인한다. 대상이 존재해도 이 요청이 만들었다는 증거가 아니다.
     사용자의 저장소로 확인되면 그 저장소를 `prepare`에 지정한다. `repositoryMode`가 `new`인 profile은 이 저장소를 허용하지 않으므로
     profile 소유자가 `repositories`에 추가해야 한다.
   - Forge 생성 기능이 없으면 해당 환경의 실제 저장소 권한 범위에서 제공된 GitHub 생성 도구로 초기화할 수 있다.
     그 저장소도 profile의 저장소 규칙이 허용해야 `prepare`된다. `new`는 Forge가 만든 저장소와 `repositories`의 저장소만 허용한다.
5. 기존 저장소가 비어 있으면 clone할 branch가 없다. 첫 commit을 만드는 지원 경로와 요청 범위를 확인하고
   초기화한다. 존재하는 파일을 덮거나 Git 보호 경계를 우회하지 않는다.
6. 준비된 저장소의 `origin`·`repository`와 기본 branch(`baseBranch`)로 Git `prepare`를 실행한다. 실패하면 네트워크·권한·빈 저장소·없는 branch를
   구분하고 확인된 원인을 고친 뒤 같은 Workspace에서 다시 준비한다. 새 Workspace 생성으로 해결하지 않는다.
   `git_repository_not_found`는 연결된 계정이 그 저장소를 볼 수 없다는 뜻이다. 다시 연결하라고 하지 않고 저장소 이름과 그 계정의 권한을 확인한다.

## 구현과 검증

1. 코딩 Runtime에 목적·스택·생성 경로·최소 동작·검사 방법을 전달한다. command Runtime에는
   자연어 단계가 아닌 실제 비대화형 스크립트를 전달한다.
2. 공식 생성기·템플릿 또는 작은 수동 구조 중 목적에 맞는 것을 선택한다. 생성기가 기존 파일을
   지우거나 원격 Git·telemetry·인증을 요구하는지 확인하고 현재 실행 환경에 맞춘다.
3. 핵심 기능, 의존성·lockfile, 필요한 환경변수 예시와 실행·검사 방법을 만든다. 실제 시크릿은 넣지 않는다.
4. 설치·빌드·테스트 또는 CLI/API smoke 검증을 실행한다. 서버 프로세스가 종료될 수 있는 Sandbox의
   주소를 지속적인 공개 서비스 주소로 안내하지 않는다. 브라우저가 없으면 시각 검증은 미실행으로 밝힌다.

생성 파일 경로, 실행 명령, 구현한 최소 기능과 검증 결과를 전달한다. Workspace 파일과 별도
다운로드 Artifact는 다르며, 실제 제공된 전달 도구가 없으면 Workspace 링크를 제공한다.
내부 파일명은 상대 경로를 코드로 표시하고 `/workspace/...`를 다운로드 링크로 만들지 않는다.
호스트 앱에서 저장소를 지정한 프로젝트 생성은 사용자가 제한하지 않으면 새 작업 브랜치에서 구현·검증 후
`workspace-task`의 Git 게시 절차로 커밋·푸시·PR까지 추가 승인 없이 완료한다.
Git-free 결과물에는 원격 게시를 추가하지 않는다. main 반영·태그·릴리즈·배포는 별도 요청과 확인을 따른다.
