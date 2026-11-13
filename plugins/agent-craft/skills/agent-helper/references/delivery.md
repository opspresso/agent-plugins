# Agent Runway

앱의 Project·pipeline·환경·리소스·secret·`application.yaml`·배포를 다루거나 Runway 콘솔을 안내할 때 읽는다.
앱을 처음부터 배포까지 진행하는 절차는 `app-delivery` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **환경**: 관리자가 정한 배포 대상이다. 기본은 `dev`·`prod`이고 `staging` 같은 환경이 더 있을 수 있다. 환경마다 cloud 하나와
  제공하는 target type(`eks`: 클러스터, `eb`: Elastic Beanstalk)이 있다. sandbox 환경(기본 `dev`)의 값만 Forge Sandbox에 전달된다.
  `approval: owner` 환경(기본 `prod`)은 Agent의 요청을 소유자가 승인해야 한다. 환경의 규칙은 `approval`과 `sandbox` 두 가지다.
- **pipeline**(콘솔 표기: 파이프라인): 관리자가 정한 배포 경로다. cloud·target type·architecture(`amd64` 또는 `arm64`) 하나씩,
  trigger(`{kind: branch | tag, pattern}`, push 배포를 켠 Project에서 배포를 시작하는 push)와 **단계** 목록을 가진다. 단계는 환경과 그 환경의 크기(`small`·`medium`·`large`)이고,
  목록 순서가 승격 순서다. 첫 부팅이 `default` pipeline을 만든다. `pipeline_list`가 설치의 pipeline을 준다.
  pipeline을 쓰는 Project에 배포된 서비스가 있는 동안 관리자는 그 pipeline의 단계(환경 추가·삭제·순서)와 architecture를 바꿀 수 없다(`pipeline_locked`).
  설명·trigger·단계의 크기는 언제든 바꿀 수 있다.
