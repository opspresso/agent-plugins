---
name: app-delivery
description: >
  앱 하나를 저장소 생성·개발부터 리소스·빌드·테스트·배포·서비스 확인까지 Agent Delivery와 Agent Forge로 진행할 때 쓴다.
  application.yaml로 앱을 선언하고 Agent Delivery project_apply·deploy·promote로 dev·prod에 배포한 뒤 URL을 확인한다.
  코드 변경만 필요하면 implement-feature, 기존 GitOps 설정 변경은 gitops-change를 쓴다.
metadata:
  org.opspresso.agent-studio.icon: rocket
---

# 앱 전달

사용자가 요청한 앱을 실행 중인 서비스로 만든다. 저장소·코드·`application.yaml`·리소스·Delivery·응답하는 URL이
모두 확인될 때 완료다. PR이나 이미지 push만으로 완료라고 하지 않는다.

필요한 연결: Agent Delivery MCP(`project_apply`, `deploy`, `promote` 등)와 Agent Forge MCP(Workspace·Git).
둘 중 하나가 없으면 할 수 있는 단계까지만 진행하고, 없는 연결과 남은 단계를 알린다.

## 1. 요구사항과 이름

1. 앱의 목적·핵심 기능·데이터·외부 API와 필요한 Environment(`dev`, `prod`)를 확인한다. 정해진 부분은 묻지 않는다.
2. 저장소 owner를 정한다. 사용자가 정하지 않았으면 Agent 지침이 정한 기본 owner를 쓰고, 그것도 없으면 묻는다.
3. 이름(slug)을 정한다. `^[a-z][a-z0-9-]{1,30}[a-z0-9]$`이고 `-dev`·`-prod`로 끝날 수 없다.
   저장소 이름과 같게 하면 추적이 쉽다. 주소는 `https://<slug>-dev.<앱 도메인>`(dev), `https://<slug>.<앱 도메인>`(prod)이다.

## 2. 저장소와 코드

1. 새 저장소는 연결된 `project-generator` 절차로 Forge `repository_create`를 실행하고 `private: false`로 만든다.
   Delivery의 checkout은 인증 없이 clone하므로 비공개 저장소는 `checkout_failed`로 실패한다. 사용자가 비공개를 요구하면
   Delivery로 배포할 수 없다고 먼저 알리고 결정을 받는다. 기존 비공개 저장소를 임의로 공개로 바꾸지 않는다.
2. 앱이 DB·버킷을 쓰면 코드를 쓰기 전에 `dev` 리소스를 만든다. `project_ensure`(`repository`)로 Project를 만들고
   `resource_create`(`environment: dev`, `class`, `name`, `idempotencyKey`)를 호출한 뒤 `resource_get`으로 `ready`를 확인한다.
   기본 `name`은 Project slug다. 이 리소스의 Variable에는 접두어가 없다(`DATABASE_URL`). `main`은 다른 이름처럼 `MAIN_` 접두어가 붙는다.
   접속 정보는 Agent Delivery가 SSM SecureString에 저장한다. 값은 Chat·코드·로그에 쓰지 않고 Variable 이름만 쓴다.
   나중에 `application.yaml`이 같은 이름·class로 선언하면 `project_apply`가 이 리소스를 그대로 쓴다.
3. 코드를 구현한다. 배포에 필요한 조건은 다음과 같다. 세부 규칙과 예시는 [application.yaml과 배포 조건](references/application-yaml.md)을 읽는다.
   - 저장소 루트의 `application.yaml`(`spec.owner`에 Project 소유자의 Studio subject)
   - `Dockerfile`: linux/arm64에서 빌드되고, `PORT` 환경 변수의 포트에서 HTTP를 받는다.
   - health 경로(기본 `/health`): 리소스를 선언한 앱은 매 요청에서 각 리소스에 실제로 연결하고(PostgreSQL은 `SELECT 1`)
     기동 시 migration이 성공했을 때만 2xx를 반환한다. Delivery의 verify는 이 경로만 확인하므로 고정 응답은 DB 장애를 숨긴다.
   - 테스트 명령: 외부 리소스 없이 끝나야 한다. Delivery의 test 단계에는 Agent Delivery Variable이 없다.
4. Forge Run의 checks(test·lint·build)로 확인한다. `dev` 리소스가 `ready`이면 Forge가 Run의 명령 환경에 그 Variable을
   넣으므로 migration과 DB 연동을 실제 DB로 확인한다. 이 확인은 Forge에서만 가능하다. Delivery의 test 단계에는 DB가 없다.
5. Git `review`·`commit`·`push`·`pull-request`로 PR을 만든다. `pull-request`는 승인을 만들지 않는다.
6. PR의 CI가 통과하면 Git `merge`를 제출한다. 보호 작업이므로 Run이 승인을 기다리며 `approvalUrl`을 반환한다.
   그 링크를 사용자에게 주고, 병합 Run이 `succeeded`인지 확인한 뒤 다음 단계로 간다. 승인 없이 다른 경로로 병합하지 않는다.

