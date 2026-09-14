---
name: workspace-task
description: >
  파일·코드·분석·자동화 작업을 지속형 Workspace에서 시작하거나 이전 작업에 이어서 수행할 때 쓴다.
  실행 상태, Diff와 검사 결과를 확인하고 Workspace와 세션을 재사용한다.
  실행에는 Workspace 도구 또는 동등한 격리 실행 기능이 필요하다.
compatibility: >
  Agent Studio에서는 프로젝트에 활성화된 Workspace 빌트인을 사용한다.
  Skill 설치만으로 실행 권한이나 저장소 연결이 생기지 않는다.
---

# 지속형 Workspace 작업

사용자가 정한 작업을 실행하고 후속 요청에 파일과 세션을 이어 준다. 저장소, 기준 브랜치,
변경 파일, 산출물과 게시 범위는 현재 사용자 요청에서 얻는다. 특정 계정이나 저장소를 기본값으로 정하지 않는다.

## 실행 경로

- 현재 제공된 도구 목록에서 Workspace 기능을 확인한다. 다른 클라이언트는 실제 도구 schema를 따른다.
  기능이 없으면 실행했다고 말하지 말고 필요한 연결과 수행 가능한 준비 작업을 알려 준다.
- Agent Studio의 `Workspace`는 `{"request":{"operation":"options"}}`로 현재 프로젝트의
  Runtime, 저장소와 검사 명령을 확인한다. 이 응답은 사용자의 변경·게시 허가가 아니다.
- 이미 반환받은 `workspace_id`가 있고 같은 작업을 이어가는 요청이면 `run`을 쓴다.
  새 `start`나 별도 저장소 복제로 이전 파일과 세션을 잃지 않는다.
- 새 작업은 `start`에 `runtime`, `repository`, `base_branch`, `task`를 보낸다.
  Git 없는 작업은 `repository`와 `base_branch`를 모두 `null`로 둔다.
  저장소 작업은 `options.repositories`의 허용 목록에서 사용자가 요청한 저장소를 선택한다.
  기본 `repository`와 다른 허용 저장소도 실제 요청의 `repository` 값으로 전달한다.
- `task`에는 실제 요청, 변경 범위와 검사 방법을 완결된 지시문으로 전달한다.
  코딩 Runtime에는 자연어 작업을, `command` Runtime에는 실행 가능한 비대화형 스크립트를 전달한다.
  선택하지 않은 도구·운영 자격증명을 사용할 수 있다고 가정하지 않는다.

## 진행과 후속 요청

`start`와 `run`의 `queued`는 접수 상태다. `workspace_id`, `run_id`, `workspace_path`를 보관하고
`wait`에 반환된 ID와 `after_seq`를 넘긴다. 최초 cursor는 0이며 이후에는 `next_seq`를 쓴다.
`status`도 같은 주소와 cursor로 결과를 읽는다. `has_more`면 같은 Run의 나머지 출력을 읽는다.

`succeeded`, `failed`, `cancelled`, `interrupted`를 구별한다. 성공한 검사와 실패·미실행 검사를
분리해 설명하고 Diff로 요청 밖 변경을 확인한다. 출력이 잘렸으면 전체 검토가 끝났다고 하지 않는다.
오래 걸려 현재 응답에서 완료를 확인할 수 없으면 실행 중임을 밝히고 Workspace 링크를 제공한다.
같은 작업을 새 ID로 다시 접수하지 않는다. 세션 종료나 통신 오류는 작업의 실패·취소를 뜻하지 않는다.

사용자가 중지를 요청하면 `cancel`, 작업 공간 종료를 요청하면 `close`를 사용한다.
일반 턴 완료만으로 Workspace를 닫지 않는다. 비활성 Sandbox가 정리된 뒤에도 후속 `run`은 저장된
파일과 native Session에서 복원된다. Git에서 무시하는 의존성·빌드 출력은 재생성한다.

## 검토와 게시

clone이나 로컬 재구현 요청은 원격 저장소 생성·fork·공개 게시의 허가가 아니다.
Workspace 기능이 없으면 GitHub의 쓰기 도구로 대체하지 말고 필요한 실행 환경을 알린다.

Commit·Draft PR·PR·병합·배포는 사용자의 요청 범위 안에서만 준비한다. Agent Studio에서는
`workspace_path`의 Git·배포 화면에서 현재 변경을 검토하고 명시적으로 승인한다.
Workspace 도구는 그 승인을 대신 누르거나 소비하지 않는다. GitHub 도구로 이 승인 경계를 우회하지 않는다.
main 반영은 PR과 검사 성공을 확인하며 배포는 기존 CI/CD 경로를 따른다.

최종 답변에는 실제 변경, 확인한 검사, 남은 작업을 담고 `workspace_path`를 주소로 하는 클릭 가능한 Markdown 링크를 제공한다.
없는 파일·테스트·커밋·PR·릴리스를 완료된 것으로 보고하지 않는다.
