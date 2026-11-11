---
name: app-delivery
description: >
  앱 하나를 저장소 생성·개발부터 리소스·빌드·테스트·배포·서비스 확인까지 Agent Runway와 Agent Forge로 진행할 때 쓴다.
  application.yaml로 앱을 선언하고 pipeline을 고른 뒤 Agent Runway project_apply·resource_create·deploy·promote로
  pipeline의 단계마다 배포하고 URL을 확인한다.
  코드 변경만 필요하면 implement-feature, 기존 GitOps 설정 변경은 gitops-change를 쓴다.
metadata:
  org.opspresso.agent-studio.icon: rocket
---

# 앱 전달

사용자가 요청한 앱을 실행 중인 서비스로 만든다. 저장소·코드·`application.yaml`·리소스·배포·응답하는 URL이
모두 확인될 때 완료다. PR이나 이미지 push만으로 완료라고 하지 않는다.

필요한 연결: Agent Runway MCP(`pipeline_list`, `project_apply`, `resource_create`, `deploy`, `promote` 등)와 Agent Forge MCP(Workspace·Git).
둘 중 하나가 없으면 할 수 있는 작업까지만 진행하고, 없는 연결과 남은 작업을 알린다.
사용자는 저장소가 있는 Git 호스트를 Agent Studio의 프로필 → Git 계정에서 연결해야 한다([저장소 접근](#저장소-접근)).

## 배포 모델

- **환경**: 관리자가 정한 배포 대상이다(기본 설치는 `dev`, `prod`). 환경의 규칙은 승인(`approval`)과 `sandbox` 두 가지다.
  sandbox 환경(기본 `dev`)의 Variable만 Forge Run에 전달된다.
- **pipeline**: 관리자가 정한 배포 경로다. cloud, target type(`eks`: 클러스터의 Pod, `eb`: Elastic Beanstalk 인스턴스),
  architecture(`amd64` 또는 `arm64`), trigger(push 배포를 켠 Project에서 배포를 시작하는 push)와 단계 목록을 가진다.
- **단계**: pipeline에 들어 있는 환경이다. 목록 순서가 승격 순서이고, 단계마다 크기(`small`·`medium`·`large`)가 있다.
  앱 주소는 단계의 위치가 정한다. 마지막 단계의 주소에만 환경 이름이 붙지 않는다.
- **Project**: 저장소 하나이고 pipeline 하나로 배포한다. 단계별 크기, trigger, 마지막 단계의 주소 형식을 자기 값으로 바꿀 수 있다.
- **push 배포**: Project마다 켜고 끄는 기능이다. 켠 Project만 trigger와 맞는 push를 첫 단계에 배포한다.
  켜지 않은 Project는 요청(`deploy`)으로만 배포한다([push 배포](#push-배포)).
- **`application.yaml`**: 앱의 빌드·테스트·실행 방법과 `secrets`·`env`만 선언한다. 환경·리소스·크기·trigger·cloud·target type·architecture는
  파일에 없다. 이 값들은 pipeline, `project_configure`, `resource_create`가 정한다.

## 1. 요구사항, 이름, pipeline

1. 앱의 목적·핵심 기능·데이터·외부 API와 배포할 환경을 확인한다. 정해진 부분은 묻지 않는다.
2. 저장소 owner를 정한다. 사용자가 정하지 않았으면 Agent 지침이 정한 기본 owner를 쓰고, 그것도 없으면 묻는다.
3. 이름(slug)을 정한다. `^[a-z][a-z0-9-]{1,30}[a-z0-9]$`이고 설치의 환경 이름으로 끝날 수 없다(예: `-dev`, `-prod`).
   `agent-`·`addon-`·`delivery-`·`kube-`로 시작하는 이름과 `istio`·`argocd`·`default`·`system`은 쓸 수 없다.
   저장소 이름과 같게 하면 추적이 쉽다. 주소는 Project pipeline의 마지막 단계가 `https://<slug>.<도메인>`, 그 밖의 단계가 `https://<slug>-<env>.<도메인>`이다.
   Project가 `suffixEveryStage`를 켜면 마지막 단계도 `https://<slug>-<env>.<도메인>`이다([5. 운영과 변경](#5-운영과-변경)).
   단계의 주소는 `project_status`의 `environments[].host`로 확인한다.
4. [pipeline 선택](#pipeline-선택)으로 pipeline을 정한다.

### pipeline 선택

1. 저장소에 Project가 이미 있으면 그 Project의 pipeline을 쓴다. `project_status`의 `pipeline`이 이름·architecture·trigger·단계를 준다.
   `project_ensure`와 `project_apply`는 기존 Project의 pipeline을 바꾸지 않는다. 사용자가 다른 pipeline을 요청했을 때만
   [5. 운영과 변경](#5-운영과-변경)의 `project_configure`로 바꾼다.
2. 새 Project이고 사용자가 pipeline을 정했으면 그 이름을 쓴다.
3. 사용자가 정하지 않았으면 `pipeline_list`를 읽고 다음 조건에 모두 맞는 pipeline을 고른다.
   - `stages`에 사용자가 요청한 환경이 있다.
   - `architecture`: 저장소의 Dockerfile base image와 native 의존성이 그 architecture로 빌드된다.
   - `type`: 앱의 배포 형태와 맞는다. Runway 리소스(DB·cache·bucket)가 필요한 앱은 `eks` pipeline을 고른다.
     `resource_create`는 `eks`가 아닌 pipeline에서 `target_unsupported`로 거부된다.
   - `default`가 조건에 맞으면 `default`를 고른다.
4. 조건에 맞는 pipeline이 둘 이상이고 요청과 저장소로 고를 수 없을 때만 `AskUser`로 한 번 묻는다.
   후보마다 이름·`type`·`architecture`·단계 순서를 보여 준다.
5. 조건에 맞는 pipeline이 없으면 Project를 만들지 않는다. 없는 조건을 알리고, 관리자가 Agent Runway 콘솔 `/admin/pipelines`에서
   pipeline을 추가해야 한다고 안내한다.

고른 이름은 새 Project를 만드는 `project_ensure` 또는 `project_apply`의 `pipeline`에 넘긴다. `default`는 `pipeline`을 생략한다.
설치에 `default` pipeline이 없는데 `pipeline`을 생략하면 `pipeline_required`로 실패하고 메시지가 이름 목록을 준다.
이름이 틀리면 `pipeline_not_found`다.

## 저장소 접근

Agent Runway는 한 사용자의 Git 계정으로 저장소를 읽는다. 요청한 배포는 요청한 사용자의 계정으로,
push로 시작한 배포는 그 Project의 push 배포를 켠 사용자의 계정으로 읽는다([push 배포](#push-배포)).
공개 저장소와 비공개 저장소의 절차가 같다. Runway에는 저장소를 연결하거나 등록하는 단계가 없고, Runway는 deploy key를 만들지 않는다.
사용자는 저장소가 있는 Git 호스트를 Agent Studio의 프로필 → Git 계정에서 한 번 연결한다.

- **Git 계정이 필요한 호출**: 새 Project를 만드는 `project_ensure`·`project_apply`와 `ref`를 보내는 `deploy`다.
  호출한 사용자가 그 Git 호스트를 연결했고, 연결한 계정이 저장소를 읽을 수 있어야 한다.
- **Git 계정이 필요 없는 호출**: 이미 있는 Project의 `project_ensure`·`project_apply`, `release`를 보내는 `deploy`, `promote`, `rollback`, 배포 승인이다.
- `ref`를 보낸 `deploy`는 응답하기 전에 저장소를 읽고 `ref`를 commit으로 확정한다. 아래 code로 거절되면 Deployment는 만들어지지 않았다.

| code | 뜻 | 행동 |
|---|---|---|
| `git_connection_required` | 사용자가 그 Git 호스트를 연결하지 않았거나 다시 연결해야 한다 | 오류 메시지에 있는 Agent Studio 연결 링크(`connectUrl`)를 사용자에게 준다. 사용자가 연결한 뒤 같은 호출을 다시 한다 |
| `repository_access_denied` | 연결한 Git 계정이 저장소를 볼 수 없다. `push_enable`에서는 저장소의 webhook을 관리하는 역할이 없다는 뜻일 수도 있다 | 다시 연결하게 하지 않는다. 저장소 이름과 그 계정의 저장소 권한을 사용자와 확인한다 |
| `ref_not_found` | 저장소에 그 branch·tag·commit이 없다 | `ref`를 확인해 고친 뒤 다시 호출한다 |
| `source_too_large` | 그 commit의 소스 아카이브가 설치의 한도를 넘는다 | 사용자에게 알린다. 저장소를 줄이거나 운영자가 한도를 올려야 한다 |
| `git_host_removed` | Agent Studio가 그 Git 호스트를 더 이상 Git 호스트로 두지 않는다 | 사용자에게 알린다. 운영자가 Agent Studio에 그 호스트를 다시 등록해야 한다 |
| `invalid_repository` | 새 Project의 저장소가 이 설치의 Git 호스트에 있지 않거나, 저장소 주소가 `<host>/<path>` 형식이 아니다 | 메시지가 알려 주는 Git 호스트와 저장소 주소를 사용자와 확인한다 |

## 기존 저장소의 Project 만들기

사용자가 기존 저장소를 Project로 추가하자고 하면 확인 절차를 사용자에게 넘기지 않고 이어서 진행한다.
요청이 이미 정한 작업(예: "프로젝트를 추가, dev 배포"의 Project 생성·`application.yaml` 추가·`dev` 배포)는 그 요청을 동의로 보고 묻지 않는다.
요청과 저장소로 정할 수 없는 결정만 `AskUser`로 한 번 묻는다. 이미 끝난 작업은 묻지 않는다.

1. Forge `git_connections`로 저장소가 있는 Git 호스트의 연결 상태를 확인한다. 그 host의 `status`가 `connected`가 아닐 때만
   host의 `connectUrl`을 사용자에게 주고, 사용자가 Agent Studio에서 연결한 뒤 이어간다. Runway도 이 연결로 저장소를 읽는다.
   저장소를 Forge나 Runway에 등록하는 단계는 없다. Forge Git `prepare`에는 그 host의 `origin`과 저장소 경로(`repository`)를 보낸다.
2. 기본 branch의 `application.yaml`, `Dockerfile`, health 경로를 확인한다. 사용자에게 파일을 만들라고 하지 않는다.
3. `application.yaml`이 없으면 [pipeline 선택](#pipeline-선택)으로 pipeline을 정하고 `project_ensure`(`repository`, `default`가 아니면 `pipeline`)로
   Project를 확인한 뒤 `project_status`로 pipeline과 단계를 읽는다. `slug`는 넘기지 않는다.
   Agent Runway가 저장소 이름으로 정하고, 그 slug가 예약돼 있으면 다음 접미사(`-2`, `-3` …)를 고른다. 삭제된 Project의 slug도 영구히 예약된다.
   저장소에서 언어·포트·테스트 명령과 앱이 기본 설정으로 연결하는 백엔드를 읽어 `application.yaml` 초안과 리소스 계획을 만든다.
   - 초안: `spec.name`에는 응답의 `project.slug`, `spec.owner`에는 `project.owner.subject`를 그대로 쓴다. 자리표시자를 남기지 않는다.
     환경·리소스·크기·trigger는 쓰지 않는다.
   - 리소스 계획: 코드가 읽는 Variable 이름에 맞춰 리소스 이름과 template을 정한다. Variable은 `<리소스 이름>_<class 키>`이므로, 예를 들어
     `CACHE_VALKEY_URL`을 읽는 앱에는 `valkey` template의 리소스 `cache`를, 접두어 없는 `DATABASE_URL`을 읽는 앱에는 slug 이름의
     PostgreSQL 리소스(보통 `pool-postgres`)를 계획한다. 앱이 실행될 모든 단계에 같은 이름·template으로 만든다.
     리소스를 피하려고 어느 단계에서든 앱 기능을 끄는 값(예: `REDIS_ENABLED: "false"`)을 넣지 않고, 그런 선택지를 묻지도 않는다.
   사용자가 추가를 요청했으면 초안과 리소스 계획을 보여 주고 바로 진행하며, 요청하지 않았을 때만 `AskUser`로 묻는다.
   묻는 경우의 예: "application.yaml이 없습니다. 아래 내용으로 만들어 추가할까요?" 진행하면 [2. 저장소와 코드](#2-저장소와-코드)의 PR 절차로 추가한다.
   `Dockerfile`이나 health 경로가 없으면 같은 질문에 함께 포함한다.
4. 병합되면 [3. 선언 적용과 리소스](#3-선언-적용과-리소스)로 `project_apply`와 `resource_create`까지 진행한다.
   배포는 사용자가 요청했을 때만 한다. 요청이 없으면 `AskUser`로 첫 단계 배포 여부를 묻는다.

`project_ensure`·`project_apply`·`deploy`가 Git 계정이나 저장소 권한 때문에 거절되면 [저장소 접근](#저장소-접근)의 code별 행동에 따른다.

## 2. 저장소와 코드

1. 새 저장소는 연결된 `project-generator` 절차로 Forge `repository_create`를 실행한다. 공개 범위는 사용자 요청을 따르고,
   정해지지 않았으면 `private: true`다. Runway는 공개·비공개 저장소를 같은 방법으로 읽으므로 배포 때문에 공개로 만들지 않는다.
   기존 저장소의 공개 범위를 임의로 바꾸지 않는다.
2. 앱이 DB·버킷을 쓰면 코드를 쓰기 전에 sandbox 환경(기본 `dev`)의 리소스를 만든다. `project_ensure`(`repository`, `default`가 아니면 `pipeline`)로
   Project를 만들고 `resource_create`(`project`, `environment`, `template`, `name`, `idempotencyKey`)를 호출한 뒤 `resource_get`으로 `ready`를 한 번 확인한다.
   `template`은 `resource_catalog`에서 `available`이 `true`인 것을 고른다. 앱 DB는 보통 공유 풀의 `pool-postgres`, 파일은 `bucket`이다.
   기본 `name`은 Project slug다. 이 리소스의 Variable에는 접두어가 없다(`DATABASE_URL`). `main`은 다른 이름처럼 `MAIN_` 접두어가 붙는다.
   접속 정보는 Agent Runway가 저장한다. 값은 Chat·코드·로그에 쓰지 않고 Variable 이름만 쓴다.
3. 코드를 구현한다. 배포에 필요한 조건은 다음과 같다. 세부 규칙과 예시는 [application.yaml과 배포 조건](references/application-yaml.md)을 읽는다.
   - 저장소 루트의 `application.yaml`(`spec.owner`에 Project 소유자의 Studio subject).
     부모가 `application_validate`로 통과한 전체 내용을 task에 그대로 넣고, runtime이 그 내용으로 파일을 쓰게 한다. runtime은 스키마를 모르므로 직접 짓게 하지 않는다.
   - `Dockerfile`: Project pipeline의 architecture 하나(`linux/amd64` 또는 `linux/arm64`, `project_status`의 `pipeline.architecture`)로 빌드되고,
     `PORT` 환경 변수의 포트에서 HTTP를 받는다. 빌드는 commit의 소스 아카이브로 하므로 `.git`·submodule·Git LFS 객체에 의존하지 않는다.
   - health 경로(기본 `/health`): 리소스를 쓰는 앱은 매 요청에서 각 리소스에 실제로 연결하고(PostgreSQL은 `SELECT 1`)
     기동 시 migration이 성공했을 때만 2xx를 반환한다. Runway의 verify는 이 경로만 확인하므로 고정 응답은 DB 장애를 숨긴다.
   - 테스트 명령: 외부 리소스 없이 끝나야 한다. Runway의 test 스텝에는 Agent Runway Variable이 없다.
4. Forge Run의 checks(test·lint·build)로 확인한다. sandbox 환경의 리소스가 `ready`이면 Forge가 Run의 명령 환경에 그 Variable을
   넣으므로 migration과 DB 연동을 실제 DB로 확인한다. 이 확인은 Forge에서만 가능하다. Runway의 test 스텝에는 DB가 없다.
5. task가 끝나면 부모가 `run_submit`의 Git `review` Run을 내고, diff의 `application.yaml` 전체를 `application_validate`로 다시 검사한다.
   거부되면 커밋하지 않고 오류 필드를 고치는 task를 낸 뒤 `review`부터 다시 한다.
6. 부모가 Git `commit`·`push`·`pull-request` Run으로 PR을 만든다. Git 작업을 task에 넣지 않는다. native Runtime은 커밋할 수 없다.
   `pull-request`는 승인을 만들지 않는다.
7. PR의 CI가 통과하면 Git `merge`를 제출한다. 보호 작업이므로 Run이 승인을 기다리며 `approvalUrl`을 반환한다.
   그 링크를 답변에 그대로 넣어 사용자에게 준다(`WaitForServiceWork`로 턴을 끝낼 때도 그 메시지에 넣는다). 병합 Run이 `succeeded`인지 확인한 뒤 3절로 간다. 승인 없이 다른 경로로 병합하지 않는다.
   Forge는 `main`으로만 병합한다. Workspace의 기준 브랜치가 `main`이 아니면 `merge`가 `git_action_unsupported`로 거절되고 승인은 만들어지지 않는다.
   이때는 사용자가 Git 호스트에서 그 PR을 병합해야 한다고 알리고, 병합된 뒤 3절로 간다.

## 3. 선언 적용과 리소스

1. 배포할 revision(기본 병합된 main)의 `application.yaml` 내용을 그대로 `project_apply`에 넘긴다(`repository`, `application`).
   새 Project를 `default`가 아닌 pipeline으로 만들 때만 `pipeline`을 함께 넘긴다. 기존 Project에는 `pipeline`을 넘기지 않는다.
   Project의 pipeline과 다른 이름을 넘기면 `pipeline_mismatch`로 실패한다.
   새 Project를 만드는 `project_apply`는 호출한 사용자의 Git 계정이 저장소를 읽을 수 있는지 확인한다([저장소 접근](#저장소-접근)).
   Runway는 그 revision의 파일 SHA-256이 적용한 내용과 같은지 확인하므로, 한 글자라도 다르면 `application_changed`로 실패한다.
2. `project_apply`는 리소스를 만들지 않는다. 응답의 `application.environments`가 단계마다 `resources`(이미 있는 리소스와 상태)와
   `missingSecrets`를 준다. 앱이 기본 설정으로 시작하는 데 필요한 리소스 중 없는 것을 `resource_create`로 만든다.
   - 리소스는 환경 하나에 속한다. 앱이 실행될 단계마다 한 번씩, 같은 `name`·`template`으로 호출한다. 그 단계의 첫 Deployment 전에 만든다.
   - 호출마다 새 `idempotencyKey`를 쓴다. 응답을 잃었을 때만 같은 key로 다시 호출한다.
   - `environment`는 Project pipeline의 단계여야 한다. 아니면 `environment_not_in_pipeline`이다. Runway는 이 조건을 그 환경의 target보다 먼저 확인한다.
   - `sandbox`가 `false`인 template은 sandbox 환경에 만들 수 없다(`template_not_in_sandbox`). 그 단계에는 같은 Variable 이름을 주는
     template(예: `rds-postgres` 대신 `pool-postgres`)을 같은 `name`으로 만든다. 그런 template이 없으면 사용자에게 알린다.
   - `eks`가 아닌 pipeline은 `target_unsupported`다. 연결 값의 Variable 이름을 `application.yaml`의 `secrets`에 선언하고 사용자가 값을 입력하게 한다.
3. 배포를 요청받았으면 리소스가 `ready`가 되기를 기다리지 않고 바로 [4. 배포와 승격](#4-배포와-승격)의 `deploy`를 호출한다.
   생성 중(`pending`)인 리소스는 Deployment가 `resources` 스텝에서 기다리고, Studio가 그 Deployment를 끝까지 따라간다.
   Deployment는 리소스를 만들지 않는다. 리소스가 `failed`이면 원인을 보고한다.
4. `missingSecrets`가 있으면 각 항목의 `url`(또는 `secret_request`가 준 링크)을 사용자에게 준다. 값은 Chat으로 받지 않는다.
   사용자가 입력했다고 하면 `project_status`에서 그 단계의 `missingSecrets`가 비었는지 확인한다.
5. `invalid_application`이면 오류의 필드를 고쳐 2절의 PR로 다시 반영한다. 이전 apiVersion의 파일은 거부되며, 메시지가 고칠 내용을 알려 준다.

## 4. 배포와 승격

단계 순서와 승인 규칙은 Project의 pipeline과 설치의 환경이 정한다. 먼저 `project_status`를 읽는다.
`pipeline.stages`가 승격 순서와 크기를, `environments[]`의 `position`·`next`·`approval`·`deployBlockers`·`promoteBlockers`가 단계별 상태를 준다.
기본 설치의 `default` pipeline은 `dev`(승인 없음) → `prod`(소유자 승인)이다.

1. 첫 단계(`position`이 `0`인 환경)에 `deploy`(`project`, `environment`, `ref`, `idempotencyKey`)를 호출한다. 기본 ref는 `main`이다.
   Agent Runway가 호출한 사용자의 Git 계정으로 저장소를 읽고, ref를 pipeline의 architecture로 build해 Release(`r<n>`)를 만들고 배포한다.
   Git 계정이나 `ref` 때문에 거절되면 [저장소 접근](#저장소-접근)의 code별 행동에 따른다.
   push 배포를 켠 Project(`project_get`의 `push.state`가 `on`)는 trigger(`project_status`의 `pipeline.trigger`)와 맞는 push를
   Runway가 첫 단계에 배포한다. 그래서 병합 직후의 `deploy`가 `deployment_in_progress`일 수 있다. 이때는 새로 요청하지 않고 `project_status`의 그 단계 `inProgress.deploymentId`를
   `deployment_get`으로 한 번 읽어 그 Deployment를 따른다. push 배포를 켜지 않은 Project는 병합만으로 배포되지 않으므로 `deploy`를 호출한다.
2. 다음 단계는 `promote`(`project`, `from`, `idempotencyKey`)로 같은 Release를 배포한다. `from` 단계의 `next`가 배포될 단계다.
   다시 build하지 않으므로 앞 단계에서 검증한 이미지가 그대로 간다.
   - 첫 단계가 아닌 단계에 `deploy`로 ref를 보내면 `release_not_promoted`다. 마지막 단계에서 `promote`하면 `no_next_environment`다.
   - `approval: owner` 환경은 `awaiting_approval`과 `approvalUrl`을 반환한다. 링크를 사용자에게 주고 소유자가 Agent Runway 콘솔에서 승인하게 한다.
     승인 요청은 24시간 뒤 만료된다. 소유자가 Studio의 승인 카드에서 그 호출을 직접 승인했으면 Runway가 소유자 승인으로 받아 기다리지 않고 진행한다.
3. Studio가 Deployment를 따라가다 끝나면 결과를 Chat에 전달하고 대화를 이어 준다. 같은 Deployment를 기다리며
   `deployment_get`을 반복 호출하지 않는다. 사용자가 진행 상황을 물으면 한 번 조회해 스텝(`step`)을 알린다.
   응답을 잃었으면 같은 key로 `deployment_lookup_request`를 읽는다.
4. 결과를 확인한다.
   - `succeeded`: verify 스텝이 새 rollout을 확인하고 `url`의 health 경로가 2xx를 반환한 것까지 검증했다는 뜻이다.
     `url`, health 경로, Release 이름과 `revision`(짧은 SHA)을 알린다. HTTP 요청 도구가 없어도 health를 미검증으로 보고하지 않는다.
   - `failed`: `step`, `errorCode`, `statusMessage`를 확인하고 `deployment_logs`(`deploymentId`, `step`)로 원인을 읽는다.
     workflow가 시작되기 전의 실패와 `resources` 스텝에는 로그가 없다(`deployment_not_started`). 이때는 `errorCode`와 `statusMessage`로 판단한다.
     코드 문제는 2절로 고친 뒤 다시 배포한다. `delivery_unavailable`은 플랫폼 문제다. 코드나 선언을 바꾸지 말고
     Deployment ID와 스텝을 사용자에게 알린다. `application_changed`이면 배포한 ref의 `application.yaml`을
     읽어 그 내용을 3절로 적용하거나, 적용한 선언과 같은 파일을 가진 ref로 다시 배포한다. 다른 ref의 파일을 적용하지 않는다.
     같은 실패를 원인 확인 없이 다시 시작하지 않는다.
   - `rejected`: 소유자가 거절했거나 승인이 만료됐다(`approval_expired`). 다시 요청할지 사용자에게 확인한다.
5. 요청이 거부되면 오류 코드에 따라 처리한다.
   - `environment_not_ready`: 시간이 해결하지 못하는 문제다. 메시지가 원인을 알려 준다. `failed` 리소스와 값 없는 secret은 3절로 준비한다.
     적용한 `application.yaml`이 없으면 `project_apply`를 먼저 한다. 환경에 pipeline의 target type·architecture를 실행할 target이 없거나
     계정 접근이 확인되지 않았으면 관리자가 고쳐야 하므로 메시지를 사용자에게 전한다.
     `deployBlockers`의 `pending` 리소스는 배포를 막지 않는다. Deployment가 기다린다.
   - `resource_failed`·`resource_timeout`(Deployment의 `errorCode`): 기다리던 리소스가 실패했거나 2시간 안에 준비되지 않았다. 그 리소스의 상태를 보고한다.
   - `environment_not_in_pipeline`: 그 환경은 Project pipeline의 단계가 아니다. `project_status`의 단계 중에서 고른다.
     Runway는 이 조건을 target·적용한 선언·Release·준비 상태보다 먼저 확인한다. 단계가 아닌 환경의 요청은 다른 문제가 있어도 이 code로 거절된다.
   - `no_next_environment`: `promote`의 `from`이 pipeline의 마지막 단계다. 승격할 단계가 없다.
   - `release_outdated`: 그 Release는 다른 architecture로 build됐거나 이전 버전의 `application.yaml`로 build됐다(`release_list`의 `deployable: false`).
     다시 배포할 수 없다. 첫 단계에 ref를 `deploy`해 새 Release를 만든 뒤 승격한다.
   - `host_conflict`: 요청한 주소를 같은 Project의 다른 환경이 쓰고 있다(pipeline의 마지막 단계나 주소 형식을 바꾼 뒤에 생긴다). 오류 메시지의 조치를 따른다:
     그 환경에 다시 배포하거나, 그 환경의 서비스를 `service_remove`로 삭제하거나, 진행 중인 배포가 끝나기를 기다린다.
   - `deployment_in_progress`: 진행 중인 Deployment가 끝나기를 기다린다.
6. 배포한 Release에 문제가 있으면 `rollback`(`project`, `environment`, `idempotencyKey`)으로 그 환경의 직전 Release를 다시 배포한다.
   승격은 필요 없다. 되돌릴 Release가 없으면 `no_rollback_target`이다. `project_status`의 `rollbackTo`가 대상 Release다.

### push 배포

`project_get`·`project_list`의 `push.state`가 Project의 push 배포 상태다.

| `push.state` | 뜻 |
|---|---|
| `off` | push로 배포하지 않는다. 요청(`deploy`)으로만 배포한다 |
| `on` | trigger와 맞는 push가 첫 단계에 배포한다. Runway는 push 배포를 켠 사용자(`push.enabledBy`)의 Git 권한으로 저장소를 읽는다 |
| `delegation_invalid` | 켠 사용자의 Git 위임이 Agent Studio에 없다. push로 시작한 Deployment가 모두 `push_delegation_invalid`로 실패한다. 다시 켜야 한다 |

- **켜기**: `push_enable`(`project`)은 사용자가 push 배포를 요청했을 때만 호출한다. Project 생성이나 배포 요청을 push 배포 요청으로 보지 않는다.
  - 켜면 Runway가 저장소에 push webhook을 만들고, push마다 켠 사용자의 Git 권한으로 저장소를 읽는다.
    이 허용은 push 배포를 끄거나 그 사용자가 Agent Studio의 프로필 → Git 계정에서 위임을 폐기할 때까지 유지된다. 호출하기 전에 사용자에게 이 내용을 알린다.
  - Studio Chat은 호출마다 사람의 승인 카드를 보여 주고, 승인된 호출만 실행한다. 승인할 사람이 없는 실행에는 `push_enable` 도구가 없다.
    도구가 없으면 Project 소유자나 Studio 관리자가 Agent Runway 콘솔의 Project 설정(`/projects/<slug>/settings`)에서 켜야 한다고 안내한다.
  - Project 소유자나 Studio 관리자만 켤 수 있다(`owner_required`). 켜는 사용자의 Git 계정은 저장소의 webhook을 관리하는 역할이어야 한다:
    GitHub 저장소는 `admin`, GitLab 프로젝트는 Maintainer 이상이다. 아니면 `repository_access_denied`다.
  - `git_connection_required`·`git_host_removed`는 [저장소 접근](#저장소-접근)에 따른다. `policy_refused`는 Agent Studio가 그 사용자에게 Git 위임을 주지 않는다는 뜻이다.
    사용자 등급이 허용하지 않거나, 그 Git 계정의 위임이 한도에 찼다. 한도에 찼으면 사용자가 프로필 → Git 계정에서 위임을 폐기한다.
    `identity_unavailable`은 메시지가 알려 주는 시간 뒤에 다시 호출한다. `source_refused`는 Git 호스트가 webhook을 거절한 것이며 메시지가 이유를 준다.
  - 다시 호출하면 webhook secret과 위임을 새로 만들고, 그 뒤의 push는 다시 켠 사용자의 권한으로 읽는다. 중간에 실패한 켜기도 다시 호출하면 끝난다.
- **끄기**: 사용자가 요청하면 `push_disable`(`project`)을 호출한다. 소유자나 Studio 관리자만 끌 수 있고(`owner_required`), 끄는 데에는 Git 계정이 필요 없다.
  응답의 `remoteCleanup`이 `skipped`이면 저장소에 webhook이 남았고, `delegationRevoked`가 `false`이면 Agent Studio에 Git 위임이 남았다.
  두 경우 모두 push 배포는 꺼졌다. 응답의 `message`가 남은 것과 다음 행동을 알려 주므로 사용자에게 그대로 전한다.
  남은 위임은 push 배포를 켠 사용자가 Agent Studio의 프로필 → Git 계정에서 폐기한다. `push_disable`을 다시 호출해도 그 위임은 폐기되지 않는다.
- **push로 시작한 Deployment의 실패**: Runway는 빌드 직전에 켠 사용자의 권한으로 소스를 읽는다. 읽지 못하면 Deployment가 `prepare` 스텝에서 실패한다.

| `errorCode` | 뜻 | 행동 |
|---|---|---|
| `push_delegation_invalid` | 켠 사용자가 Agent Studio에서 위임을 폐기했거나, 그 Git 호스트의 연결을 해제했거나, 다른 계정을 연결했다. `push.state`가 `delegation_invalid`가 된다 | 사용자에게 알린다. 사용자가 요청하면 `push_enable`로 다시 켠다 |
| `git_connection_required` | 켠 사용자가 그 Git 호스트를 다시 연결해야 한다. `push.state`는 바뀌지 않는다 | 켠 사용자가 Agent Studio에서 다시 연결해야 한다고 알린다. 다시 연결하면 다음 push부터 배포된다 |
| `repository_access_denied` | 켠 사용자의 Git 계정이 저장소를 볼 수 없다. `push.state`는 바뀌지 않는다 | 사용자에게 알린다. 그 계정의 저장소 권한을 확인하거나, 권한이 있는 소유자·관리자가 push 배포를 다시 켠다 |
| `git_host_removed` | 운영자가 그 Git 호스트를 Agent Studio 설정에서 뺐다 | 운영자가 호스트를 되돌려야 한다고 알린다. 되돌리면 다음 push부터 배포된다 |
| `checkout_failed` | push한 commit이 저장소에 없거나, 빌드가 소스 아카이브를 풀지 못했다 | 사용자에게 원인을 알린다 |
| `source_too_large` | 소스 아카이브가 설치의 한도를 넘는다 | [저장소 접근](#저장소-접근)과 같다 |

## 5. 운영과 변경

- **값 변경과 재시작**: Variable 값을 바꾸면 다시 배포해야 앱이 새 값을 읽는다. 그 환경에서 실행 중인 Release를 `deploy`(`release`)로 다시 배포한다.
- **앱 선언 변경**(port·health·command·build·test·`secrets`·`env`): `application.yaml`을 고치는 PR → 병합 → `project_apply` → 배포·승격 순서로 바꾼다.
  GitOps 저장소의 배포 값 파일을 직접 고치지 않는다.
- **크기·trigger·주소·pipeline 변경**: 파일 PR이 아니라 `project_configure`(`project`와 바꿀 필드)로 바꾼다. 다음 Deployment부터 적용된다.
  Project 소유자나 Studio 관리자만 호출할 수 있다(`owner_required`). 호출 전에 `project_status`의 `pipeline`을 읽는다.
  `stages[].overridden`과 `trigger.overridden`이 Project가 직접 정한 값을 표시한다.
  - `sizes`: 환경 이름별 크기다(예: `{prod: large}`). map 전체를 교체하므로, 자기 값을 유지할 단계를 모두 함께 넘긴다.
    빠진 단계는 pipeline의 크기로 돌아간다. `{}` 또는 `null`은 모두 제거한다.
    크기의 실제 값(CPU·memory·복제 수 또는 instance type)은 관리자가 환경의 target에 정한다. Deployment의 `size`가 적용된 값을 보여 준다.
  - `trigger`: `{kind: branch, pattern: main}` 또는 `{kind: tag, pattern: "v*"}` 형태다. `null`은 제거해 pipeline의 trigger로 돌아간다.
  - `installScript`: target type이 인스턴스를 쓰는 pipeline(`pipeline.machines`가 `true`)에서만 쓴다. secret을 넣지 않는다. `null`은 제거한다.
  - `suffixEveryStage`: `true`이면 마지막 단계의 주소도 `<slug>-<env>.<도메인>`이 된다. `false` 또는 `null`은 기본값으로 되돌려
    마지막 단계가 다시 `<slug>.<도메인>`을 쓴다. 현재 값은 `pipeline.suffixEveryStage`다. 실행 중인 서비스는 다음 Deployment까지
    기존 주소(`environments[].current.url`)를 유지하므로, 주소를 바꾸려면 그 단계에 다시 배포한다.
  - `pipeline`: `pipeline_list`의 이름이다. 생략하면 유지한다. cloud나 target type이 다른 pipeline은 Project에 서비스·리소스·Variable이
    남아 있으면 `project_in_use`로 거부된다. 새 pipeline에 맞지 않는 Project 값(단계가 아닌 환경의 크기 등)은 제거된다.
  - 생략한 필드는 그대로 유지된다. `invalid_pipeline`이면 메시지가 위반을 모두 알려 준다.
- **환경마다 다른 값**: 비밀이 아닌 값도 환경마다 다르면 `env`가 아니라 Variable로 둔다. 소유자가 Agent Runway 콘솔의
  Project 환경 변수 화면(`/projects/<slug>/variables`)에서 입력한다. 그 이름은 `application.yaml`의 `env`와 `secrets`에 쓰지 않는다.
  적용한 `env`에 있는 이름은 콘솔에서 입력할 때 `variable_declared`(409)로 거부된다.
- 장애 조사는 `incident-triage`를 쓴다. `eks` pipeline의 앱 namespace는 `app-<slug>-<env>`, Deployment 이름은 `app`이다.
- Project 삭제를 요청받으면 `project_delete`(`project`, `confirmation`: slug)를 한 번 호출한다. Studio가 사람에게 승인을 받은 뒤 실행되고,
  Agent Runway가 모든 환경의 서비스를 제거한 뒤 모든 리소스와 그 데이터, Project를 차례로 지운다. 되돌릴 수 없다.
  응답의 남은 서비스·리소스를 알리고, 사용자가 다시 물으면 `project_deletion_get`으로 한 번 확인한다.
  삭제는 먼저 Project의 push 배포를 끈다. 응답의 `remoteCleanup`이 `skipped`이거나 `delegationRevoked`가 `false`이면 `message`의 내용도 전한다([push 배포](#push-배포)).
  서비스 하나만 내리면 `service_remove`, 리소스 하나만 지우면 `resource_delete`를 쓴다. 둘 다 승인 뒤 실행된다.
  `service_remove`의 대상이 있는지는 `project_status`의 `environments[].removable`이 알려 준다. 실행 중인 서비스가 없어도
  실패한 배포가 앱을 남겼을 수 있으면 `true`다.

## 보고

진행한 작업마다 확인한 사실만 보고한다: 저장소와 PR, pipeline 이름, 적용한 선언의 SHA, 단계별 리소스 상태, Release 이름, Deployment ID·상태·URL.
승인을 기다리는 작업과 사용자가 할 일(승인, secret 입력, Git 호스트 연결)을 분리해 알린다.
