---
name: app-delivery
description: >
  앱 하나를 저장소 생성·개발부터 리소스·빌드·테스트·배포·서비스 확인까지 Agent Runway와 Agent Forge로 진행할 때 쓴다.
  application.yaml로 앱을 선언하고 Project의 런타임과 pipeline을 정한 뒤 Agent Runway project_apply·resource_create·deploy·promote로
  각 pipeline의 단계마다 배포하고 URL을 확인한다.
  코드 변경만 필요하면 implement-feature, 기존 GitOps 설정 변경은 gitops-change를 쓴다.
metadata:
  org.opspresso.agent-studio.icon: rocket
---

# 앱 전달

사용자가 요청한 앱을 실행 중인 서비스로 만든다. 저장소·코드·`application.yaml`·리소스·배포·응답하는 URL이
모두 확인될 때 완료다. PR/MR이나 이미지 push만으로 완료라고 하지 않는다.

필요한 연결: Agent Runway MCP(`repository_inspect`, `pipeline_list`, `project_apply`, `resource_create`, `variables_set`, `deploy`, `promote` 등)와 Agent Forge MCP(Workspace·Git).
둘 중 하나가 없으면 할 수 있는 작업까지만 진행하고, 없는 연결과 남은 작업을 알린다.
사용자는 저장소가 있는 Git 호스트를 Agent Studio의 프로필 → Git 계정에서 연결해야 한다([저장소 접근](#저장소-접근)).

## 배포 모델

- **환경**: 관리자가 정한 배포 대상이다(기본 설치는 `dev`, `prod`). 환경의 규칙은 승인(`approval`)과 `sandbox` 두 가지다.
  sandbox 환경(기본 `dev`)의 Variable만 Forge Run에 전달된다.
- **pipeline**: 관리자가 정한 배포 경로다. trigger(push 배포를 켠 Project에서 그 pipeline을 시작하는 branch push 또는 tag push)와
  단계 목록을 가진다. cloud·target type·architecture는 갖지 않는다. `default`가 `true`인 pipeline은 pipeline을 정하지 않은 새 Project가 쓴다.
- **단계**: pipeline에 들어 있는 환경이다. 목록 순서가 승격 순서이고, 단계마다 크기(`small`·`medium`·`large`)가 있다.
  첫 단계만 `ref`를 받는다. 그다음 단계는 같은 pipeline의 바로 앞 단계에서 성공한 Release를 받는다.
- **Project**: 저장소 하나다. 런타임(`runtime`) 하나로 모든 단계에서 앱을 실행하고, pipeline 하나 이상을 순서대로 가진다.
  런타임은 cloud, target type(`eks`: 클러스터의 Pod, `eb`: Elastic Beanstalk 인스턴스), architecture(`amd64` 또는 `arm64`)다.
  Project의 pipeline끼리는 환경을 공유하지 않는다. 예: `main` push → `dev` pipeline과 `v*` tag → `stg` → 승격 → `prod` pipeline.
  Project는 pipeline마다 trigger, 단계마다 크기, 환경 이름 없는 주소를 받을 단계를 자기 값으로 정할 수 있다.
- **앱 주소**: 한 단계가 `https://<slug>.<도메인>`(환경 이름 없는 주소)으로, 그 밖의 환경이 `https://<slug>-<env>.<도메인>`으로 응답한다([앱 주소](#앱-주소)).
- **push 배포**: Project마다 켜고 끄는 기능이다. 켠 Project만 trigger와 맞는 push를 그 pipeline의 첫 단계에 배포한다.
  켜지 않은 Project는 요청(`deploy`)으로만 배포한다([push 배포](#push-배포)).
- **`application.yaml`**: 앱의 빌드·테스트·실행 방법과 `secrets`·`env`만 선언한다. 환경·리소스·크기·trigger·cloud·target type·architecture는
  파일에 없다. 이 값들은 Project의 런타임과 pipeline, `project_configure`, `resource_create`가 정한다.

## 질문

사용자에게 물을 것은 모아서 `AskUser` **한 번**으로 묻는다. 질문마다 `questions[]`의 항목 하나(`id`, `question`, `kind`, `options`, `default`)로 넣고,
도구가 확인한 값과 근거(예: "Node 24 (package.json engines) · port 8080 (Dockerfile EXPOSE)")와 `application.yaml` 초안은 `context`에 넣는다.
도구와 저장소로 확인할 수 있는 값(언어·버전·포트·health 경로·테스트 명령·환경 변수 이름·namespace 후보·런타임·pipeline)은 묻지 않는다.
요청이 이미 정한 작업(예: "만들어서 dev에 배포해")은 다시 확인하지 않는다. 물을 것이 없으면 묻지 않고 진행한다.

## 1. 요구사항, 이름, 런타임과 pipeline

1. 앱의 목적·핵심 기능·데이터·외부 API와 배포할 환경을 확인한다. 정해진 부분은 묻지 않는다.
2. 저장소의 Git 호스트와 owner(GitHub owner, GitLab 사용자 이름이나 group 경로)를 정한다. 사용자가 정하지 않았으면 `repository_namespaces`로
   연결 계정이 저장소를 만들 수 있는 namespace를 읽고, 하나뿐이면 그것을 쓰고 여럿이면 [질문](#질문)에 넣는다. 새 저장소의 owner는 짐작하지 않는다([2. 저장소와 코드](#2-저장소와-코드)).
3. 이름(slug)을 정한다. `^[a-z][a-z0-9-]{1,30}[a-z0-9]$`이고 설치의 환경 이름으로 끝날 수 없다(예: `-dev`, `-prod`).
   `agent-`·`addon-`·`delivery-`·`kube-`로 시작하는 이름과 `istio`·`argocd`·`default`·`system`은 쓸 수 없다.
   저장소 이름과 같게 하면 추적이 쉽다. 주소는 [앱 주소](#앱-주소)의 규칙을 따른다. `project_status`의 `environments[].host`가
   그 단계의 다음 배포가 받을 주소이고, `runningHost`가 실행 중인 서비스의 주소다.
4. [런타임과 pipeline 선택](#런타임과-pipeline-선택)으로 런타임과 pipeline을 정한다.

### 런타임과 pipeline 선택

1. 저장소에 Project가 이미 있으면 그 Project의 런타임과 pipeline을 쓴다. `project_status`의 `runtime`이 cloud·target type·architecture를,
   `pipelines[]`가 pipeline마다 이름·trigger·단계를 준다. `project_ensure`와 `project_apply`는 기존 Project의 런타임과 pipeline을 바꾸지 않는다.
   사용자가 다른 값을 요청했을 때만 [5. 운영과 변경](#5-운영과-변경)의 `project_configure`로 바꾼다.
2. 새 Project이고 사용자가 pipeline을 정했으면 그 이름을 쓴다. 사용자가 배포 흐름만 말했으면(예: "main은 dev, v 태그는 stg를 거쳐 prod")
   `pipeline_list`에서 그 trigger와 단계를 가진 pipeline을 하나씩 고른다.
3. 사용자가 정하지 않았으면 `pipeline_list`를 읽는다. `default`가 `true`인 pipeline들의 단계에 사용자가 요청한 환경이 모두 있으면
   pipeline을 넘기지 않는다. 새 Project는 `default`인 pipeline을 모두 쓴다. 아니면 다음 조건에 모두 맞는 pipeline 목록을 고른다.
   - 사용자가 요청한 환경이 모두 고른 pipeline 중 하나의 단계다.
   - 고른 pipeline끼리 같은 환경을 단계로 갖지 않는다. 같은 환경을 가지면 `pipeline_conflict`로 거부된다.
   - 사용자가 요청한 배포 시작 방법(branch push, tag push)과 trigger가 맞는다.
4. 런타임은 사용자가 정한 값과 저장소가 요구하는 값만 넘긴다. 넘기지 않은 항목은 첫 단계의 환경이 정한다.
   - `architecture`: 저장소의 Dockerfile base image와 native 의존성이 빌드되는 architecture다.
   - `type`: 앱의 배포 형태와 맞는다. Runway 리소스(DB·cache·bucket)가 필요한 앱은 `eks`다.
     `resource_create`는 런타임 type이 `eks`가 아닌 Project를 `target_unsupported`로 거부한다. `pipeline_list`의 `targetTypes`가 cloud별 type을 준다.
   - 모든 단계의 환경이 런타임 type의 target을 갖고 그 target이 런타임 architecture를 실행해야 한다. 아니면 `pipeline_incompatible`이다.
5. 조건에 맞는 조합이 둘 이상이고 요청과 저장소로 고를 수 없을 때만 `AskUser`로 한 번 묻는다.
   후보마다 pipeline 이름·trigger·단계 순서를 보여 준다.
6. 조건에 맞는 pipeline이 없으면 Project를 만들지 않는다. 없는 조건을 알리고, 관리자가 Agent Runway 콘솔 `/admin/pipelines`에서
   pipeline을 추가해야 한다고 안내한다.

고른 이름은 새 Project를 만드는 `project_ensure` 또는 `project_apply`의 `pipelines`(이름 배열, Project의 순서)에, 런타임은 `runtime`(`{cloud?, type?, architecture?}`)에 넘긴다.
`default`인 pipeline을 쓰면 `pipelines`를 생략한다. 설치에 `default` pipeline이 없는데 `pipelines`를 생략하면 `pipeline_required`로 실패하고 메시지가 이름 목록을 준다.
이름이 틀리면 `pipeline_not_found`다. 기존 Project에는 `pipelines`와 `runtime`을 넘기지 않는다.

## 저장소 접근

Agent Runway는 한 사용자의 Git 계정으로 저장소를 읽는다. 요청한 배포는 요청한 사용자의 계정으로,
push로 시작한 배포는 그 Project의 push 배포를 켠 사용자의 계정으로 읽는다([push 배포](#push-배포)).
공개 저장소와 비공개 저장소의 절차가 같다. Runway에는 저장소를 연결하거나 등록하는 단계가 없고, Runway는 deploy key를 만들지 않는다.
사용자는 저장소가 있는 Git 호스트를 Agent Studio의 프로필 → Git 계정에서 한 번 연결한다.
Git 호스트는 GitHub(github.com·GitHub Enterprise Server)와 GitLab(GitLab.com·self-managed GitLab)이다.
`repository`는 `<host>/<path>`다(예: `github.com/owner/todo`, `github.example.com/owner/todo`, `gitlab.example.com/apps/demo/todo`).
host가 없는 `owner/repo`는 github.com만 뜻하므로 다른 호스트의 저장소에는 host를 쓴다. GitLab은 group 경로 전체를 쓴다.
host 주소는 Forge `git_connections`의 `origin`에서 읽는다.

- **Git 계정이 필요한 호출**: 새 Project를 만드는 `project_ensure`·`project_apply`와 `release` 없이 호출하는 `deploy`(`ref`를 보내거나 생략)다.
  호출한 사용자가 그 Git 호스트를 연결했고, 연결한 계정이 저장소를 읽을 수 있어야 한다.
- **Git 계정이 필요 없는 호출**: 이미 있는 Project의 `project_ensure`·`project_apply`, `release`를 보내는 `deploy`, `promote`, `rollback`, 배포 승인이다.
- `release` 없는 `deploy`는 응답하기 전에 저장소를 읽고 `ref`를 commit으로 확정한다. `ref`를 생략하면 Git 호스트가 알려 주는
  저장소의 기본 브랜치를 쓴다. 아래 code로 거절되면 Deployment는 만들어지지 않았다.

| code | 뜻 | 행동 |
|---|---|---|
| `git_connection_required` | 사용자가 그 Git 호스트를 연결하지 않았거나 다시 연결해야 한다 | 오류 메시지에 있는 Agent Studio 연결 링크(`connectUrl`)를 사용자에게 준다. 사용자가 연결한 뒤 같은 호출을 다시 한다 |
| `repository_access_denied` | 연결한 Git 계정이 저장소를 볼 수 없다. `push_enable`에서는 저장소의 webhook을 관리하는 역할이 없다는 뜻일 수도 있다 | 다시 연결하게 하지 않는다. 저장소 이름과 그 계정의 저장소 권한을 사용자와 확인한다 |
| `ref_not_found` | 저장소에 그 branch·tag·commit이 없다. `ref`를 생략했으면 저장소에 기본 브랜치가 없다(커밋 없는 저장소) | `ref`를 확인해 고친 뒤 다시 호출한다. 기본 브랜치가 없으면 첫 커밋을 만든 뒤 배포한다 |
| `invalid_ref` | `ref` 형식이 틀렸다. `ref`를 생략했으면 저장소의 기본 브랜치 이름이 Runway의 `ref` 규칙에 맞지 않는다 | 형식을 고친다. 기본 브랜치 이름 때문이면 배포할 tag나 commit SHA를 `ref`로 보낸다 |
| `source_too_large` | 그 commit의 소스 아카이브가 설치의 한도를 넘는다 | 사용자에게 알린다. 저장소를 줄이거나 운영자가 한도를 올려야 한다 |
| `source_busy` | Runway가 한 번에 읽는 소스 아카이브 수가 한도에 있거나, 같은 Project의 다른 소스 아카이브를 읽는 중이다 | 메시지가 알려 주는 시간(10초) 뒤에 같은 호출을 다시 한다 |
| `git_host_removed` | Agent Studio가 그 Git 호스트를 더 이상 Git 호스트로 두지 않는다 | 사용자에게 알린다. 운영자가 Agent Studio에 그 호스트를 다시 등록해야 한다 |
| `invalid_repository` | 새 Project의 저장소가 이 설치의 Git 호스트에 있지 않거나, 저장소 주소가 그 호스트의 `<host>/<path>` 형식이 아니다(GitHub는 정확히 `owner/repo`, port가 있는 주소는 받지 않는다) | 메시지가 알려 주는 Git 호스트와 저장소 주소를 사용자와 확인한다 |

## 기존 저장소의 Project 만들기

사용자가 기존 저장소를 Project로 추가하자고 하면 확인 절차를 사용자에게 넘기지 않고 이어서 진행한다.
요청이 이미 정한 작업(예: "프로젝트를 추가, dev 배포"의 Project 생성·`application.yaml` 추가·`dev` 배포)는 그 요청을 동의로 보고 묻지 않는다.
요청과 저장소로 정할 수 없는 결정만 `AskUser`로 한 번 묻는다. 이미 끝난 작업은 묻지 않는다.

1. Forge `git_connections`로 저장소가 있는 Git 호스트의 연결 상태를 확인한다. 그 host의 `status`가 `connected`가 아닐 때만
   host의 `connectUrl`을 사용자에게 주고, 사용자가 Agent Studio에서 연결한 뒤 이어간다. Runway도 이 연결로 저장소를 읽는다.
   저장소를 Forge나 Runway에 등록하는 단계는 없다. Forge Git `prepare`에는 그 host의 `origin`과 저장소 경로(`repository`)를 보낸다.
2. Agent Runway `repository_inspect`(`repository`, 저장소에 Project가 있으면 `project`)를 한 번 호출한다. Runway가 사용자의 Git 계정으로 기본 브랜치를 읽고
   언어·버전·포트·health·테스트 명령·환경 변수(secret/env)·필요한 리소스와 `application.yaml` 초안(`application`), Dockerfile 초안(`dockerfile`),
   질문(`questions`), 없는 파일(`missing`)을 준다. 파일을 직접 읽어 짐작하지 않는다. 사용자에게 파일을 만들라고 하지 않는다.
   결과의 `directories`에 앱이 여럿이면 배포할 앱의 `directory`로 다시 호출한다.
   `git_connection_required`·`repository_access_denied`·`ref_not_found`·`source_too_large`·`source_busy`는 [저장소 접근](#저장소-접근)에 따른다.
   분석은 사용자당 한 번에 하나만 실행된다. `source_busy`는 `Retry-After` 뒤에 다시 호출하고, 그사이 다른 분석을 시작하지 않는다.
   `inspection_too_complex`(422)이면 `directories`에서 배포할 앱의 `directory`로 다시 호출한다. `limits.*Omitted`가 0이 아니면 결과가 잘린 것이므로 그 앱의 `directory`로 다시 분석한다.
   `detected.variables[].value`는 예시 파일(`.env.example` 등)의 기본값만 담는다. 커밋된 `.env`의 값은 읽지 않으므로, 값이 없는 이름은 질문 답이나 `variables_set`으로 채운다.
   `firstStage`는 Project의 첫 pipeline의 첫 단계(새 Project는 첫 `default` pipeline의 첫 단계)다. 리소스를 먼저 만들고 처음 배포할 환경이다.
   `entries`는 pipeline마다 첫 단계다. `deploy`가 `ref`를 받는 환경은 이것뿐이다.
3. `application.yaml`이 없으면 [런타임과 pipeline 선택](#런타임과-pipeline-선택)으로 런타임과 pipeline을 정하고
   `project_ensure`(`repository`, 필요하면 `pipelines`·`runtime`)로 Project를 확인한 뒤 `project_status`로 런타임·pipeline·단계를 읽는다. `slug`는 넘기지 않는다.
   Agent Runway가 저장소 이름으로 정하고, 그 slug가 예약돼 있으면 다음 접미사(`-2`, `-3` …)를 고른다. 삭제된 Project의 slug도 영구히 예약된다.
   초안은 `repository_inspect`의 `application.text`를 쓴다. `application.valid`가 `true`인지 확인하고, `false`면 `violations`를 고친다.
   `spec.name`·`spec.owner`는 그대로 둔다(Project가 있으면 응답의 `project.slug`·`project.owner.subject`와 같아야 한다). 환경·리소스·크기·trigger는 쓰지 않는다.
   - 질문: `questions[]`를 [질문](#질문)대로 `AskUser` 한 번에 모두 묻는다. 각 항목의 `id`·`text`·`kind`·`options`·`default`를 그대로 옮기고,
     `detected`의 값과 근거, 초안은 `context`에 넣는다. `detected`에 있는 값은 묻지 않는다. 질문이 없으면 묻지 않고 진행한다.
   - 답 반영: `field`가 가리키는 `application.yaml` 필드를 고친다. `variables.secret`에서 고른 이름은 `secrets`에 넣는다.
     `env.<NAME>`은 모든 환경에 같은 값이면 `env`에, 환경마다 다르면 적용 뒤 `variables_set`으로 둔다. `rename.<NAME>`은 코드와 선언의 이름을 함께 바꾼다.
     `test.enable`이 `false`면 `test`를 지운다. `dockerfile.generate`가 `true`면 `dockerfile.text`를 `dockerfile.path`에 커밋한다.
     고친 내용은 `application_validate`로 다시 확인한다.
   - 리소스 계획: `detected.resources[]`의 `template`과 `name`을 그대로 쓴다. 그 `name`이면 리소스의 Variable이 코드가 읽는 이름이 된다.
     `note`가 있으면 그 안내를 따른다. `template`이 `null`이면 그 연결 값을 `secrets`로 선언한다. 앱이 실행될 모든 단계에 같은 이름·template으로 만든다.
     리소스를 피하려고 어느 단계에서든 앱 기능을 끄는 값(예: `REDIS_ENABLED: "false"`)을 넣지 않고, 그런 선택지를 묻지도 않는다.
   사용자가 추가를 요청했으면 질문의 답을 받은 뒤 바로 [2. 저장소와 코드](#2-저장소와-코드)의 PR/MR 절차로 추가한다. 요청하지 않았으면
   같은 `AskUser`에 "이 내용으로 추가할까요?"(`confirm`)를 함께 넣는다. `missing`에 `health_route`가 있으면 health 경로를 추가하는 코드 변경도 같은 PR/MR에 넣는다.
4. 병합되면 [3. 선언 적용과 리소스](#3-선언-적용과-리소스)로 `project_apply`와 `resource_create`까지 진행한다.
   배포는 사용자가 요청했을 때만 한다. 요청이 없으면 `AskUser`로 첫 단계 배포 여부를 묻는다.

`project_ensure`·`project_apply`·`deploy`가 Git 계정이나 저장소 권한 때문에 거절되면 [저장소 접근](#저장소-접근)의 code별 행동에 따른다.

## 2. 저장소와 코드

1. 새 저장소는 Forge `repository_create`로 만든다. 연결된 `project-generator`가 있으면 그 원격 준비 절차도 따른다.
   GitHub(github.com·GitHub Enterprise Server) 저장소와 GitLab(GitLab.com·self-managed GitLab) 프로젝트는 같은 절차다.
   - `origin`은 저장소를 만들 host의 `git_connections` `origin`이다. 그 host의 `status`가 `connected`가 아니면 `connectUrl`을 사용자에게 준다.
   - 만들기 전에 `repository_namespaces`(`origin`)로 연결한 계정이 저장소를 만들 수 있는 namespace(GitHub 계정·조직, GitLab 사용자 이름·group 경로)를 확인한다.
     사용자가 지정한 namespace가 목록의 `path`에 있으면 그대로 쓴다. 없고 `complete`가 `true`이면 만들지 않는다.
     경로가 비슷한 항목(예: `app/demo` → `apps/demo`)을 보여 주고, 사용자가 고른 namespace로 만든다. 사용자가 확인하기 전에는 아무것도 만들지 않는다.
     `complete`가 `false`이면 목록에 없는 namespace도 쓸 수 있다. 사용자가 지정한 경로로 요청하고 Git 호스트의 판정을 따른다.
   - `repository`는 `<namespace>/<이름>`이다(예: GitHub `owner/todo`, GitLab `apps/demo/todo`). 공개 범위는 사용자 요청을 따르고,
     정해지지 않았으면 `private: true`다. Runway는 공개·비공개 저장소를 같은 방법으로 읽으므로 배포 때문에 공개로 만들지 않는다.
   - 영수증이 `failed`이면 `error`가 원인을 알린다. namespace가 없거나 만들 권한이 없으면 문장이 비슷한 namespace를 붙인다.
     어느 것인지 사용자에게 확인한 뒤 새 `requestKey`로 다시 요청한다. `unknown`이면 다시 만들지 않고 `repository_get`으로 영수증을 읽는다.
   - `created`이면 영수증의 `result.origin`·`result.repository`로 Git `prepare`를 한다. `result.repository`는 github.com이 `owner/repo`,
     다른 host가 `<host>/<path>`(예: `gitlab.example.com/apps/demo/todo`)이며 Runway의 `repository`와 `spec.repository`에 그대로 쓸 수 있다.
   기존 저장소의 공개 범위를 임의로 바꾸지 않는다.
2. 앱이 DB·버킷을 쓰면 코드를 쓰기 전에 sandbox 환경(기본 `dev`)의 리소스를 만든다. `project_ensure`(`repository`, 필요하면 `pipelines`·`runtime`)로
   Project를 만들고 `resource_create`(`project`, `environment`, `template`, `name`, `idempotencyKey`)를 호출한 뒤 `resource_get`으로 `ready`를 한 번 확인한다.
   `template`은 `resource_catalog`에서 `available`이 `true`인 것을 고른다. 앱 DB는 보통 공유 풀의 `pool-postgres`, 파일은 `bucket`이다.
   기본 `name`은 Project slug다. 이 리소스의 Variable에는 접두어가 없다(`DATABASE_URL`). `main`은 다른 이름처럼 `MAIN_` 접두어가 붙는다.
   접속 정보는 Agent Runway가 저장한다. 값은 Chat·코드·로그에 쓰지 않고 Variable 이름만 쓴다.
3. 코드를 구현한다. 배포에 필요한 조건은 다음과 같다. 세부 규칙과 예시는 [application.yaml과 배포 조건](references/application-yaml.md)을 읽는다.
   - 저장소 루트의 `application.yaml`(`spec.owner`에 Project 소유자의 Studio subject).
     이미 있는 저장소의 `application.yaml`을 바꾸기 전에는 `repository_inspect`로 현재 선언과 감지 결과를 읽는다.
     부모가 `application_validate`로 통과한 전체 내용을 task에 그대로 넣고, runtime이 그 내용으로 파일을 쓰게 한다. runtime은 스키마를 모르므로 직접 짓게 하지 않는다.
   - `Dockerfile`: Project 런타임의 architecture 하나(`linux/amd64` 또는 `linux/arm64`, `project_status`의 `runtime.architecture`)로 빌드되고,
     `PORT` 환경 변수의 포트에서 HTTP를 받는다. 빌드는 commit의 소스 아카이브로 하므로 `.git`·submodule·Git LFS 객체에 의존하지 않는다.
   - health 경로(기본 `/health`): 리소스를 쓰는 앱은 매 요청에서 각 리소스에 실제로 연결하고(PostgreSQL은 `SELECT 1`)
     기동 시 migration이 성공했을 때만 2xx를 반환한다. Runway의 verify는 이 경로만 확인하므로 고정 응답은 DB 장애를 숨긴다.
   - DB 재시작: 앱은 DB가 잠시 끊겨도 종료되지 않고 다시 연결한다. 연결 pool의 오류 이벤트를 처리하고, 기동 시 migration은 성공할 때까지 다시 시도한다.
   - 테스트 명령: 외부 리소스 없이 끝나야 한다. Runway의 test 스텝에는 Agent Runway Variable이 없다.
   - 언어 런타임 버전: `test.image`와 Dockerfile의 base image는 Forge Run이 checks를 실행하는 런타임과 같은 메이저 버전으로 한다
     (예: Run의 Node가 24면 `node:24-alpine`). 메이저 버전이 다르면 Forge에서 통과한 테스트가 Runway의 test 스텝에서 실패할 수 있다.
     새 앱의 스택을 제안할 때도 이 버전을 권장한다. 다른 버전이 필요하면 그 버전으로 Forge Run의 test를 실행해 통과한 뒤에만 쓴다.
4. Forge Run의 checks(test·lint·build)로 확인한다. sandbox 환경의 리소스가 `ready`이면 Forge가 Run의 명령 환경에 그 Variable을
   넣으므로 migration과 DB 연동을 실제 DB로 확인한다. 이 확인은 Forge에서만 가능하다. Runway의 test 스텝에는 DB가 없다.
5. task가 끝나면 부모가 `run_submit`의 Git `review` Run을 내고, diff의 `application.yaml` 전체를 `application_validate`로 다시 검사한다.
   거부되면 커밋하지 않고 오류 필드를 고치는 task를 낸 뒤 `review`부터 다시 한다.
6. 부모가 Git `commit`·`push`·`pull-request` Run으로 PR/MR을 만든다. Git 작업을 task에 넣지 않는다. native Runtime은 커밋할 수 없다.
   `pull-request`는 승인을 만들지 않는다. `pull-request` Run이 `interrupted`로 끝나면 사용자에게 Git 호스트 화면을 확인하게 하지 않는다.
   같은 `headSha`·`fingerprint`와 새 `requestKey`로 `pull-request`를 다시 제출한다. Forge는 그 브랜치의 열린 PR/MR을 찾아 갱신하므로 두 번 만들지 않고, 결과의 `pullRequestNumber`를 확정한다.
7. PR/MR의 CI가 통과하면 Git `merge`를 제출한다. 보호 작업이므로 Run이 승인을 기다리며 `approval.id`와 `approvalUrl`을 반환한다.
   `git_approval_get` 화면을 Chat에 보여 소유자가 그 자리에서 승인하게 하고, 링크도 답변에 그대로 넣어 사용자에게 준다(`WaitForServiceWork`로 턴을 끝낼 때도 그 메시지에 넣는다). 병합 Run이 `succeeded`인지 확인한 뒤 3절로 간다. 승인 없이 다른 경로로 병합하지 않는다.
   Forge는 저장소의 기본 브랜치(`main`이 아닐 수 있다)로만 병합한다.
   Workspace의 기준 브랜치가 기본 브랜치가 아니면 `merge`가 `git_action_unsupported`로 거절되고 승인은 만들어지지 않는다.
   `baseBranch` 없이 준비한 Workspace는 기본 브랜치에서 시작하므로 이 이유로 거절되지 않는다.
   이때는 사용자가 Git 호스트에서 그 PR/MR을 병합해야 한다고 알리고, 병합된 뒤 3절로 간다.

## 3. 선언 적용과 리소스

1. 배포할 revision(기본: 저장소의 기본 브랜치. Forge가 병합한 PR/MR이 들어가는 브랜치다)의 `application.yaml` 내용을 그대로 `project_apply`에 넘긴다(`repository`, `application`).
   새 Project를 `default`가 아닌 pipeline이나 정한 런타임으로 만들 때만 `pipelines`·`runtime`을 함께 넘긴다. 기존 Project에는 둘 다 넘기지 않는다.
   기존 Project에 그 Project의 것과 다른 `pipelines`를 넘기면 `pipeline_mismatch`로 실패한다.
   새 Project를 만드는 `project_apply`는 호출한 사용자의 Git 계정이 저장소를 읽을 수 있는지 확인한다([저장소 접근](#저장소-접근)).
   Runway는 그 revision의 파일 SHA-256이 적용한 내용과 같은지 확인하므로, 한 글자라도 다르면 `application_changed`로 실패한다.
   마지막 줄바꿈 하나만 달라도 다르다. 그래서 내용을 기억이나 task 입력에서 다시 쓰지 않는다. `repository_inspect`(`ref`: 배포할 revision)가
   돌려준 `application`(저장소 파일이 유효하면 그 파일의 원문)을 바꾸지 않고 `application`에 넘긴다.
2. `project_apply`는 리소스를 만들지 않는다. 응답의 `application.environments`가 단계마다 `resources`(이미 있는 리소스와 상태)와
   `missingSecrets`를 준다. 앱이 기본 설정으로 시작하는 데 필요한 리소스 중 없는 것을 `resource_create`로 만든다.
   - 리소스는 환경 하나에 속한다. 앱이 실행될 단계마다 한 번씩, 같은 `name`·`template`으로 호출한다. 그 단계의 첫 Deployment 전에 만든다.
   - 호출마다 새 `idempotencyKey`를 쓴다. 응답을 잃었을 때만 같은 key로 다시 호출한다.
   - `environment`는 Project pipeline 중 하나의 단계여야 한다. 아니면 `environment_not_in_pipeline`이다. Runway는 이 조건을 그 환경의 target보다 먼저 확인한다.
   - `sandbox`가 `false`인 template은 sandbox 환경에 만들 수 없다(`template_not_in_sandbox`). 그 단계에는 같은 Variable 이름을 주는
     template(예: `rds-postgres` 대신 `pool-postgres`)을 같은 `name`으로 만든다. 그런 template이 없으면 사용자에게 알린다.
   - 런타임 type이 `eks`가 아닌 Project는 `target_unsupported`다. 연결 값의 Variable 이름을 `application.yaml`의 `secrets`에 선언하고 사용자가 값을 입력하게 한다.
3. 배포를 요청받았으면 리소스가 `ready`가 되기를 기다리지 않고 바로 [4. 배포와 승격](#4-배포와-승격)의 `deploy`를 호출한다.
   생성 중(`pending`)인 리소스는 Deployment가 `resources` 스텝에서 기다리고, Studio가 그 Deployment를 끝까지 따라간다.
   Deployment는 리소스를 만들지 않는다. 리소스가 `failed`이면 원인을 보고한다.
4. 값 없는 시크릿이 있으면 응답의 `application.secretsUrl`(모든 단계), 또는 한 단계만이면 그 환경의 `secretsUrl` **링크 하나**를 사용자에게 준다.
   시크릿마다 링크를 주지 않는다. `secret_request`를 `variable` 없이 호출해도 같은 링크다. 값은 Chat으로 받지 않는다.
   사용자가 입력했다고 하면 `project_status`에서 `secretsUrl`이 `null`인지 확인한다.
5. `invalid_application`이면 오류의 필드를 고쳐 2절의 PR/MR로 다시 반영한다. 이전 apiVersion의 파일은 거부되며, 메시지가 고칠 내용을 알려 준다.

## 4. 배포와 승격

단계 순서와 승인 규칙은 Project의 pipeline과 설치의 환경이 정한다. 먼저 `project_status`를 읽는다.
`pipelines[]`가 pipeline마다 trigger와 단계(승격 순서·크기)를 준다. `environments[]`의 `pipeline`·`position`·`next`·`approval`·`deployBlockers`·`promoteBlockers`가
단계별 상태를 준다. `position`은 그 pipeline 안의 자리이고, `next`는 같은 pipeline의 다음 단계다.
기본 설치의 `default` pipeline은 `dev`(승인 없음) → `prod`(소유자 승인)이다.

1. 첫 단계(`position`이 `0`인 환경)에 `deploy`(`project`, `environment`, 선택 `ref`, `idempotencyKey`)를 호출한다.
   pipeline이 여럿이면 배포할 pipeline의 첫 단계를 고른다.
   저장소의 기본 브랜치를 배포하면 `ref`를 생략한다. Runway가 Git 호스트에서 기본 브랜치를 읽어 build하며, 이름이 `main`이 아니어도 된다.
   Forge가 병합한 PR/MR은 기본 브랜치에 들어가므로 병합 뒤의 첫 배포는 `ref` 없이 호출한다. 다른 branch·tag·commit을 배포할 때만 `ref`를 보낸다.
   응답의 `ref`·`commit`이 실제로 build한 branch와 commit이다.
   Agent Runway가 호출한 사용자의 Git 계정으로 저장소를 읽고, 그 commit을 Project 런타임의 architecture로 build해 Release(`r<n>`)를 만들고 배포한다.
   같은 pipeline에서 같은 commit을 같은 선언으로 build한 Release가 있으면 다시 build하지 않고 그 Release를 쓴다.
   다른 pipeline이 build한 Release는 쓰지 않는다. 예: `main`이 build한 commit에 `v*` 태그를 달면 태그 pipeline이 그 commit을 다시 build한다.
   Git 계정이나 `ref` 때문에 거절되면 [저장소 접근](#저장소-접근)의 code별 행동에 따른다.
   - trigger의 `kind`가 `tag`인 pipeline의 첫 단계는 trigger와 맞는 태그만 `ref`로 받는다. `ref`가 없으면 `ref_required`(400),
     맞지 않는 이름이면 `ref_not_allowed`다. `release`를 보내면 그 Release의 `tag`가 trigger와 맞아야 한다.
     배포할 태그는 사용자에게 확인한다. 저장소에 그 태그가 없으면 `ref_not_found`다.
     태그를 새로 만들면 workspace-task의 tag 규칙대로 기본 브랜치의 commit에 단다. PR/MR을 병합한 Workspace의 HEAD에 달지 않는다.
   - trigger가 기본 브랜치가 아닌 branch(예: `stg`, `prod`)인 pipeline은 그 브랜치에 commit을 올려 시작한다. 사용자가 브랜치로 배포하기를 원하면
     다른 `ref`의 `deploy`로 대신하지 않는다. 브랜치는 workspace-task의 보호 branch 게시 규칙대로 Forge `publish-protected`로 올린다(소유자 승인).
     기본 브랜치(`baseBranch` 생략)로 새 Workspace를 `prepare`하고 `review`의 `headSha`·`fingerprint`를 쓴다.
     브랜치가 없으면 `expectedHeadSha: null`로 만든다. 있으면 `repository_inspect`(`ref`: 그 브랜치)의 `commit`을 `expectedHeadSha`로 보내 fast-forward한다.
     push 배포가 켜져 있으면 Runway가 그 push로 첫 단계에 배포한다. 꺼져 있으면 `deploy`(`ref`: 그 브랜치)를 호출한다.
   - push 배포를 켠 Project(`project_get`의 `push.state`가 `on`)는 trigger(`project_status`의 `pipelines[].trigger`)와 맞는 push를
     Runway가 그 pipeline의 첫 단계에 배포한다. push가 여러 pipeline의 trigger와 맞으면 맞는 pipeline마다 첫 단계에 배포하고, pipeline마다 자기 Release를 build한다.
     그래서 병합 직후의 `deploy`가 `deployment_in_progress`일 수 있다. 이때는 새로 요청하지 않고 `project_status`의 그 단계 `inProgress.deploymentId`를
     `deployment_get`으로 한 번 읽어 그 Deployment를 따른다. push 배포를 켜지 않은 Project는 병합만으로 배포되지 않으므로 `deploy`를 호출한다.
2. 다음 단계는 `promote`(`project`, `from`, `idempotencyKey`)로 같은 Release를 배포한다. `from` 단계의 `next`가 배포될 단계다.
   다시 build하지 않으므로 앞 단계에서 검증한 이미지가 그대로 간다.
   - 첫 단계가 아닌 단계에 `deploy`로 ref를 보내면 `release_not_promoted`다. 같은 pipeline의 바로 앞 단계에서 성공하지 않은 Release를 `release`로 보내도 같다.
     그 단계에서 지금 실행 중인 Release를 다시 배포하는 `deploy`(재시작)는 이 조건을 보지 않는다.
   - pipeline의 마지막 단계에서 `promote`하면 `no_next_environment`다. 승격은 다른 pipeline으로 이어지지 않는다.
     예: `main` → `dev`와 `v*` → `stg` → `prod` pipeline을 가진 Project에서 `dev`의 Release는 `stg`로 승격되지 않는다. `stg`에는 `v*` 태그를 `deploy`한다.
   - `approval: owner` 환경은 `awaiting_approval`을 반환한다. Studio Chat에는 `deploy`·`promote`·`rollback` 결과의 배포 화면이 보인다.
     소유자에게 그 화면의 **승인하고 시작**·**거절**을 누르고 Studio 승인 카드에서 확인하라고 안내한다. 모델은 승인하지 않는다.
     화면이 없는 surface(Slack·Telegram·Teams·API)에서만 `approvalUrl`을 주고 소유자가 Agent Runway 콘솔에서 승인하게 한다.
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
     메시지 끝에 시크릿 입력 링크가 있으면 그 링크 하나를 준다.
     적용한 `application.yaml`이 없으면 `project_apply`를 먼저 한다. 환경에 Project 런타임의 target type이 없거나 그 target이 런타임 architecture를
     실행하지 않거나 계정 접근이 확인되지 않았으면 관리자가 환경을 고치거나 소유자가 런타임을 고쳐야 하므로 메시지를 사용자에게 전한다.
     `deployBlockers`의 `pending` 리소스는 배포를 막지 않는다. Deployment가 기다린다.
   - `resource_failed`·`resource_timeout`(Deployment의 `errorCode`): 기다리던 리소스가 실패했거나 2시간 안에 준비되지 않았다. 그 리소스의 상태를 보고한다.
   - `environment_not_in_pipeline`: 그 환경은 Project pipeline 중 어느 것의 단계도 아니다. 메시지가 Project의 pipeline과 단계를 나열한다.
     `project_status`의 단계 중에서 고른다.
     Runway는 이 조건을 target·적용한 선언·Release·준비 상태보다 먼저 확인한다. 단계가 아닌 환경의 요청은 다른 문제가 있어도 이 code로 거절된다.
   - `no_next_environment`: `promote`의 `from`이 그 pipeline의 마지막 단계다. 승격할 단계가 없다.
   - `ref_required`·`ref_not_allowed`: tag trigger pipeline의 첫 단계에 맞는 태그를 보내지 않았다. 1단계의 tag 규칙에 따른다.
   - `release_outdated`: 그 Release는 Project 런타임과 다른 architecture로 build됐거나 이전 버전의 `application.yaml`로 build됐다(`release_list`의 `deployable: false`).
     다시 배포할 수 없다. 첫 단계에 ref를 `deploy`해 새 Release를 만든 뒤 승격한다.
   - `host_conflict`: 요청한 주소를 같은 Project의 다른 환경이 쓰고 있다(환경 이름 없는 주소를 받을 단계가 바뀐 뒤에 생긴다). 오류 메시지의 조치를 따른다:
     그 환경에 다시 배포해 자기 주소로 옮기거나, 그 환경의 서비스를 `service_remove`로 삭제하거나, 진행 중인 배포가 끝나기를 기다린다([앱 주소](#앱-주소)).
   - `project_changed`: 요청하는 동안 그 환경의 pipeline·단계 순서·architecture·주소 규칙이 바뀌었다. 아무것도 저장되지 않았다.
     `project_status`를 다시 읽고 다시 요청한다.
   - `deployment_in_progress`: 진행 중인 Deployment가 끝나기를 기다린다.
6. 배포한 Release에 문제가 있으면 `rollback`(`project`, `environment`, `idempotencyKey`)으로 그 환경의 직전 Release를 다시 배포한다.
   승격은 필요 없다. 되돌릴 Release가 없으면 `no_rollback_target`이다. `project_status`의 `rollbackTo`가 대상 Release다.

### push 배포

`project_get`·`project_list`의 `push.state`가 Project의 push 배포 상태다.

| `push.state` | 뜻 |
|---|---|
| `off` | push로 배포하지 않는다. 요청(`deploy`)으로만 배포한다 |
| `on` | pipeline의 trigger와 맞는 push가 그 pipeline의 첫 단계에 배포한다. Runway는 push 배포를 켠 사용자(`push.enabledBy`)의 Git 권한으로 저장소를 읽는다 |
| `delegation_invalid` | 켠 사용자의 Git 위임이 Agent Studio에 없다. push로 시작한 Deployment가 모두 `push_delegation_invalid`로 실패한다. 다시 켜야 한다 |

- **켜기**: `push_enable`(`project`)은 사용자가 push 배포를 요청했을 때만 호출한다. Project 생성이나 배포 요청을 push 배포 요청으로 보지 않는다.
  - 켜면 Runway가 저장소에 push webhook을 만들고, push마다 켠 사용자의 Git 권한으로 저장소를 읽는다.
    이 허용은 push 배포를 끄거나 그 사용자가 Agent Studio의 프로필 → Git 계정에서 위임을 폐기할 때까지 유지된다. 호출하기 전에 사용자에게 이 내용을 알린다.
  - Studio Chat은 호출마다 사람의 승인 카드를 보여 주고, 승인된 호출만 실행한다. 승인할 사람이 없는 실행에는 `push_enable` 도구가 없다.
    도구가 없으면 Project 소유자나 Studio 관리자가 Agent Runway 콘솔의 Project 설정(`/projects/<slug>/settings`)에서 켜야 한다고 안내한다.
  - Runway는 승인 표시가 없는 호출을 아무것도 바꾸지 않고 `person_approval_required`로 거절한다. [사람의 승인](#사람의-승인)에 따른다.
  - `push_busy`는 같은 Project의 다른 push 배포 변경(켜기·끄기·Project 삭제의 끄기)이 진행 중이라는 뜻이다. Runway는 기다리지 않고 거절한다.
    메시지가 알려 주는 시간(5초) 뒤에 다시 호출한다. `push_enable`을 다시 호출하면 승인 카드도 다시 뜬다.
  - Project 소유자나 Studio 관리자만 켤 수 있다(`owner_required`). 켜는 사용자의 Git 계정은 저장소의 webhook을 관리하는 역할이어야 한다:
    GitHub(github.com·GitHub Enterprise Server) 저장소는 `admin`, GitLab 프로젝트는 Maintainer 이상이다. 아니면 `repository_access_denied`다.
  - `git_connection_required`·`git_host_removed`는 [저장소 접근](#저장소-접근)에 따른다. `policy_refused`는 Agent Studio가 그 사용자에게 Git 위임을 주지 않는다는 뜻이다.
    사용자 등급이 허용하지 않거나, 그 Git 계정의 위임이 한도에 찼다. 한도에 찼으면 사용자가 프로필 → Git 계정에서 위임을 폐기한다.
    `identity_unavailable`은 메시지가 알려 주는 시간 뒤에 다시 호출한다. `source_refused`는 Git 호스트가 webhook을 거절한 것이며 메시지가 이유를 준다.
  - 다시 호출하면 webhook secret과 위임을 새로 만들고, 그 뒤의 push는 다시 켠 사용자의 권한으로 읽는다. 중간에 실패한 켜기도 다시 호출하면 끝난다.
- **끄기**: 사용자가 요청하면 `push_disable`(`project`)을 호출한다. 소유자나 Studio 관리자만 끌 수 있고(`owner_required`), 끄는 데에는 Git 계정이 필요 없다.
  `push_busy`이면 켜기와 같이 5초 뒤에 다시 호출한다.
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
- **앱 선언 변경**(port·health·command·build·test·`secrets`·`env`): `application.yaml`을 고치는 PR/MR → 병합 → `project_apply` → 배포·승격 순서로 바꾼다.
  GitOps 저장소의 배포 값 파일을 직접 고치지 않는다.
- **런타임·pipeline·크기·trigger·주소 변경**: 파일 PR/MR이 아니라 `project_configure`(`project`와 바꿀 필드)로 바꾼다. 다음 Deployment부터 적용된다.
  Project 소유자나 Studio 관리자만 호출할 수 있다(`owner_required`). 호출 전에 `project_status`의 `runtime`·`pipelines`·`host`·`deployedEnvironments`를 읽는다.
  `pipelines[].trigger.overridden`과 `pipelines[].stages[].overridden`이 Project가 직접 정한 값을 표시한다. 응답은 바뀐 배포 설정이다.
  - `runtime`: `{cloud?, type?, architecture?}`다. 준 항목만 바꾼다. 배포된 서비스나 리소스가 있으면 거절될 수 있다([런타임과 pipeline 변경](#런타임과-pipeline-변경)).
  - `pipelines`: pipeline 목록 전체(1–8개, Project의 순서)다. pipeline 하나를 더하거나 뺄 때도 남길 pipeline을 모두 함께 넘긴다.
    항목은 `pipeline_list`의 이름 또는 `{name, trigger}`다. 이름만 주면 Project가 그 pipeline에 정한 trigger를 유지하고, `trigger: null`은 pipeline의 trigger로 돌아간다.
    trigger는 `{kind: branch, pattern: main}` 또는 `{kind: tag, pattern: "v*"}` 형태다.
  - `sizes`: 환경 이름별 크기다(예: `{prod: large}`). 환경은 Project pipeline의 단계여야 한다. map 전체를 교체하므로, 자기 값을 유지할 단계를 모두 함께 넘긴다.
    빠진 단계는 pipeline의 크기로 돌아간다. `{}` 또는 `null`은 모두 제거한다.
    크기의 실제 값(CPU·memory·복제 수 또는 instance type)은 관리자가 환경의 target에 정한다. Deployment의 `size`가 적용된 값을 보여 준다.
  - `installScript`: 런타임 type이 인스턴스를 쓰는 Project(`project_status`의 `machines`가 `true`)에서만 쓴다. secret을 넣지 않는다. `null`은 제거한다.
    Project 자기 스크립트가 있는지는 `ownInstallScript`가 알려 준다. 스크립트 내용을 돌려주는 도구는 없다.
  - `host`: 환경 이름 없는 주소를 받을 단계다. `{bare: <환경>}`, `{bare: none}`, `{bare: auto}`(또는 `null`) 중 하나다([앱 주소](#앱-주소)).
  - 생략한 필드는 그대로 유지된다. `invalid_settings`(400)이면 메시지가 위반을 모두 알려 준다.
  - 배포된 서비스가 있어도 바꿀 수 있는 것: pipeline 추가와 순서 변경, 배포된 서비스가 없는 pipeline 빼기, trigger, 크기, `installScript`, `host`.
    그 밖의 변경은 [런타임과 pipeline 변경](#런타임과-pipeline-변경)을 따른다.
- **환경마다 다른 값**: 비밀이 아닌 값도 환경마다 다르면 `env`가 아니라 Variable로 둔다. Agent가 `variables_set`(`project`, `environment`, `values`, `idempotencyKey`)으로
  설정한다. `idempotencyKey`는 요청마다 새로 만든다. 응답을 잃었을 때만 같은 키와 값으로 다시 보낸다.
  같은 키에 다른 값을 보내면 그 Variable은 바뀌지 않고 `failed[]`의 `idempotency_conflict`가 된다(모든 Variable이 그렇다면 409 `idempotency_conflict`). 값을 바꿀 때는 새 키를 쓴다.
  소유자·관리자만 호출할 수 있고 값은 반환되지 않는다. 결과의 `applied[]`는 쓴 Variable이고 `failed[]`는 쓰지 못한 Variable과 `code`다. `failed[]`가 있으면 그 이름만 새 키로 다시 보내거나 `code`에 따라 처리한다.
  호출이 `internal_error` 같은 오류로 끝나면 같은 키와 같은 값으로 한 번 다시 보낸다. 이미 쓴 Variable은 재생(`replayed: true`)되고 나머지만 쓴다.
  앱은 다음 배포부터 값을 받는다. 소유자가 콘솔(`/projects/<slug>/variables`)에서 입력해도 된다. 그 이름은 `application.yaml`의 `env`와 `secrets`에 쓰지 않는다.
  다음은 `variable_is_secret`으로 거절된다: 선언한 `secrets`의 이름, 환경의 secret, 자격 증명 형태의 이름(`…_TOKEN`, `…_KEY`, `…_PASSWORD`, `…_WEBHOOK`, `DATABASE_URL` 등), 자격 증명 형태의 값(token, JWT, webhook URL, 비밀번호가 든 URL, 개인 키, 긴 무작위 문자열). 거절되면 메시지의 링크를 사용자에게 주고, 값을 Chat에 다시 쓰거나 붙여 넣으라고 하지 않는다.
  적용한 `env`에 있는 이름은 `variable_declared`, 리소스가 주는 이름은 `variable_conflict`다.
- 장애 조사는 `incident-triage`를 쓴다. 런타임 type이 `eks`인 Project의 앱 namespace는 `app-<slug>-<env>`, Deployment 이름은 `app`이다.
- Project 삭제를 요청받으면 `project_delete`(`project`, `confirmation`: slug)를 한 번 호출한다. Studio가 사람에게 승인을 받은 뒤 실행되고,
  Agent Runway가 모든 환경의 서비스를 제거한 뒤 모든 리소스와 그 데이터, Project를 차례로 지운다. 되돌릴 수 없다.
  응답의 남은 서비스·리소스를 알리고, 사용자가 다시 물으면 `project_deletion_get`으로 한 번 확인한다.
  삭제는 먼저 Project의 push 배포를 끈다. 응답의 `remoteCleanup`이 `skipped`이거나 `delegationRevoked`가 `false`이면 `message`의 내용도 전한다([push 배포](#push-배포)).
  서비스 하나만 내리면 `service_remove`, 리소스 하나만 지우면 `resource_delete`를 쓴다. 둘 다 승인 뒤 실행된다.
  `service_remove`의 대상이 있는지는 `project_status`의 `environments[].removable`이 알려 준다. 실행 중인 서비스가 없어도
  실패한 배포가 앱을 남겼을 수 있으면 `true`다. 세 삭제 도구는 [사람의 승인](#사람의-승인)을 거친다.

### 앱 주소

Project의 한 단계가 `https://<slug>.<도메인>`(환경 이름 없는 주소)으로 응답하고, 그 밖의 환경은 `https://<slug>-<env>.<도메인>`으로 응답한다.
`<도메인>`은 그 환경에서 앱을 실행하는 target의 도메인이다. `project_status`의 `host`가 규칙을 준다.

| 필드 | 뜻 |
|---|---|
| `bare` | 환경 이름 없는 주소를 받는 환경. 없으면 `null`이다 |
| `chosenBy` | 고른 주체. `auto`(Agent Runway 규칙), `person`(사람이 콘솔에서 골랐다), `agent`(Agent가 `project_configure`로 골랐다) |
| `fixed` | 선택이 저장됐는지. `auto`는 환경 이름 없는 주소로 처음 배포하는 요청이 그 환경을 저장한다 |
| `suggestion` | Agent Runway 규칙이 지금 고를 다른 단계. 없으면 `null`이다. 주소를 옮기지는 않는다 |
| `moves[]` | 다음 배포에서 주소가 바뀌는 실행 중인 서비스 `{environment, from, to}`다. `from`·`to`는 전체 host 이름(예: `todo.apps.rovr.dev`)이고, 배열이 실행할 순서다 |

- **Agent Runway 규칙**(`auto`): 이름이 `prd`·`prod`·`production`인 단계 중 Project 단계 순서(`order`)의 마지막 것을 고른다. 없으면 `sandbox` 환경이 아닌 마지막 단계이고, 그것도 없으면 없다. 그래서 sandbox 단계(보통 `dev`)만 있는 Project의 dev 주소는 `<slug>-dev.<도메인>`이고, `<slug>.<도메인>`은 나중에 추가할 운영 단계가 받는다.
  저장된 뒤에는 pipeline이나 환경을 더해도 주소가 옮겨지지 않는다. 규칙이 다른 단계를 고르게 되면 `suggestion`이 알려 준다.
- **고르기**: `project_configure`의 `host`로 정한다. `{bare: <환경>}`은 그 단계(Project pipeline의 단계여야 한다), `{bare: none}`은 모든 환경에 환경 이름을 붙인다.
  `{bare: auto}`와 `null`은 Agent Runway 규칙으로 돌아간다. 사용자가 공개 주소를 받을 환경을 정했으면 그 환경으로 정한다.
  사용자가 Agent에게 맡기면 사용자가 공개할 환경을 고르고, `suggestion`이 있으면 그 단계를 먼저 검토한다.
  pipeline을 바꾼 뒤 `suggestion`이 생기면 사용자에게 알리고 옮길지 묻는다. 사용자의 동의 없이 옮기지 않는다.
- **실행 중인 서비스의 주소 옮기기**: 환경 이름 없는 주소로 실행 중이거나 배포 중인 서비스가 있으면 `host_move`(`{project, bare}`)로 옮긴다.
  `project_configure`의 `host`는 이 이동을 `person_approval_required`(403)로 거절한다. Studio는 `host_move` 호출마다 사람의 승인 카드를 보인다.
  호출하기 전에 사용자에게 다음을 알린다: 어느 주소를 어느 환경에서 어느 환경으로 옮기는지,
  옛 주소는 그 환경의 다음 배포부터 응답하지 않는다는 것, 브라우저의 cookie·localStorage, OAuth redirect URI, 외부 webhook이 옛 주소에 묶여 있을 수 있다는 것.
  사용자가 이미 옮기기로 했으면(예: `AskUser`에서 동의) 다시 묻지 않고 `host_move`를 호출한다. 승인 카드가 마지막 확인이다.
- **적용 시점**: 바뀐 주소는 각 환경의 다음 `deploy`·`promote`부터 적용된다. 실행 중인 서비스는 그때까지 주소를 유지한다.
  주소를 내놓는 환경을 먼저 다시 배포한다. 예: `prod`에서 `stg`로 옮기면 `prod`에 한 번 다시 배포해 `<slug>-prod`로 옮긴 뒤 `stg`에 배포한다.
  순서를 지키지 않으면 `host_conflict`다. `host.moves`가 그 순서를 준다.

### 런타임과 pipeline 변경

`project_configure`는 배포된 서비스를 깨뜨리는 변경만 거절한다. 배포된 서비스는 실행 중인 서비스, 실패한 배포가 남겼을 수 있는 서비스(`removable: true`),
끝나지 않은 Deployment(서비스 삭제 포함)다. `project_status`의 `deployedEnvironments`가 그 환경을 `order` 순서로 나열한다.

| code | 조건 | 행동 |
|---|---|---|
| `pipeline_locked` | 배포된 서비스가 있는 환경이 어느 pipeline의 단계도 아니게 된다. 또는 배포된 서비스가 있는데 `architecture`를 바꾼다 | 아래 절차를 따른다. 메시지가 그 환경을 나열한다 |
| `project_in_use` | Project가 어느 환경에 서비스·리소스·Variable을 가진 동안 `cloud`나 `type`을 바꾼다 | 바꾸지 않는다. 메시지가 그 환경을 나열한다. 리소스를 지우면 데이터가 사라지므로 사용자가 요청하지 않으면 지우지 않는다 |
| `pipeline_conflict` | 두 pipeline이 같은 환경을 단계로 가진다 | 같은 환경을 갖지 않는 pipeline을 고른다 |
| `pipeline_incompatible` | 단계의 환경이 런타임 type의 target을 갖지 않거나, 그 target이 런타임 architecture를 실행하지 않는다 | 다른 pipeline이나 런타임을 고른다. 환경의 target은 관리자가 더한다 |
| `pipeline_required` | `pipelines`가 비었다 | pipeline을 하나 이상 넘긴다 |
| `person_approval_required` | `project_configure`가 실행 중인 서비스가 쓰는 환경 이름 없는 주소를 다른 환경으로 옮긴다 | `host_move`로 옮긴다([앱 주소](#앱-주소)) |

`pipeline_locked`일 때의 절차:

1. `project_status`를 읽는다. 변경 뒤에도 `deployedEnvironments`의 환경이 모두 남는 pipeline 중 하나의 단계이고 `architecture`를 바꾸지 않으면
   `project_configure`를 바로 호출한다. 예: `dev`에 서비스가 있는 Project에 `stg` → `prod` pipeline을 더하는 변경은 바로 된다. `dev`를 가진 pipeline을 빼는 변경은 거절된다.
2. 거절되면 그 변경을 하지 않는다. 나열된 환경마다 서비스를 먼저 삭제해야 한다고 사용자에게 알린다. 삭제하면 그 환경의 앱이 멈추고 주소가 응답하지 않는다.
   리소스와 데이터는 남고, 다시 배포하면 앱이 돌아온다. 사용자의 동의 없이 서비스를 삭제하지 않는다.
3. 사용자가 동의하면 환경마다 `service_remove`(`project`, `environment`, `confirmation`: 환경 이름, `idempotencyKey`)를 호출한다.
   호출마다 [사람의 승인](#사람의-승인)을 거친다.
   진행 중인 Deployment가 있는 환경은 그 Deployment가 끝나거나 소유자가 승인 대기를 거절한 뒤에 삭제한다.
   그 전의 `service_remove`는 `deployment_in_progress`, 그 환경에 배포된 적이 없으면 `not_deployed`다.
4. 삭제 Deployment도 Studio가 끝까지 따라가 결과를 Chat에 전달한다. 반복 조회하지 않는다.
   모든 삭제가 끝나면 `project_status`를 한 번 읽어 그 환경이 `deployedEnvironments`에서 빠졌는지 확인한다. 삭제가 실패한 환경은 원인을 보고한다.
5. 빠졌으면 `project_configure`를 다시 호출한다.
6. 앱을 다시 실행하려면 새 pipeline의 첫 단계에 다시 배포한다([4. 배포와 승격](#4-배포와-승격)). 사용자가 배포를 요청하지 않았으면 배포할지 묻는다.

설정 변경과 배포 요청이 겹치면 먼저 저장된 쪽이 이긴다. 배포가 먼저 저장되면 `project_configure`의 검사가 그 배포를 포함한다.
변경이 먼저 끝나면 그 배포 요청이 `project_changed`로 거절된다. `project_changed`이면 `project_status`를 다시 읽고 다시 요청한다.

### 사람의 승인

`push_enable`·`service_remove`·`resource_delete`·`project_delete`·`host_move`는 사람이 호출마다 승인한다([앱 주소](#앱-주소)).
Studio Chat이 호출 전에 승인 카드를 보여 주고, 사용자가 승인한 호출만 실행한다. 사용자가 거절한 호출은 반복하지 않는다.

- `person_approval_required`(403)는 승인 표시 없이 호출됐다는 뜻이다. Runway는 아무것도 읽거나 바꾸지 않았다.
- 같은 호출을 자동으로 반복하지 않는다. Studio Chat의 승인 카드에서 사용자가 그 호출을 승인해야 한다고 알린다.
- 사용자가 승인했는데도 이 code가 오면 Studio가 승인 표시를 보내지 않는 버전이다. 운영자에게 알리고,
  그동안은 Project 소유자나 Studio 관리자가 Agent Runway 콘솔에서 직접 해야 한다고 안내한다.

## 보고

진행한 작업마다 확인한 사실만 보고한다: 저장소와 PR/MR, Project 런타임과 pipeline 이름, 적용한 선언의 SHA, 단계별 리소스 상태, Release 이름, Deployment ID·상태·URL.
승인을 기다리는 작업과 사용자가 할 일(승인, `secretsUrl`에서의 secret 입력, Git 호스트 연결)을 분리해 알린다.