## 3. 선언 적용과 리소스

1. 배포할 revision(기본 병합된 main)의 `application.yaml` 내용을 그대로 `project_apply`에 넘긴다(`repository`, `application`).
   Delivery는 그 revision의 파일 SHA-256이 적용한 내용과 같은지 확인하므로, 한 글자라도 다르면 `application_changed`로 실패한다.
2. 결과의 리소스가 `ready`가 될 때까지 `project_status`로 확인한다. `failed`이면 원인을 보고한다.
3. `missingSecrets`가 있으면 각 `secret_request` 링크를 사용자에게 준다. 값은 Chat으로 받지 않는다.
   사용자가 입력했다고 하면 `project_get`으로 Variable 이름이 생겼는지 확인한다.
4. `invalid_application`이면 오류의 필드를 고쳐 2단계의 PR로 다시 반영한다.

## 4. 배포와 승격

환경과 규칙(승인, 앞 환경 성공 필요 여부)은 설치마다 다르다. 먼저 `project_status`로 환경 순서와 `approval`·`requiresPrevious`를 확인한다.
기본은 `dev`(바로 실행) → `prod`(앞 환경에서 성공한 Release만, 소유자 승인)이다.

1. 첫 환경에 `deploy`(`project`, `environment`, `ref`, `idempotencyKey`)를 호출한다. 기본 ref는 `main`이다.
   Agent Delivery가 ref를 build해 Release(`r<n>`)를 만들고 배포한다.
2. 다음 환경은 `promote`(`project`, `from`, `idempotencyKey`)로 같은 Release를 배포한다. 다시 build하지 않으므로 앞 환경에서 검증한 이미지가 그대로 간다.
   `requiresPrevious` 환경에 `deploy`로 ref를 보내면 `release_not_promoted`다.
   `approval: owner` 환경은 `awaiting_approval`과 `approvalUrl`을 반환한다. 링크를 사용자에게 주고 소유자가 Agent Delivery 콘솔에서 승인하게 한다.
3. Studio가 Deployment를 따라가다 끝나면 결과를 Chat에 전달하고 대화를 이어 준다. 같은 Deployment를 기다리며
   `deployment_get`을 반복 호출하지 않는다. 사용자가 진행 상황을 물으면 한 번 조회해 단계(`step`)를 알린다.
   응답을 잃었으면 같은 key로 `deployment_lookup_request`를 읽는다.
4. 결과를 확인한다.
   - `succeeded`: verify 단계가 새 rollout을 확인하고 `url`의 health 경로가 2xx를 반환한 것까지 검증했다는 뜻이다.
     `url`, health 경로, Release 이름과 `revision`(짧은 SHA)을 알린다. HTTP 요청 도구가 없어도 health를 미검증으로 보고하지 않는다.
   - `failed`: `step`과 `errorCode`를 확인하고 `deployment_logs`(`deploymentId`, `step`)로 원인을 읽는다.
     코드 문제는 2단계로 고친 뒤 다시 배포한다. `delivery_unavailable`은 플랫폼 문제다. 코드나 선언을 바꾸지 말고
     Deployment ID와 단계를 사용자에게 알린다. `application_changed`이면 배포한 ref의 `application.yaml`을
     읽어 그 내용을 3단계로 적용하거나, 적용한 선언과 같은 파일을 가진 ref로 다시 배포한다. 다른 ref의 파일을 적용하지 않는다.
     같은 실패를 원인 확인 없이 다시 시작하지 않는다.
   - `rejected`: 소유자가 거절했거나 승인이 만료됐다. 다시 요청할지 사용자에게 확인한다.
5. `environment_not_ready`이면 오류가 알려 준 리소스·secret을 3단계로 준비한다. `deployment_in_progress`이면 진행 중인
   Deployment가 끝나기를 기다린다.
6. 배포한 Release에 문제가 있으면 `rollback`(`project`, `environment`, `idempotencyKey`)으로 그 환경의 직전 Release를 다시 배포한다.

## 5. 운영과 변경

- Variable 값을 바꾸면 다시 배포해야 Pod가 다시 시작해 값을 읽는다.
- 설정(복제 수·자원·환경 변수)은 `application.yaml`을 고치는 PR → 병합 → `project_apply` → 배포·승격 순서로 바꾼다.
  GitOps 저장소의 배포 값 파일을 직접 고치지 않는다.
- 장애 조사는 `incident-triage`를 쓴다. 앱 namespace는 `app-<slug>-<env>`, Deployment 이름은 `app`이다.
- 리소스·Project 삭제는 Agent Delivery 콘솔에서 소유자만 한다. MCP로 삭제를 시도하지 않는다.

## 보고

단계마다 확인한 사실만 보고한다: 저장소와 PR, 적용한 선언의 SHA, 리소스 상태, Release 이름, Deployment ID·상태·URL.
승인을 기다리는 단계와 사용자가 할 일(승인, secret 입력)을 분리해 알린다.
