---
name: workspace-task
description: >
  코드·파일·데이터·자동화 작업을 Agent Forge의 지속형 Workspace에서 실행하거나 이어갈 때 쓴다.
  기존 Workspace를 재사용하고 실행 접수·결과 확인·Git 게시 단계를 조율한다.
  실행에는 Forge MCP 도구가 필요하며 원격 자료를 읽는 것만으로 충분한 요청에는 Workspace를 만들지 않는다.
compatibility: >
  연결된 Agent Forge MCP(workspace_create, run_submit, run_result 등)가 필요하다.
  Workspace profile·실행·Git 연결·보호 작업 승인·이력은 Forge가 소유한다. Skill 설치가 Runtime·저장소 권한·계정 연결을 만들지는 않는다.
metadata:
  org.opspresso.agent-studio.icon: folder-code
---

# 지속형 Workspace 작업 조율

Workspace는 파일·Git·native Session을 유지하는 작업 공간이고 Sandbox는 그 파일을 실행하는 일시적 자원이다.
Agent Forge는 Workspace profile·실행·checkpoint·Git 연결·보호 작업 승인·실행 이력을 소유한다.
Studio는 Forge MCP 연결을 전담 specialist로 제공하고, Chat에서 접수한 실행의 terminal 결과를 원래 Chat에 한 번 전달한다.
계정·저장소·브랜치·작업 파일은 사용자 요청에서 얻는다.

사람이 profile·GitHub 연결·승인·이력을 다룰 때는 Forge 콘솔을 안내한다. Studio Tools의 Forge 상세 화면에
설정·이력 링크가 있고, Workspace·Run 응답의 `links`에 `settingsUrl`·`historyUrl`·`workspaceUrl`·`runUrl`·`approvalUrl`이 있다.
반환된 URL만 링크로 쓴다.

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

없는 Skill을 임의로 호출하지 않는다. Skill 선택 때문에 새로운 게시·수정 범위를 추가하지 않는다.
도구 이름·입력·응답 유실 처리는 [Forge 도구](references/forge.md)를 읽는다. 실제 발견한 schema가 우선한다.
Forge URL·조직·사용자 신원·provider credential·Git token은 서버 설정이며 모델이 입력하지 않는다.

## Workspace 준비

1. **profile 확인**: `profile_list`의 `selection`과 `profile_get`으로 사용할 `profileId`와 현재 `revision`을 읽는다.
   profile은 Runtime·모델·저장소 규칙·검사·배포 workflow를 정한다. 선택이 없으면 Forge 콘솔 설정에서 선택하도록 안내한다.
   사용자가 Runtime을 직접 지정하면 `model_channels`로 허용 채널을 확인하고 명시적 입력으로 만든다.
2. **기존 Workspace 재사용**: 같은 작업의 후속 요청은 `workspace_list`·`workspace_get`으로 찾은 Workspace에서 이어간다.
   `suspended` Workspace에도 `run_submit`을 바로 보낸다. Forge가 다시 시작하고 checkpoint를 복원한 뒤 실행하므로 `workspace_resume`을 먼저 부르지 않는다.
   `closed`는 다시 열 수 없다. Workspace당 실행은 한 번에 하나다.
3. **새 Workspace**: 재사용할 공간이 없을 때만 `workspace_create`에 `title`과 profile을 보낸다.
   `title`은 사용자 언어의 짧은 작업 목적이다. 셸 스크립트를 제목으로 복사하지 않는다.
4. **저장소 연결**: 저장소 작업이면 `git_connections`에서 등록된 저장소의 연결 `id`와 `defaultBranch`를 확인한다.
   `{kind:"git", action:"prepare"}` 실행으로 `agent/`로 시작하는 작업 브랜치를 준비한다. 등록되지 않은 저장소는
   사용자가 Forge 콘솔의 Git 설정에서 연결·등록해야 한다. credential을 인수로 보내지 않는다.
   새 저장소 생성은 project-generator의 원격 준비 절차를 따른다.

실행 지시를 만들 때는 [task 전달과 파일 작업](references/task-handoff.md)을 필요한 부분만 읽는다.
command Runtime에는 실제 셸 스크립트를, native Runtime(codex·claude·opencode)에는 완결된 자연어 작업을 보낸다.

## 접수·완료·후속 요청

- `queued`·`running`은 완료가 아니다. 접수 응답의 작업 참조(`work`)와 실행 ID·상태를 보고한다.
  Studio Chat에서 접수한 실행은 완료 결과가 원래 Chat에 전달된다. 같은 실행에서 상태를 반복 조회하지 않는다.
- 결과는 `run_result`로 읽는다. `lastEventSeq`까지 `run_events`를 읽고 `hasMore:false`를 확인한다.
  `outputLoss:true`나 `diffTruncated`는 출력 일부가 없다는 뜻이다. 완전한 결과로 표현하지 않는다.
- `interrupted`는 외부 효과가 불확실한 상태다. 자동으로 다시 실행하지 않는다.
- 응답을 잃으면 `run_lookup_request`·`workspace_lookup_request`로 원래 키의 접수를 확인한다.
  결과가 불확실한 작업을 새 키나 새 입력으로 다시 제출하지 않는다.
- 오류는 입력·환경·상태의 확인된 원인을 고친 뒤 같은 Workspace에서 이어간다. 새 Workspace나 다른 Git 경로로 우회하지 않는다.
- 사용자가 중지를 요청하면 `run_cancel`, 재시도를 요청하면 `run_retry`(현재 `profileRevision` 필요)를 쓴다.
  공간 정리는 사용자가 요청한 경우에만 `workspace_suspend`·`workspace_close`를 쓴다. 일반 턴 완료나 PR 생성 때문에 닫지 않는다.

## 검증·게시·전달

Run의 checks, native 작업에서 직접 실행한 검사와 GitHub CI는 별개의 근거다.
checks가 없다고 GitHub 검사가 없다고 하지 않는다. CI는 GitHub 읽기 도구로 해당 SHA의 실제 실행 기록을 확인한다.

코딩 요청은 사용자가 제한하지 않으면 새 작업 브랜치의 구현·검증·커밋·푸시·PR까지 포함한다.
[Git 게시와 확인](references/git-actions.md)을 읽고 review → commit → push → pull-request 실행으로 추가 질문 없이 진행한다.
조회·진단만 요청한 작업이나 Git-free 파일 처리에는 이 게시 범위를 추가하지 않는다.
보호 branch 게시·merge·tag·release·deploy는 별도 사용자 요청이 필요하고, Forge 콘솔에서 Workspace 소유자가 승인해야 실행된다.
모델은 승인할 수 없다. 실패·거절·결과 불명인 게시를 자동으로 반복하지 않는다.
실제 변경, 검증 근거, 미완료 작업과 반환된 Workspace·PR·승인 링크를 전달한다.
