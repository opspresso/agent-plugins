---
name: workspace-task
description: >
  코드·파일·데이터·자동화 작업을 지속형 Workspace에서 실행하거나 이어갈 때 쓴다.
  기존 공간과 Session을 재사용하고 작업 접수·검증·Git 게시 단계를 조율한다.
  실행에는 Workspace 도구가 필요하며 원격 자료를 읽는 것만으로 충분한 요청에는 공간을 만들지 않는다.
compatibility: >
  Agent Studio의 Workspace 빌트인과 활성화된 Worker를 사용한다.
  Skill 설치가 Runtime·저장소 권한·계정 연결을 만들지는 않는다.
---

# 지속형 Workspace 작업 조율

Workspace는 파일·Git·Session을 유지하는 작업 공간이고 Sandbox는 그 파일을 실행하는 일시적 자원이다.
조율 Agent는 사용자 의도와 결과를 관리하고, 코딩 Runtime은 파일 수정·검사를 수행한다.
계정·저장소·브랜치·작업 파일은 사용자 요청에서 얻는다.

## 필요한 경로 선택

원격 PR·Issue·CI 자료만 읽으면 되는 작업은 제공된 MCP로 시작한다. 실제 파일 수정·재현·검증이
필요할 때 Workspace를 사용한다. 작업의 판단 기준은 연결된 해당 Skill을 읽는다.

| 요청 | 작업 Skill |
|---|---|
| PR·diff 리뷰 | code-review |
| 버그·Issue 수정 | fix-issue |
| 기존 제품 기능 구현 | implement-feature |
| 동작을 유지하는 구조 개선 | refactor-code |
| 의존성 업그레이드 | dependency-upgrade |
| CI 실패 조사·요청된 수정 | ci-failure-investigator |
| 지정된 보안 문제 대응 | security-remediation |
| 새 프로젝트 생성 | project-generator |
| 파일·데이터 처리·스크립트 자동화 | sandbox-task |

없는 Skill을 임의로 호출하지 않는다. 해당 작업을 직접 수행할 도구·자료가 있으면 그 범위에서
진행하고 한계를 알린다. Skill 선택 때문에 새로운 게시·수정 범위를 추가하지 않는다.

## 공간과 Runtime

1. `{"request":{"operation":"options"}}`로 workdir, 허용 Runtime·저장소와 current_workspace를 읽는다.
2. 선택된 공간은 `run`으로 이어간다. `workspace_id`를 생략할 수 있다. 사용자가 다른 기존 공간을
   지정했을 때만 `use_workspace`로 선택한다. start를 반복해도 새 작업이 접수되지 않는다.
3. 선택이 없을 때 `start`에 runtime, repository, base_branch, task를 보낸다. 저장소 작업은 두 Git
   선택 값을 모두 지정한다. 둘 다 null이면 Git-free다. 기본 저장소는 없으며 Runtime 미지정 시 options의 default_runtime을 따른다.
4. 사용자가 Runtime을 지정하지 않으면 options의 default_runtime을 따른다. 현재 허용 Runtime 목록에
   없으면 Models의 모델 연결 또는 프로젝트 기본 Runtime 설정을 확인한다. command에는 실제 실행할
   셸 스크립트를 구성해서 보내며 자연어 목록을 넣지 않는다. 코딩 Runtime에는 완결된 자연어 task를 보낸다.
   선택된 Runtime은 run에서 바꿀 수 없다.

