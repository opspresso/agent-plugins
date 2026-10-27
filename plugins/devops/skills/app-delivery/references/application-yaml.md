# application.yaml과 배포 조건

저장소 루트의 `application.yaml`이 앱 하나를 선언한다. Agent Broker가 검증하고, Delivery가 이 선언대로 빌드·배포한다.

## 예시

```yaml
apiVersion: agent.opspresso.com/v1
kind: Application
spec:
  name: todo                  # Broker Project slug
  repository: nalworks/todo   # owner/repo
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
      - name: main
        class: postgres
    env:
      LOG_LEVEL: debug
  prod:
    replicas: 2
    maxReplicas: 4
    resources:
      - name: main
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
| `resources` | 아니요 | `{name, class}`. class는 `postgres`·`bucket`. 이름이 `main`이면 Variable에 접두어가 없다 | |
| `secrets` | 아니요 | 사용자가 Broker 콘솔에서 입력할 Variable 이름 | |
| `env` | 아니요 | 비밀이 아닌 환경 변수. 값 1 KiB 이하 | |

- 알 수 없는 필드는 거부된다.
- `env`·`secrets` 이름은 `^[A-Z][A-Z0-9_]{0,63}$`이다. `PORT`와 리소스 Variable 이름은 쓸 수 없다.
- `dev`의 `env`·`secrets`는 Forge Sandbox 예약 이름(`OPENAI_`·`ANTHROPIC_`·`AWS_`·`GIT_`로 시작하는 이름 등)을 쓸 수 없다.
  예: dev는 `APP_OPENAI_API_KEY`, prod는 `OPENAI_API_KEY`.

## 리소스 Variable

| class | Variable (`main`이면 접두어 없음, 아니면 `<NAME>_`) |
| --- | --- |
| `postgres` | `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`. `vector` 확장을 쓸 수 있다 |
| `bucket` | `S3_BUCKET`, `S3_PREFIX`, `S3_REGION`. 배포된 앱은 Pod Identity로, Forge Run은 임시 AWS credential로 접근한다. prefix 밖은 거부된다 |

앱은 `S3_PREFIX` 아래에만 쓴다. AWS SDK의 기본 credential 체인을 쓰면 두 환경에서 같은 코드가 동작한다.

## 컨테이너 조건

- 이미지는 linux/arm64로 빌드된다. arm64를 지원하지 않는 base image나 바이너리를 쓰지 않는다.
- `PORT`에서 HTTP를 받는다. TLS는 플랫폼이 처리한다.
- 컨테이너는 privilege escalation 없이, 모든 capability를 뺀 상태로 실행된다. 1024 미만 포트를 쓰지 않는다.
- 외부 연결은 HTTPS(443)와 Broker PostgreSQL만 허용된다. 다른 포트의 외부 API는 쓸 수 없다.
- 기동 후 3분 안에 health 경로가 2xx를 반환해야 한다. DB migration은 기동 시 실행하되 실패하면 health가 실패하게 한다.
- 로그는 stdout·stderr로 쓴다. 비밀 값을 로그에 쓰지 않는다.

## Node.js 예시

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
// server.js: PORT와 /health
import http from "node:http";
const server = http.createServer((req, res) => {
  if (req.url === "/health") { res.writeHead(200, { "content-type": "application/json" }); return res.end('{"ok":true}'); }
  res.writeHead(404); res.end();
});
server.listen(Number(process.env.PORT ?? 8080));
```
