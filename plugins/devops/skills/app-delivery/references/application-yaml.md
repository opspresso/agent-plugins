# application.yaml과 배포 조건

저장소 루트의 `application.yaml`이 앱 하나를 선언한다. Agent Delivery가 검증하고, Delivery가 이 선언대로 빌드·배포한다.

## 예시

```yaml
apiVersion: agent.opspresso.com/v1
kind: Application
spec:
  name: todo                  # Agent Delivery Project slug
  repository: nalworks/todo   # owner/repo
  owner: 3f2c9d1e-…          # Studio subject of the Project owner
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
environments:
  dev:
    resources:
      - name: todo            # same as spec.name: unprefixed DATABASE_URL, PGHOST, …
        class: postgres
    env:
      LOG_LEVEL: debug
  prod:
    replicas: 2
    maxReplicas: 4
    resources:
      - name: todo
        class: postgres
    secrets: [API_KEY]
    cpu: 250m
    memory: 512Mi
```

## 필드

| 필드 | 필수 | 규칙 | 기본값 |
| --- | --- | --- | --- |
| `spec.name` | 예 | slug. `-dev`·`-prod`로 끝날 수 없다 | |
| `spec.repository` | 예 | `owner/repo`. Project의 저장소와 같아야 한다 | |
| `spec.owner` | 예 | Project 소유자의 Studio subject. 아래 [소유자](#소유자)를 따른다 | |
| `spec.description` | 아니요 | 200자 이하 | |
| `runtime.port` | 예 | 1024~65535. 플랫폼이 `PORT`로도 넘긴다 | |
| `runtime.health` | 아니요 | `/`로 시작하는 경로 | `/health` |
| `runtime.build.context`, `dockerfile` | 아니요 | 저장소 안의 상대 경로 | `.`, `Dockerfile` |
| `runtime.test.image`, `command` | 아니요 | 이미지와 `/bin/sh -c`로 실행할 명령. 저장소 루트에서 실행한다 | 없으면 건너뜀 |
| `runtime.command`, `args` | 아니요 | 문자열 목록 | 이미지 기본값 |
| `environments.<env>` | 예 | `dev`·`prod` 중 하나 이상 | |
| `replicas` | 아니요 | 1~5 | 1 |
| `maxReplicas` | 아니요 | `replicas`~10. 크면 CPU 70% 기준 자동 확장 | `replicas` |
| `cpu`, `memory` | 아니요 | `50m`~`1`, `64Mi`~`2Gi`. memory는 limit도 된다 | `100m`, `256Mi` |
| `resources` | 아니요 | `{name, class, parameters?}`. class는 `resource_catalog`의 템플릿. 이름이 `spec.name`(Project slug)과 같으면 Variable에 접두어가 없다 | |
| `secrets` | 아니요 | 사용자가 Agent Delivery 콘솔에서 입력할 Variable 이름 | |
| `env` | 아니요 | 비밀이 아닌 환경 변수. 값 1 KiB 이하 | |

- 알 수 없는 필드는 거부된다.
- `env`·`secrets` 이름은 `^[A-Z][A-Z0-9_]{0,63}$`이다. `PORT`와 리소스 Variable 이름은 쓸 수 없다.
- `dev`의 `env`·`secrets`는 Forge Sandbox 예약 이름(`OPENAI_`·`ANTHROPIC_`·`AWS_`·`GIT_`로 시작하는 이름 등)을 쓸 수 없다.
  예: dev는 `APP_OPENAI_API_KEY`, prod는 `OPENAI_API_KEY`.

## 소유자

`spec.owner`는 Project 소유자의 Studio subject다. Agent Delivery는 이 값이 다르면 `application_owner_mismatch`로 거부하고,
메시지에 기대한 값을 알려 준다. 값은 다음 순서로 정한다.

1. Project가 있으면 `project_get`의 `owner.subject`를 쓴다.
2. 새 Project면 처음 `project_apply`의 `application_owner_mismatch` 메시지가 알려 주는 요청자의 subject를 쓴다.
   그 값으로 파일을 고쳐 commit한 뒤 다시 적용한다.

이 값 덕분에 저장소에 쓸 수 있는 사람만 그 저장소를 자기 Project로 배포할 수 있다. 다른 사람의 값으로 바꾸지 않는다.
`project_owned_elsewhere`이면 다른 사용자가 Project를 소유한 것이다. Studio 관리자에게 소유자 이전을 요청하라고 안내한다.

## 리소스 Variable

| class | Variable (이름이 Project slug면 접두어 없음, 아니면 `<NAME>_`) |
| --- | --- |
| `postgres` | `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`. `vector` 확장을 쓸 수 있다 |
| `bucket` | `S3_BUCKET`, `S3_PREFIX`, `S3_REGION`. 배포된 앱은 Pod Identity로, Forge Run은 임시 AWS credential로 접근한다. prefix 밖은 거부된다 |

앱은 `S3_PREFIX` 아래에만 쓴다. AWS SDK의 기본 credential 체인을 쓰면 두 환경에서 같은 코드가 동작한다.

## 컨테이너 조건

- 이미지는 linux/arm64로 빌드된다. arm64를 지원하지 않는 base image나 바이너리를 쓰지 않는다.
- `PORT`에서 HTTP를 받는다. TLS는 플랫폼이 처리한다.
- 컨테이너는 privilege escalation 없이, 모든 capability를 뺀 상태로 실행된다. 1024 미만 포트를 쓰지 않는다.
- 외부 연결은 HTTPS(443)와 Agent Delivery PostgreSQL만 허용된다. 다른 포트의 외부 API는 쓸 수 없다.
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
