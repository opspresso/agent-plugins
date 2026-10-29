# Agent Delivery

앱의 Project·환경·리소스·secret·`application.yaml`·배포를 다루거나 Delivery 콘솔을 안내할 때 읽는다.
앱을 처음부터 배포까지 진행하는 절차는 `app-delivery` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **Project**: GitHub 저장소(`owner/repo`) 하나. 처음 등록한 Studio 사용자가 소유자다. slug는 전체에서 유일하며 다시 쓰지 않는다.
- **환경**: 설치 설정이 정한 순서 있는 목록이다. 기본은 `dev`·`prod`이고 `staging` 같은 환경이 더 있을 수 있다. 실제 목록과 규칙은 `project_status`가 준다.
  sandbox 환경(기본 `dev`)의 값만 Forge Sandbox에 전달된다. `approval: owner` 환경은 Agent의 요청을 소유자가 콘솔에서 승인해야 하고,
  `requiresPrevious` 환경(기본 `prod`)은 앞 환경에서 성공한 Release만 받는다.
- **리소스**: 카탈로그 템플릿으로 만든다(`resource_catalog`). `postgres`(`DATABASE_URL`·`PG*`), `bucket`(`S3_BUCKET`·`S3_PREFIX`·`S3_REGION`),
  `rds-postgres`(전용 RDS, 비용이 들고 sandbox 환경 불가, 환경당 2개), `secret`(사용자가 콘솔에서 입력).
  이름이 Project slug와 같은 리소스는 Variable에 접두어가 없다(`DATABASE_URL`). 다른 이름(`main` 포함)은 대문자 이름이 접두어가 된다.
  콘솔의 기본 리소스 이름도 Project slug다.
- **`application.yaml`**: 저장소 루트의 앱 선언(apiVersion `agent.opspresso.com/v1`). 이름·저장소·소유자·runtime(port·health·build·test)·
  환경별 replica·리소스(템플릿 `parameters` 포함)·secret·env를 적는다. 모르는 필드와 설치에 없는 환경은 거절되며 최대 64 KiB다.
- **Release**: build 한 번의 결과 `r<n>`(commit, 이미지 digest, 선언). 상태는 `building`·`ready`·`failed`다.
- **Deployment**: Release 하나를 환경 하나에 배포한다(`deploy`·`promote`·`rollback`). 단계는 prepare → test → build(Release build) → deploy → verify,
  상태는 `awaiting_approval`·`queued`·`running`·`succeeded`·`failed`·`rejected`다.
  주소는 primary 환경(기본 `prod`)이 `https://<slug>.<domain>`, 그 밖은 `https://<slug>-<env>.<domain>`이다.

## Helper가 쓸 수 있는 도구

| 도구 | 용도 | 주의 |
|---|---|---|
| `project_list`, `project_get`, `resource_catalog`, `resource_get` | Project·리소스 상태, 템플릿, Variable 이름 | 읽기 전용. 값은 반환하지 않는다 |
| `project_status` | 환경마다 현재 Release·주소·진행 중 Deployment·승인 링크·리소스 상태 | 읽기 전용. 대화창에 환경 표로 그려질 수 있다 |
| `release_list`, `release_get` | Release와 환경별 Deployment 이력 | 읽기 전용 |
| `deployment_list`, `deployment_get`, `deployment_logs` | 배포 목록·상태·단계 로그(마지막 64 KiB) | 읽기 전용. 승인 대기면 `approvalUrl`이 있다. 로그는 workflow 실행 중과 끝난 뒤 하루 동안 있다 |
| `deployment_lookup_request` | 응답 유실 복구 | 같은 `idempotencyKey`로 조회한다 |
| `project_ensure`, `project_apply` | Project 생성, `application.yaml` 적용과 선언된 리소스 생성 | `project_apply`는 값이 없는 secret마다 입력 링크를 돌려준다 |
| `resource_create` | 템플릿과 `parameters`로 리소스 생성 | 접수형. `pending → ready | failed` |
| `deploy`, `promote`, `rollback` | ref를 첫 환경에 배포, 같은 Release를 다음 환경으로 승격, 직전 Release로 되돌리기 | 접수형. `idempotencyKey` 필수. 결과는 원래 Chat으로 돌아온다. `approval: owner` 환경은 소유자 승인 대기 |
| `secret_request` | secret 입력 콘솔 링크 | 읽기 전용이라 승인 없이 실행된다. 링크만 돌려준다. 값은 묻지 않는다 |

