# Agent Delivery

앱의 Project·환경·리소스·secret·`application.yaml`·배포를 다루거나 Delivery 콘솔을 안내할 때 읽는다.
앱을 처음부터 배포까지 진행하는 절차는 `app-delivery` Skill이 있으면 그것을 따른다. 실제 도구 schema가 이 문서보다 우선한다.

## 개념

- **Project**: GitHub 저장소(`owner/repo`) 하나. 처음 등록한 Studio 사용자가 소유자다. slug는 전체에서 유일하며 다시 쓰지 않는다.
- **환경**: `dev`·`prod`. Forge Sandbox에는 `dev` 값만 전달된다.
- **리소스**: `postgres`(`DATABASE_URL`·`PG*`), `bucket`(`S3_BUCKET`·`S3_PREFIX`·`S3_REGION`), `secret`(사용자가 콘솔에서 입력).
  `main`이라는 이름의 리소스는 Variable에 접두어가 없다. 다른 이름은 대문자 이름이 접두어가 된다.
- **`application.yaml`**: 저장소 루트의 앱 선언(apiVersion `agent.opspresso.com/v1`). 이름·저장소·소유자·runtime(port·health·build·test)·
  환경별 replica·리소스·secret·env를 적는다. 모르는 필드는 거절되며 최대 64 KiB다.
- **Delivery**: prepare → test → build → deploy → verify. 상태는 `awaiting_approval`·`queued`·`running`·`succeeded`·`failed`·`rejected`다.
  주소는 dev `https://<slug>-dev.<domain>`, prod `https://<slug>.<domain>`이다.

## Helper가 쓸 수 있는 도구

| 도구 | 용도 | 주의 |
|---|---|---|
| `project_list`, `project_get`, `resource_classes`, `resource_get` | Project·리소스 상태와 Variable 이름 | 읽기 전용. 값은 반환하지 않는다 |
| `delivery_list`, `delivery_get`, `delivery_logs` | 배포 목록·상태·단계 로그(마지막 64 KiB) | 읽기 전용. 대기 중 prod는 `approvalUrl`이 있다 |
| `delivery_lookup_request` | 응답 유실 복구 | 같은 `idempotencyKey`로 조회한다 |
| `project_ensure`, `project_apply` | Project 생성, `application.yaml` 적용과 선언된 리소스 생성 | `project_apply`는 값이 없는 secret마다 입력 링크를 돌려준다 |
| `resource_create` | postgres·bucket 생성 | 접수형. `pending → ready | failed` |
| `delivery_start` | dev·prod 배포 시작 | 접수형. 결과는 원래 Chat으로 돌아온다. prod는 소유자 승인 대기 |
| `secret_request` | secret 입력 콘솔 링크 | 읽기 전용이라 승인 없이 실행된다. 링크만 돌려준다. 값은 묻지 않는다 |

삭제 도구는 없다. Studio는 `delivery:delete`를 위임하지 않는다.

## Secret

secret 값은 대화로 받지 않는다. `project_apply` 결과의 링크나 `secret_request`가 돌려준 콘솔 링크를 사용자에게 준다.
입력 페이지는 `/projects/<slug>/secrets/new?environment=<env>&variable=<NAME>`이다.
dev Variable에는 Sandbox 예약 이름을 쓰지 않는다. 예: `OPENAI_API_KEY` 대신 `APP_OPENAI_API_KEY`.

## 콘솔 페이지 (`agent-delivery`)

| 경로 | 용도 |
|---|---|
| `/` | Project 목록, `application.yaml`로 Project 생성 |
| `/projects/<slug>` | 환경·리소스·Variable·`application.yaml`·Delivery 목록 |
| `/projects/<slug>/deliveries/<id>` | 단계·로그, 소유자의 prod 승인 |
| `/projects/<slug>/secrets/new` | secret 값 입력 |
| `/profile` | 계정 정보 |

콘솔 전용 작업: secret 입력·변경, 값 보기(소유자, 감사 기록), 리소스·Project 삭제(이름 재입력), prod 배포 승인·거절(소유자만,
Studio 관리자도 불가), 소유권 이전·private checkout 허용(Studio 관리자). 소유자가 콘솔에서 시작한 prod 배포는 승인이 필요 없다.

## 오류

| 코드 | 원인과 해결 |
|---|---|
| `invalid_application` (400) | 메시지가 잘못된 필드를 모두 나열한다. 파일을 고쳐 다시 적용한다 |
| `application_owner_mismatch`, `application_name_mismatch` (409) | `owner`·이름이 Project와 다르다. 메시지의 기대 값을 쓴다 |
| `project_owned_elsewhere` (409) | 다른 사용자의 Project다. Studio 관리자가 소유권을 이전해야 한다 |
| `environment_not_ready` (409) | 메시지가 준비되지 않은 리소스·secret을 알려 준다. secret 링크를 주고 리소스 `ready`를 확인한다 |
| `delivery_in_progress` (409) | 진행 중인 배포를 먼저 확인한다 |
| `quota_exceeded` (409) | Project·리소스 수 한도. 기본은 소유자당 Project 20개, 환경당 리소스 20개이며 설치마다 다르다. 정확한 한도는 오류 메시지에 있다 |
| `approval_expired` | prod 승인이 24시간을 넘었다. 새 Delivery를 시작한다 |
| `application_changed` | 커밋된 파일로 `project_apply`를 다시 하고 새 Delivery를 시작한다 |
| `checkout_failed` | 대개 private 저장소의 checkout이 허용되지 않았다. Studio 관리자 확인이 필요하다 |
| `test_failed`, `build_failed`, `deploy_failed`, `verify_failed` | `delivery_logs(deliveryId, step)`로 원인을 읽는다. verify는 health 경로가 2xx를 돌려줘야 한다 |
| `delivery_unavailable` (502), `provider_unavailable` (503) | 운영 문제다. 다시 시도해도 같은 결과이므로 반복하지 않는다 |
| 리소스 `failed` | 같은 이름으로 `resource_create`를 다시 하거나 콘솔에서 재시도한다 |
