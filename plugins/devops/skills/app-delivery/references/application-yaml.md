# application.yaml과 배포 조건

저장소 루트의 `application.yaml`이 앱 하나를 선언한다. 앱을 빌드·테스트·실행하는 방법과 앱이 받을 `secrets`·`env`만 적는다.
Agent Runway가 이 파일을 검증하고, 이 선언대로 빌드·배포한다. 파일은 최대 64 KiB다.

## 예시

```yaml
apiVersion: agent.opspresso.com/v4
kind: Application
spec:
  name: todo                           # Agent Runway Project slug
  repository: github.com/nalworks/todo # <host>/<path>; owner/repo means GitHub
  owner: 3f2c9d1e-…                   # Studio subject of the Project owner
  description: Todo API
runtime:
  port: 8080
  health: /health
build:
  context: .
  dockerfile: Dockerfile
test:
  image: node:24-alpine
  command: npm ci && npm test
secrets: [API_KEY]
env:
  LOG_LEVEL: info
```

## 필드

| 필드 | 필수 | 규칙 | 기본값 |
| --- | --- | --- | --- |
| `apiVersion`, `kind` | 예 | `agent.opspresso.com/v4`, `Application` | |
| `spec.name` | 예 | Project slug. `^[a-z][a-z0-9-]{1,30}[a-z0-9]$`이고 설치의 환경 이름으로 끝날 수 없다(예: `-dev`, `-prod`). `agent-`·`addon-`·`delivery-`·`kube-`로 시작하는 이름과 `istio`·`argocd`·`default`·`system`은 쓸 수 없다. Project가 있으면 그 slug와 같아야 한다 | |
| `spec.repository` | 예 | `<host>/<path>`. `owner/repo`는 GitHub다. 적용하는 저장소와 같아야 한다 | |
| `spec.owner` | 예 | Project 소유자의 Studio subject. 아래 [소유자](#소유자)를 따른다 | |
| `spec.description` | 아니요 | 200자 이하 | |
| `runtime.port` | 예 | 1024~65535. 플랫폼이 `PORT`로도 넘긴다 | |
| `runtime.health` | 아니요 | `/`로 시작하는 경로 | `/health` |
| `runtime.command`, `runtime.args` | 아니요 | 문자열 1~32개의 목록 | 이미지 기본값 |
| `build.context`, `build.dockerfile` | 아니요 | 저장소 안의 상대 경로. `..`를 쓸 수 없다 | `.`, `Dockerfile` |
| `test.image`, `test.command` | 아니요 | 이미지와 `/bin/sh -c`로 실행할 명령. 저장소 루트에서 실행한다. `test`를 쓰면 둘 다 필요하다 | 없으면 건너뜀 |
| `secrets` | 아니요 | 앱이 배포되는 모든 단계에서 값이 필요한 Variable 이름의 목록. 사용자가 Agent Runway 콘솔에서 단계마다 값을 입력한다 | |
| `env` | 아니요 | 비밀이 아니고 모든 환경에서 같은 값. 값은 문자열·숫자·boolean이고 1 KiB 이하다 | |

- 알 수 없는 필드는 거부된다. 오류(`invalid_application`)는 위반한 필드를 모두 나열한다.
- `secrets`·`env` 이름은 `^[A-Z][A-Z0-9_]{0,63}$`이다. 같은 이름을 `secrets`와 `env`에 함께 쓸 수 없다. `env`에 `PORT`를 쓸 수 없다.
- Project에 이미 있는 Variable의 이름은 `env`에 쓸 수 없다. `secrets`에는 사용자가 입력하는 secret의 이름만 쓴다.
  `resource_create`로 만든 리소스의 Variable과 비밀이 아닌 Variable의 이름은 `secrets`에 쓸 수 없다.
  리소스의 연결 값은 선언하지 않아도 Agent Runway가 그 환경에 배포된 앱에 준다.
- 설치에 sandbox 환경이 있으면 `secrets`·`env`에 Forge Sandbox 예약 이름을 쓸 수 없다. `OPENAI_`·`ANTHROPIC_`·`CLAUDE_`·`AWS_`·`GIT_`로
  시작하는 이름, `_PROXY`로 끝나는 이름, `PATH`·`HOME`·`CI` 등이다. 앱 전용 이름을 쓴다. 예: `OPENAI_API_KEY` 대신 `APP_OPENAI_API_KEY`.
- 커밋하기 전에 파일 전체를 `application_validate`(`repository`, `application`)로 검사한다. 아무것도 만들거나 바꾸지 않는다.

## 파일에 없는 설정

다음은 `application.yaml`에 쓰지 않는다. 쓰면 알 수 없는 필드로 거부된다.

| 설정 | 정하는 곳 |
| --- | --- |
| 환경과 승격 순서, cloud, target type, architecture | Project의 pipeline. 새 Project는 `project_ensure`·`project_apply`의 `pipeline`, 기존 Project는 `project_configure`의 `pipeline` |
| 복제 수·CPU·memory·instance type | pipeline의 단계별 크기(`small`·`medium`·`large`). Project 값은 `project_configure`의 `sizes` |
| 자동 배포를 시작하는 push | pipeline의 trigger. Project 값은 `project_configure`의 `trigger` |
| 앱 주소 | 단계의 위치. 마지막 단계는 `<slug>.<도메인>`, 그 밖의 단계는 `<slug>-<env>.<도메인>`이다. 마지막 단계에도 환경 이름을 붙이려면 `project_configure`의 `suffixEveryStage` |
| 리소스(DB·cache·bucket) | 단계마다 `resource_create` |
| 환경마다 다른 값 | 그 환경의 Variable. 비밀 값은 `secrets`에 이름을 선언하고 `secret_request` 링크로, 비밀이 아닌 값은 콘솔의 Project 환경 변수 화면(`/projects/<slug>/variables`)에서 소유자가 입력한다. 비밀이 아닌 Variable의 이름은 `env`와 `secrets`에 쓰지 않는다. 적용한 `env`에 있는 이름은 콘솔에서 입력할 때 `variable_declared`(409)로 거부된다 |

`apiVersion`이 `agent.opspresso.com/v1`·`v2`·`v3`인 파일은 `invalid_application`으로 거부된다. v4로 다시 쓴다.
`spec`과 `runtime`의 `port`·`health`·`command`·`args`는 유지한다. `pipeline.build`·`pipeline.test`는 최상위 `build`·`test`로 옮긴다.
`secrets`와 `env`는 최상위에 한 번만 쓴다. `runtime.cloud`·`runtime.type`·`runtime.architecture`·`pipeline`·`environments`는 지우고 위 표대로 정한다.

## 소유자

`spec.owner`는 Project 소유자의 Studio subject다. Agent Runway는 이 값이 다르면 `application_owner_mismatch`로 거부하고,
메시지에 기대한 값을 알려 준다. 값은 다음 순서로 정한다.

1. Project가 있으면 `project_get`(또는 `project_ensure` 응답)의 `project.owner.subject`를 쓴다.
2. Project가 없으면 `application_validate`의 `application_owner_mismatch` 메시지가 알려 주는 요청자의 subject를 쓴다.
   그 값으로 파일을 고쳐 다시 검사한다.

이 값 덕분에 저장소에 쓸 수 있는 사람만 그 저장소를 자기 Project로 배포할 수 있다. 다른 사람의 값으로 바꾸지 않는다.
`project_owned_elsewhere`이면 다른 사용자가 Project를 소유한 것이다. Studio 관리자에게 소유자 이전을 요청하라고 안내한다.
`application_name_mismatch`이면 `spec.name`을 메시지가 알려 주는 Project slug로 고친다.

## 리소스 Variable

리소스는 `resource_create`로 만든다. Variable 이름은 `<NAME>_<KEY>`다. `<NAME>`은 리소스 이름을 대문자로 바꾸고 `-`를 `_`로 바꾼 것이다.
리소스 이름이 Project slug와 같으면 접두어가 없다. `<KEY>`는 template의 class가 정한다. 실제 목록은 `resource_catalog`의 `keys`로 확인한다.

| class | `<KEY>` |
| --- | --- |
| `pool-postgres`, `postgres` | `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` |
| `rds-postgres` | `pool-postgres`의 키와 `PGSSLMODE` |
| `valkey` | `VALKEY_URL`, `VALKEY_HOST`, `VALKEY_PORT`, `VALKEY_USERNAME`, `VALKEY_PASSWORD` |
| `bucket` | `S3_BUCKET`, `S3_PREFIX`, `S3_REGION`. 배포된 앱은 Pod Identity로, Forge Run은 임시 AWS credential로 접근한다. prefix 밖은 거부된다 |
| `s3-bucket` | `S3_BUCKET`, `S3_REGION` |
| `dynamodb` | `DYNAMODB_TABLE`, `DYNAMODB_REGION` |

`bucket`을 쓰는 앱은 `S3_PREFIX` 아래에만 쓴다. AWS SDK의 기본 credential 체인을 쓰면 배포된 앱과 Forge Run에서 같은 코드가 동작한다.
`rds-postgres`·`s3-bucket`·`dynamodb`는 sandbox 환경에 만들 수 없다.

## 컨테이너 조건

- 이미지는 Project pipeline의 architecture 하나(`linux/amd64` 또는 `linux/arm64`)로 빌드된다. `project_status`의 `pipeline.architecture`로 확인하고,
  그 architecture를 지원하지 않는 base image나 바이너리를 쓰지 않는다.
- `PORT`에서 HTTP를 받는다. TLS는 플랫폼이 처리한다.
- 컨테이너는 privilege escalation 없이, 모든 capability를 뺀 상태로 실행된다. 1024 미만 포트를 쓰지 않는다.
- 외부 연결은 HTTPS(443)와 Agent Runway PostgreSQL만 허용된다. 다른 포트의 외부 API는 쓸 수 없다.
- 기동 후 3분 안에 health 경로가 2xx를 반환해야 한다. DB migration은 기동 시 실행하되 실패하면 health가 실패하게 한다.
- 로그는 stdout·stderr로 쓴다. 비밀 값을 로그에 쓰지 않는다.

## Node.js 예시

PostgreSQL을 쓰는 앱의 예시다. 기동 시 migration을 실행하고, `/health`는 migration 성공과 DB 연결을 매번 확인한다.
`DATABASE_URL`은 리소스 이름이 Project slug와 같을 때의 Variable이다. 의존성은 `pg`다.

```dockerfile
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build --if-present && npm prune --omit=dev

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
USER node
CMD ["node", "server.js"]
```

```js
// server.js: PORT, 기동 시 migration, DB를 확인하는 /health
import http from "node:http";
import pg from "pg";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL, max: 5 });
let migrated = false;
async function migrate() {
  await pool.query("CREATE TABLE IF NOT EXISTS todo (id serial PRIMARY KEY, title text NOT NULL)");
  migrated = true;
}
migrate().catch((error) => console.error("migration failed:", error.message));

const server = http.createServer(async (req, res) => {
  if (req.url === "/health") {
    try {
      if (!migrated) throw new Error("migration not complete");
      await pool.query("SELECT 1");
      res.writeHead(200, { "content-type": "application/json" });
      return res.end('{"ok":true}');
    } catch {
      res.writeHead(503, { "content-type": "application/json" });
      return res.end('{"ok":false}');
    }
  }
  res.writeHead(404); res.end();
});
server.listen(Number(process.env.PORT ?? 8080));
```

리소스가 없는 앱은 `/health`에서 DB 확인을 뺀다.