- **Project**: GitHub(github.com·GitHub Enterprise Server) 또는 GitLab(GitLab.com·self-managed) 저장소 하나다. 저장소는 `<host>/<path>`로 쓴다
  (예: `github.com/owner/app`, `github.example.com/owner/app`, `gitlab.example.com/group/subgroup/app`). host가 없는 `owner/repo`는 github.com만 뜻한다. 저장소의 Project를 처음 만든 Studio 사용자가 소유자다. slug는 전체에서 유일하며 다시 쓰지 않는다.
  저장소는 Agent Studio가 알려 주는 Git 호스트에 있어야 한다. Project와 저장소를 연결하거나 등록하는 단계는 없다.
  Project는 pipeline 하나로 배포한다. 새 Project는 `default`이거나 `project_ensure`·`project_apply`의 `pipeline`으로 고른 것이다.
  기존 Project의 pipeline과 Project 자기 값(단계별 크기, trigger, 인스턴스 target의 install script, 마지막 단계의 주소 형식)은 `project_configure`로 바꾼다.
  배포된 서비스가 있는 Project는 pipeline을 바꿀 수 없다([pipeline 변경](#pipeline-변경)). Project 자기 값은 언제든 바꿀 수 있다.
  실제 pipeline·단계·규칙은 `project_status`가 준다.
- **저장소 접근**: Runway는 한 사용자의 Git 계정으로 저장소를 읽어 build한다. 요청한 배포는 요청한 사용자의 계정으로,
  push로 시작한 배포는 그 Project의 push 배포를 켠 사용자의 계정으로 읽는다. 공개 저장소와 비공개 저장소가 같다.
  사용자는 Agent Studio의 프로필 → Git 계정(`/profile/git`)에서 Git 호스트마다 계정을 한 번 연결한다. Runway 콘솔에는 계정 연결과 token 입력이 없고,
  Runway는 deploy key를 만들지 않는다. 새 Project를 만드는 `project_ensure`·`project_apply`와 `release` 없이 호출하는 `deploy`에 그 사용자의 Git 계정이 필요하다.
  `ref`를 생략한 `deploy`는 Git 호스트가 알려 주는 저장소의 기본 브랜치(`main`이 아닐 수 있다)를 build한다.
  Release를 지정한 `deploy`, `promote`, `rollback`, 승인에는 필요 없다.
- **push 배포**: Project마다 켜고 끈다. 켠 Project만 trigger와 맞는 push를 pipeline의 첫 단계에 배포하고, 켜지 않은 Project는 요청으로만 배포한다.
  `project_get`·`project_list`의 `push.state`가 상태다. `off`는 꺼짐, `on`은 켜짐, `delegation_invalid`는 켠 사용자의 Git 위임이 Studio에 없어
  push 배포가 모두 `push_delegation_invalid`로 실패하는 상태다. `delegation_invalid`이면 소유자나 Studio 관리자가 다시 켠다.
- **리소스**: 운영자가 관리하는 **리소스 템플릿**으로 만든다. `resource_catalog`가 지금 쓸 수 있는 템플릿(`template` 이름, 종류, 좁힌 `parameters`,
  연결 키, sandbox 허용, 환경당 한도, `available`)을 준다. 템플릿 이름을 짐작하지 않고 이 목록에서 고른다. 기본 템플릿은 종류 이름과 같다.
  `pool-postgres`(공유 풀의 database, `DATABASE_URL`·`PG*`), `bucket`(공유 S3 prefix, `S3_BUCKET`·`S3_PREFIX`·`S3_REGION`),
  `postgres`·`valkey`(환경 namespace의 전용 서버), `rds-postgres`·`s3-bucket`·`dynamodb`(전용 AWS, 비용이 들고 sandbox 환경 불가)다.
  리소스는 환경 하나에 속한다. `application.yaml`에 선언하지 않고, 앱이 실행될 단계마다 `resource_create`로 만든다.
  `resource_create`는 Project pipeline의 단계에만, `eks` pipeline에서만 된다.
  `secret`은 템플릿이 아니라 사용자가 콘솔에서 입력하는 값이다.
  이름이 Project slug와 같은 리소스는 Variable에 접두어가 없다(`DATABASE_URL`). 다른 이름(`main` 포함)은 대문자 이름이 접두어가 된다.
- **`application.yaml`**: 저장소 루트의 앱 선언(apiVersion `agent.opspresso.com/v4`). `spec`(이름·저장소·소유자), `runtime`(port·health·command·args),
  `build`, `test`, `secrets`, `env`만 적는다. 환경·리소스·크기·trigger·cloud·target type·architecture는 적지 않는다.
  모르는 필드와 이전 apiVersion(v1~v3)은 거절되며 최대 64 KiB다. `application_validate`가 아무것도 바꾸지 않고 검사한다.
- **Release**: build 한 번의 결과 `r<n>`(commit, 이미지 digest, 선언, architecture). 상태는 `building`·`ready`·`failed`다.
- **Deployment**: Release 하나를 환경 하나에 배포한다(`deploy`·`promote`·`rollback`). 스텝은 prepare → test → build(Release build) → resources → deploy → verify이고,
  설치에 따라 analyze·publish가 더 있다. `resources`는 그 환경의 리소스가 `ready`가 되기를 기다릴 뿐 리소스를 만들지 않는다.
  상태는 `awaiting_approval`·`queued`·`running`·`succeeded`·`failed`·`rejected`다.
  pipeline의 첫 단계만 ref를 직접 받는다. 그다음 단계는 앞 단계에서 성공한 Release를 `promote`로 받는다.
  주소는 Project pipeline의 마지막 단계가 `https://<slug>.<domain>`, 그 밖의 단계가 `https://<slug>-<env>.<domain>`이다.
  Project가 `suffixEveryStage`를 켜면 마지막 단계도 `https://<slug>-<env>.<domain>`이다. 실행 중인 서비스는 다음 배포까지 기존 주소를 유지한다.
  단계의 주소는 `project_status`의 `environments[].host`가 준다.

## Helper가 쓸 수 있는 도구

| 도구 | 용도 | 주의 |
|---|---|---|
| `project_list`, `project_get`, `resource_catalog`, `resource_get` | Project·리소스 상태, push 배포 상태(`push`), 템플릿, Variable 이름 | 읽기 전용. 값은 반환하지 않는다. 여러 Project를 비교할 때는 `project_list` 한 번으로 충분하다 |
| `project_status` | Project의 `pipeline`(단계 순서·크기·trigger, `overridden`은 Project 자기 값), 배포된 서비스가 있는 환경(`deployedEnvironments`, 승격 순서)과 단계마다 현재 Release·주소·진행 중 Deployment·승인 링크·리소스·값 없는 secret·`deployBlockers` | 읽기 전용. 대화창에 환경 표로 그려질 수 있다. `position: 0`이 첫 단계, `next`가 승격될 단계다 |
| `pipeline_list` | 설치의 pipeline(이름·cloud·`type`·`architecture`·`trigger`·`stages`) | 읽기 전용. 새 Project의 pipeline을 고르거나 `project_configure` 전에 읽는다 |
| `release_list`, `release_get` | Release와 단계별 Deployment 이력 | 읽기 전용. `deployable: false`인 Release는 다시 배포할 수 없다 |
| `deployment_list`, `deployment_get`, `deployment_logs` | 배포 목록·상태·스텝 로그(마지막 64 KiB) | 읽기 전용. 승인 대기면 `approvalUrl`이 있다. 로그는 workflow 실행 중과 끝난 뒤 하루 동안 있다 |
| `deployment_lookup_request` | 응답 유실 복구 | 같은 `idempotencyKey`로 조회한다 |
| `application_validate` | `application.yaml` 검사 | 아무것도 만들거나 바꾸지 않는다 |
| `project_ensure`, `project_apply` | Project 생성, `application.yaml` 적용 | 리소스를 만들지 않는다. `pipeline`은 새 Project에만 쓴다. 새 Project를 만들 때는 호출한 사용자의 Git 계정이 저장소를 볼 수 있어야 한다. `project_apply`는 단계마다 리소스 상태와 값이 없는 secret의 입력 링크를 돌려준다 |
| `project_configure` | Project의 pipeline, 단계별 크기(`sizes`), `trigger`, `installScript`, 마지막 단계 주소에 환경 이름 붙이기(`suffixEveryStage`) 변경 | 소유자나 Studio 관리자만. 생략한 필드는 유지, `null`은 제거, `sizes`는 map 전체 교체. 다음 Deployment부터 적용된다. `deployedEnvironments`가 비어 있지 않으면 다른 `pipeline`은 `pipeline_locked`로 거절된다 |
| `resource_create` | 템플릿(`template`)과 `parameters`로 환경 하나에 리소스 생성 | 접수형. `pending → ready | failed`. 단계마다 따로 호출한다 |
| `deploy`, `promote`, `rollback` | ref를 첫 단계에 배포, 같은 Release를 다음 단계로 승격, 직전 Release로 되돌리기 | 접수형. `idempotencyKey` 필수. 결과는 원래 Chat으로 돌아온다. `approval: owner` 환경은 소유자 승인 대기이고, 결과의 배포 화면에 승인·거절 버튼이 있다. `release` 없는 `deploy`는 응답하기 전에 호출한 사용자의 Git 계정으로 저장소를 읽는다. `ref`를 생략하면 저장소의 기본 브랜치를 build한다 |
| `push_enable`, `push_disable` | Project의 push 배포 켜기·끄기 | 소유자나 Studio 관리자만. `push_enable`은 사용자가 push 배포를 요청할 때만 호출한다. Studio가 호출마다 사람의 승인을 받고, 승인할 사람이 없는 실행에는 도구가 없다. 승인 표시가 없는 호출은 Runway가 `person_approval_required`로 거절한다. 켜는 사용자의 Git 계정이 저장소의 webhook을 관리하는 역할(GitHub `admin`, GitLab Maintainer 이상)이어야 한다. `push_disable`은 Git 계정 없이 끈다. 응답의 `remoteCleanup`이 `skipped`이면 저장소에 webhook이, `delegationRevoked`가 `false`이면 Studio에 Git 위임이 남았다. `message`가 다음 행동을 알려 주므로 그대로 전한다 |
| `secret_request` | secret 입력 콘솔 링크 | 읽기 전용이라 승인 없이 실행된다. 링크만 돌려준다. 값은 묻지 않는다 |
| `service_remove`, `resource_delete`, `project_delete`, `project_deletion_get` | 환경 하나의 서비스 중지, 리소스 하나 삭제, Project 삭제와 그 진행 조회 | `runway:delete` 권한이 있을 때만 보인다. 소유자나 Studio 관리자만. 정확한 `confirmation`(환경 이름·리소스 이름·slug)이 필요하고 Studio가 호출마다 사람의 승인을 받는다. 승인 표시가 없는 호출은 Runway가 `person_approval_required`로 거절한다. 되돌릴 수 없다 |

## pipeline 변경

배포된 서비스가 있는 Project는 다른 pipeline으로 바꿀 수 없다. cloud와 target type이 같은 pipeline도 같다(`pipeline_locked`).
배포된 서비스는 실행 중인 서비스, 실패한 배포가 남겼을 수 있는 서비스(`removable: true`), 끝나지 않은 Deployment(서비스 삭제 포함)다.
리소스와 Variable은 해당하지 않는다. `project_status`의 `deployedEnvironments`가 그 환경을 승격 순서로 나열한다.

1. `project_status`를 읽는다. `deployedEnvironments`가 비어 있으면 `project_configure`(`project`, `pipeline`)를 호출한다.
2. 비어 있지 않거나 `project_configure`가 `pipeline_locked`로 거절되면, 나열된 환경마다 서비스를 먼저 삭제해야 한다고 사용자에게 알린다.
   삭제하면 그 환경의 앱이 멈추고 주소가 응답하지 않는다. 리소스와 데이터는 남는다.
3. 사용자가 동의하면 환경마다 `service_remove`(`confirmation`: 환경 이름)를 호출한다. Studio가 호출마다 사람의 승인을 받는다.
   진행 중인 Deployment가 있는 환경은 그 Deployment가 끝나거나 소유자가 승인 대기를 거절한 뒤에 삭제한다.
   그 전의 `service_remove`는 `deployment_in_progress`, 그 환경에 배포된 적이 없으면 `not_deployed`다.
4. 삭제 Deployment의 결과는 Chat으로 돌아온다. 반복 조회하지 않는다. 모든 삭제가 끝나면 `project_status`를 한 번 읽어 `deployedEnvironments`가 비었는지 확인한다.
5. 비었으면 `project_configure`를 다시 호출한다. cloud나 target type이 다른 pipeline은 리소스와 Variable도 없어야 한다(`project_in_use`).

Project 자기 값(`sizes`·`trigger`·`installScript`·`suffixEveryStage`)은 서비스가 있어도 바꿀 수 있다.
콘솔 설정 탭은 배포된 서비스가 있으면 pipeline 선택을 막고, 서비스를 삭제할 파이프라인 탭의 환경 카드로 가는 링크를 보여 준다.

## Secret과 Variable

secret 값은 대화로 받지 않는다. `project_apply` 결과의 링크나 `secret_request`가 돌려준 콘솔 링크를 사용자에게 준다.
입력 페이지는 `/projects/<slug>/secrets/new?environment=<env>&variable=<NAME>`이다.
비밀이 아닌 값이 환경마다 다르면 소유자가 `/projects/<slug>/variables`에서 Variable로 입력한다. 값을 입력하는 도구는 없다.
적용한 `application.yaml`의 `env`에 있는 이름은 입력할 때 `variable_declared`(409)로 거부되므로, 환경마다 다른 값의 이름은 `env`에 쓰지 않는다.
sandbox 환경(기본 `dev`) Variable에는 Sandbox 예약 이름을 쓰지 않는다. 예: `OPENAI_API_KEY` 대신 `APP_OPENAI_API_KEY`.
`application.yaml`의 `secrets`·`env`는 모든 환경에 적용되므로 sandbox 환경이 있는 설치에서는 그 이름에도 예약 이름을 쓸 수 없다.

## 콘솔 페이지 (`agent-runway`)

| 경로 | 용도 |
|---|---|
| `/` | Project 목록과 Project별 pipeline 단계 상태, Project 생성 |
| `/projects/<slug>` | 파이프라인 탭. Project의 pipeline과 trigger, 최근 Release가 단계를 거친 상태, 단계별 현재 Release. 소유자의 deploy·promote·rollback |
| `/projects/<slug>/releases` | 히스토리 탭. Release 이력과 단계별 Deployment. 소유자의 Release 배포·승격 |
| `/projects/<slug>/resources` | 리소스 탭. 환경별 리소스와 템플릿으로 리소스 추가 |
| `/projects/<slug>/variables` | 환경 변수 탭. 환경별 Variable과 secret. 소유자의 입력·변경·삭제 |
| `/projects/<slug>/application` | 앱 탭. 적용한 `application.yaml`과 값이 없는 secret |
| `/projects/<slug>/settings` | 설정 탭. 소유자, 파이프라인 설정(pipeline·단계별 크기·trigger·모든 단계 주소에 환경 이름 붙이기), push 배포(상태, 켠 사용자, 켜기·끄기), 소유자 이전(Studio 관리자), Project 삭제 |
| `/projects/<slug>/audit` | 감사 기록 탭 |
| `/projects/<slug>/deployments/<id>` | Deployment 스텝·로그, 소유자의 승인 |
| `/projects/<slug>/secrets/new` | secret 값 입력 |
| `/templates`, `/templates/<name>` | 리소스 템플릿. Studio 관리자가 관리한다 |
| `/admin/environments`, `/admin/environments/<name>` | 관리 > 환경. 환경의 cloud·규칙·target type. Studio 관리자만 바꾼다 |
| `/admin/pipelines`, `/admin/pipelines/<name>` | 관리 > 파이프라인. pipeline의 cloud·target type·architecture·trigger·단계. Studio 관리자만 바꾼다. 편집 화면은 배포된 서비스가 있어 단계·architecture를 잠근 Project와 환경을 나열한다 |
| `/profile` | 계정 정보 |

콘솔 전용 작업: secret·Variable 값 입력·변경, 값 보기(소유자, 감사 기록), 소유권 이전(Studio 관리자), 환경·pipeline·리소스 템플릿 관리(Studio 관리자).
Git 호스트와 Git 계정 연결은 Runway 콘솔에 없다. 사용자가 Agent Studio의 프로필 → Git 계정(`/profile/git`)에서 계정을 연결한다.
push 배포는 설정 탭이나 `push_enable`·`push_disable`로 켜고 끈다. 켜면 Runway가 저장소에 push webhook을 만들고 push마다 켠 사용자의 Git 권한으로 저장소를 읽는다.
이 허용은 push 배포를 끄거나 그 사용자가 Studio의 프로필 → Git 계정에서 위임을 폐기할 때까지 유지된다.
`approval: owner` 환경의 배포 승인·거절은 소유자만 한다(Studio 관리자도 불가). Studio Chat에서는 `deploy`·`promote`·`rollback` 결과의 배포 화면에서 **승인하고 시작**·**거절**을 누르고 Studio 승인 카드에서 확인한다. 화면이 없는 surface에서는 Runway 콘솔의 승인 링크(`approvalUrl`)에서 결정한다. 소유자가 Studio 승인 카드에서 배포 호출 자체를 승인했거나 콘솔에서 시작한 배포는 기다리지 않는다.
삭제 도구가 없는 실행에서는 서비스·리소스·Project 삭제도 콘솔에서 한다(이름 재입력).

## 오류

| 코드 | 원인과 해결 |
|---|---|
| `invalid_application` (400) | 메시지가 잘못된 필드를 모두 나열한다. 파일을 고쳐 다시 적용한다. 이전 apiVersion이면 메시지대로 v4로 다시 쓴다 |
| `application_owner_mismatch`, `application_name_mismatch` (409) | `owner`·이름이 Project와 다르다. 메시지의 기대 값을 쓴다 |
| `project_owned_elsewhere` (409) | 다른 사용자의 Project다. Studio 관리자가 소유권을 이전해야 한다 |
| `pipeline_required` (409), `pipeline_not_found` (404) | 설치에 `default` pipeline이 없는데 `pipeline`을 생략했거나 이름이 틀렸다. 메시지의 이름이나 `pipeline_list`에서 골라 `pipeline`으로 넘긴다 |
| `pipeline_mismatch` (409) | 기존 Project의 `project_apply`에 다른 `pipeline`을 넘겼다. `pipeline`을 빼고 다시 적용한다. pipeline을 바꾸려면 `project_configure`를 쓴다 |
| `pipeline_locked` (409) | Project에 배포된 서비스가 있어 다른 pipeline으로 바꿀 수 없다. 메시지가 그 환경을 나열한다. [pipeline 변경](#pipeline-변경)의 절차를 따른다. 관리자의 pipeline 편집에서는 그 pipeline을 쓰는 Project에 배포된 서비스가 있어 단계·architecture를 바꿀 수 없다는 뜻이다. 메시지가 Project와 환경을 나열하고, 각 Project의 소유자나 관리자가 그 서비스를 삭제한 뒤 바꾼다 |
| `project_in_use` (409) | cloud나 target type이 다른 pipeline으로 바꾸려는데 Project에 리소스·Variable이 남아 있다. 먼저 지우거나 같은 cloud·target type의 pipeline을 고른다 |
| `invalid_pipeline` (400) | `project_configure`의 값이 틀렸다(단계가 아닌 환경의 크기, 인스턴스가 없는 target type의 install script 등). 메시지가 위반을 모두 나열한다 |
| `owner_required` (403) | 소유자나 Studio 관리자만 할 수 있는 작업이다(`project_configure`, 삭제) |
| `person_approval_required` (403) | 사람이 호출마다 승인하는 도구(`push_enable`·`service_remove`·`resource_delete`·`project_delete`)가 승인 표시 없이 호출됐다. 아무것도 바뀌지 않았다. 같은 호출을 자동으로 반복하지 않는다. Studio Chat에 그 호출의 승인 카드가 뜨면 사용자가 승인해야 한다고 알린다. 사용자가 승인했는데도 이 code가 오면 Studio가 승인 표시를 보내지 않는 버전이므로 운영자에게 알리고, 그동안은 사용자가 Runway 콘솔에서 직접 한다 |
| `environment_not_in_pipeline` (409) | 그 환경은 Project pipeline의 단계가 아니다. `project_status`의 단계 중에서 고른다. Runway는 이 조건을 target·적용한 선언·Release·준비 상태보다 먼저 확인한다 |
| `environment_not_ready` (409) | 메시지가 원인을 알려 준다. 값 없는 secret은 링크를 주고, `failed` 리소스는 다시 만든다. 적용한 `application.yaml`이 없으면 `project_apply`를 먼저 한다. 환경에 pipeline의 target이 없거나 계정 접근이 확인되지 않았으면 관리자가 고친다. `pending` 리소스는 Deployment가 기다리므로 배포를 막지 않는다 |
| `resource_failed`, `resource_timeout` | Deployment가 `resources` 스텝에서 기다리던 리소스가 실패했거나 2시간 안에 준비되지 않았다. `statusMessage`가 리소스를 알려 준다 |
| `deployment_in_progress` (409) | 진행 중인 배포를 먼저 확인한다. push 배포를 켠 Project에서는 trigger와 맞는 push가 시작한 배포일 수 있다 |
| `release_not_promoted` (409) | 첫 단계가 아닌 단계에 앞 단계에서 성공하지 않은 Release나 ref를 배포하려 했다. 첫 단계에 `deploy`한 뒤 `promote`한다 |
| `release_outdated` (409) | Release가 pipeline과 다른 architecture로 build됐거나 이전 버전의 `application.yaml`로 build됐다. 첫 단계에 ref를 `deploy`해 새 Release를 만든다 |
| `host_conflict` (409) | 요청한 주소를 같은 Project의 다른 환경이 쓰고 있거나, 다른 Project의 주소다. 오류 메시지가 조치를 알려 준다: 그 환경에 다시 배포하거나, 그 환경의 서비스를 삭제하거나, 진행 중인 배포가 끝나기를 기다린다 |
| `no_rollback_target`, `no_next_environment` (409) | 되돌릴 Release나 승격할 다음 단계가 없다. pipeline의 마지막 단계에서 `promote`하면 `no_next_environment`다. `project_status`의 `rollbackTo`·`next`로 확인한다 |
| `target_unsupported` (409) | `eks`가 아닌 pipeline에는 리소스 템플릿이 없다. 연결 값을 secret과 Variable로 입력한다 |
| `template_not_in_sandbox` (400) | 그 템플릿은 sandbox 환경에 만들 수 없다. `resource_catalog`에서 `sandbox`가 `true`인 템플릿을 고른다 |
| `invalid_parameters` (400), `template_limit_reached` (409) | 템플릿 parameter가 틀렸거나 환경당 개수를 넘었다. `resource_catalog`를 본다 |
| `unknown_template` (400), `template_disabled` (409) | 템플릿이 없거나 운영자가 비활성화했다. `resource_catalog`에서 활성 템플릿을 다시 고른다 |
| `quota_exceeded` (409) | Project·리소스 수 한도다. 정확한 한도는 오류 메시지에 있다 |
| `resource_in_use` (409) | 서비스가 실행 중인 환경에서 적용한 `application.yaml`이나 실행 중인 Release가 `secrets`에 쓰는 Variable의 리소스는 지울 수 없다. 서비스를 내리거나 그 이름을 뺀 선언을 적용·배포한 뒤 지운다 |
| `approval_expired` | 승인이 24시간을 넘었다. 다시 요청한다 |
| `application_changed` | 커밋된 파일로 `project_apply`를 다시 하고 다시 배포한다 |
| `git_connection_required` (409, push로 시작한 Deployment의 `errorCode`) | 사용자가 그 Git 호스트를 Studio에서 연결하지 않았거나 다시 연결해야 한다. 오류 메시지의 Studio 연결 링크(`connectUrl`)를 주고, 사용자가 연결한 뒤 다시 요청한다. push로 시작한 Deployment에서는 push 배포를 켠 사용자가 다시 연결해야 하며, 다시 연결하면 다음 push부터 배포된다 |
| `repository_access_denied` (403, push로 시작한 Deployment의 `errorCode`) | 그 사용자의 Git 계정이 저장소를 볼 수 없거나, `push_enable`에 필요한 역할(GitHub `admin`, GitLab Maintainer 이상)이 없다. 다시 연결하게 하지 않는다. 저장소 이름과 그 계정의 권한을 확인한다 |
| `ref_not_found` (404) | 저장소에 그 branch·tag·commit이 없다. `ref`를 생략했으면 저장소에 기본 브랜치가 없다(커밋 없는 저장소). `ref`를 확인한다 |
| `invalid_ref` (400) | `ref` 형식이 틀렸거나, `ref`를 생략했는데 저장소의 기본 브랜치 이름이 Runway의 `ref` 규칙에 맞지 않는다. 그때는 tag나 commit SHA를 `ref`로 보낸다 |
| `source_too_large` (413, push로 시작한 Deployment의 `errorCode`) | 소스 아카이브가 설치의 한도를 넘는다. 저장소를 줄이거나 운영자가 한도를 올린다 |
| `source_busy` (503) | `release` 없는 `deploy`에서 Runway가 한 번에 읽는 소스 수가 한도에 있거나 같은 Project의 다른 소스를 읽는 중이다. Deployment는 만들어지지 않았다. 메시지의 시간(10초) 뒤에 같은 요청을 다시 보낸다. push로 시작한 Deployment는 Runway가 다시 읽으므로 할 일이 없다 |
| `git_host_removed` (409, push로 시작한 Deployment의 `errorCode`) | Studio가 그 Git 호스트를 더 이상 Git 호스트로 두지 않는다. 운영자가 Studio에 그 호스트를 다시 등록한다. push 배포의 상태와 위임은 그대로이고, 호스트를 되돌리면 다음 push부터 배포된다 |
| `invalid_repository` (400) | 새 Project의 저장소가 이 설치의 Git 호스트에 있지 않거나 저장소 주소 형식이 틀렸다(GitHub는 정확히 `owner/repo`, port가 있는 주소는 받지 않는다). 메시지가 Git 호스트를 알려 준다 |
| `push_delegation_invalid` | push로 시작한 Deployment가 `prepare` 스텝에서 실패했다. push 배포를 켠 사용자가 Studio에서 위임을 폐기했거나, 그 호스트의 연결을 해제했거나, 다른 계정을 연결했다. `push.state`가 `delegation_invalid`가 되고 그 뒤의 push도 같은 code로 실패한다. 소유자나 Studio 관리자가 push 배포를 다시 켠다 |
| `policy_refused` (403) | `push_enable`에서 Studio가 그 사용자에게 Git 위임을 주지 않는다. 사용자 등급이 허용하지 않거나 그 Git 계정의 위임이 한도에 찼다. 한도에 찼으면 사용자가 Studio의 프로필 → Git 계정에서 위임을 폐기한다 |
| `push_busy` (409) | 같은 Project의 push 배포 켜기·끄기는 한 번에 하나만 진행한다. 다른 변경이 진행 중이라 기다리지 않고 거절됐다. 메시지의 시간(5초) 뒤에 다시 호출한다. `push_enable`을 다시 호출하면 승인 카드도 다시 뜬다 |
| `checkout_failed` | `prepare` 스텝의 실패다. push한 commit이 저장소에 없거나, build가 소스 아카이브를 풀지 못했다 |
| `test_failed`, `build_failed`, `deploy_failed`, `verify_failed` | `deployment_logs(deploymentId, step)`로 원인을 읽는다. verify는 health 경로가 2xx를 돌려줘야 한다 |
| `deployment_not_started` (409), `logs_not_found` (404) | 그 스텝에 읽을 출력이 없다. workflow 전에 실패했거나(`application_changed` 등), `resources` 스텝이거나, workflow가 끝난 지 하루가 지났다. 다시 호출하지 말고 `deployment_get`의 `errorCode`와 `statusMessage`로 판단한다 |
| `delivery_unavailable` (502), `provider_unavailable` (503) | 운영 문제다. 다시 시도해도 같은 결과이므로 반복하지 않는다 |
| 리소스 `failed` | 같은 이름으로 `resource_create`를 다시 하거나 콘솔에서 재시도한다 |