새 저장소를 만들기 전 `check_repository_access`로 정확한 owner/name의 정책을 확인한다.
모드는 selected(등록 목록), owners(지정 소유자), all(GitHub 계정의 전체 접근), new(등록 목록과 신규 자동 등록)다.
`new`에서 allowed=false, creation_allowed=true이면 기존 접근은 막혀 있지만 요청한 신규 생성은 가능하다.
새 저장소는 Workspace의 create_repository를 사용한다. 서버가 생성·초기화하고 신규 모드의 허용 목록에
등록한다. MCP 생성 결과나 생성 시각을 등록 근거로 주장하지 않는다. 둘 다 차단되면 반환된
`repository_policy_url`을 관리자에게 전달한다. 일반 Agent가 정책 모드를 변경하거나 없는 관리 메뉴를 안내하지 않는다.
허용은 존재 여부가 아니다. clone 전 `check_repository`로 서버 계정의 접근·첫 commit·기준 branch를
확인한다. 새 저장소 생성 요청은 허용을 확인한 뒤 project-generator의 원격 준비 절차로 생성·초기화한다.
빈 저장소에는 clone할 main이 없으며, clone 실패는 Native task가 실행된 것이 아니다. 원인을 고친 뒤
같은 저장소의 선택된 Workspace에서 run으로 재개한다.

실행 지시를 만들 때는 [task 전달과 파일 작업](references/task-handoff.md)을 필요한 부분만 읽는다.
workdir는 실제 경로다. workspace_url·approval_url은 반환된 그대로 링크로 사용한다. URL이 없으면
workspace_path·approval_path의 상대 웹 경로를 그대로 사용하며 `/chats`에 `https://`를 붙이지 않는다.
파일은 workdir의 상대 경로로 다룬다.
`attach_repository`는 빈 Git-free 폴더에만 연결하며 이미 있는 파일을 덮거나 Git을 해제하지 않는다.

## 접수·완료·후속 요청

queued/running은 완료가 아니다. 반환된 run_id로 wait/status를 읽고 after_seq=0부터 next_seq로
출력을 이어간다. has_more면 남은 결과를 읽는다. 같은 작업을 새 ID로 재접수하지 않는다.
진전 없는 상태 조회를 연속 반복하지 말고 현재 상태와 링크를 제공한다. 부모 응답이 끝나도 작업은 계속된다.
reused=true, task_queued=false는 기존 공간만 반환한 것이다. 새 작업은 run으로 요청한다.

실행의 성공·실패·취소·중단과 실제 변경을 확인한다. 오류는 입력·환경·상태의 확인된 원인을 고친 뒤
같은 공간에서 이어간다. 경로·도구·권한 오류를 새 Workspace나 다른 Git 경로로 우회하지 않는다.
사용자가 작업 중지를 요청하면 cancel, 공간 종료를 요청하면 close를 사용한다. close는 선택과
파일을 보존하며 run·prepare_git가 종료된 공간도 복원한다. 일반 턴 완료나 PR 생성 때문에 닫지 않는다.

## 검증·게시·전달

Workspace의 checks, native task에서 직접 실행한 검사와 GitHub CI는 별개의 근거다.
checks=[]로 GitHub 검사가 없다고 하지 않는다. GitHub CI는 새 status의 pull_request.ci나
해당 SHA·run·attempt의 실제 실행 기록으로 확인한다. 릴리스 게시만으로 전체 빌드 완료를 추론하지 않는다.

Git 게시 요청에는 [Git 검토와 승인](references/git-actions.md)을 읽는다. 새 run은 미승인 검토를
취소하므로 파일 수정을 마친 뒤 검토한다. 실행 중·결과 불명 상태의 게시를 자동 반복하지 않는다.
Chat에서 만든 승인에 `source_chat_url`이 있으면 결과 전달 뒤 같은 채팅에서 자동 재개된다. 성공한
단계 뒤에 사용자 요청의 미완료 단계가 있으면 다음 검토를 준비한다. 한 단계의 승인·성공을 전체 요청
완료로 표현하지 않는다. PR 성공 결과에 ci_watch가 있으면 서버가 검사 완료를 기다렸다가 같은
채팅에 workspace_ci_result를 전달한다. 상태를 반복 조회하지 않고 기다린다. 실패·거절·결과 불명은
그대로 보고하며 같은 게시를 자동 재실행하지 않는다.
실제 변경, 검증 근거, 미완료 작업과 클릭 가능한 Workspace/PR/산출물 링크를 전달한다.