삭제 도구는 없다. Studio는 `delivery:delete`를 위임하지 않는다.

## Secret

secret 값은 대화로 받지 않는다. `project_apply` 결과의 링크나 `secret_request`가 돌려준 콘솔 링크를 사용자에게 준다.
입력 페이지는 `/projects/<slug>/secrets/new?environment=<env>&variable=<NAME>`이다.
sandbox 환경(기본 `dev`) Variable에는 Sandbox 예약 이름을 쓰지 않는다. 예: `OPENAI_API_KEY` 대신 `APP_OPENAI_API_KEY`.

## 콘솔 페이지 (`agent-delivery`)

| 경로 | 용도 |
|---|---|
| `/` | Project 목록, `application.yaml`로 Project 생성 |
| `/projects/<slug>` | 환경별 상태·Release 이력·리소스·Variable·`application.yaml`. 소유자의 deploy·promote·rollback |
| `/projects/<slug>/deployments/<id>` | Deployment 단계·로그, 소유자의 승인 |
| `/projects/<slug>/secrets/new` | secret 값 입력 |
| `/profile` | 계정 정보 |

콘솔 전용 작업: secret 입력·변경, 값 보기(소유자, 감사 기록), 리소스·Project 삭제(이름 재입력), `approval: owner` 환경 배포 승인·거절(소유자만,
Studio 관리자도 불가), 소유권 이전·private checkout 허용(Studio 관리자). 소유자가 콘솔에서 시작한 배포는 승인이 필요 없다.

## 오류

| 코드 | 원인과 해결 |
|---|---|
| `invalid_application` (400) | 메시지가 잘못된 필드를 모두 나열한다. 파일을 고쳐 다시 적용한다 |
| `application_owner_mismatch`, `application_name_mismatch` (409) | `owner`·이름이 Project와 다르다. 메시지의 기대 값을 쓴다 |
| `project_owned_elsewhere` (409) | 다른 사용자의 Project다. Studio 관리자가 소유권을 이전해야 한다 |
| `environment_not_ready` (409) | 메시지가 준비되지 않은 리소스·secret을 알려 준다. secret 링크를 주고 리소스 `ready`를 확인한다 |
| `deployment_in_progress` (409) | 진행 중인 배포를 먼저 확인한다 |
| `release_not_promoted` (409) | `requiresPrevious` 환경에 앞 환경에서 성공하지 않은 Release를 배포하려 했다. 앞 환경에 `deploy`한 뒤 `promote`한다 |
| `no_rollback_target`, `no_next_environment` (409) | 되돌릴 Release나 승격할 다음 환경이 없다. `project_status`로 확인한다 |
| `invalid_parameters` (400), `template_limit_reached` (409) | 템플릿 parameter가 틀렸거나 환경당 개수를 넘었다. `resource_catalog`를 본다 |
| `quota_exceeded` (409) | Project·리소스 수 한도. 기본은 소유자당 Project 20개, 환경당 리소스 20개이며 설치마다 다르다. 정확한 한도는 오류 메시지에 있다 |
| `approval_expired` | 승인이 24시간을 넘었다. 다시 요청한다 |
| `application_changed` | 커밋된 파일로 `project_apply`를 다시 하고 다시 배포한다 |
| `checkout_failed` | 대개 private 저장소의 checkout이 허용되지 않았다. Studio 관리자 확인이 필요하다 |
| `test_failed`, `build_failed`, `deploy_failed`, `verify_failed` | `deployment_logs(deploymentId, step)`로 원인을 읽는다. verify는 health 경로가 2xx를 돌려줘야 한다 |
| `deployment_not_started` (409), `logs_not_found` (404) | 그 단계에 읽을 출력이 없다. workflow 전에 실패했거나(`application_changed` 등) workflow가 끝난 지 하루가 지났다. 다시 호출하지 말고 `deployment_get`의 `errorCode`와 메시지로 판단한다 |
| `delivery_unavailable` (502), `provider_unavailable` (503) | 운영 문제다. 다시 시도해도 같은 결과이므로 반복하지 않는다 |
| 리소스 `failed` | 같은 이름으로 `resource_create`를 다시 하거나 콘솔에서 재시도한다 |
