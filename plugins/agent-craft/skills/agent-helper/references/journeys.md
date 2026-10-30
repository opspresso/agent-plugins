# 여러 서비스에 걸친 작업

사용자가 결과 하나를 얻으려고 여러 서비스를 거쳐야 할 때 읽는다. 각 단계에서 이미 끝난 준비는 건너뛴다.
먼저 조회 도구로 현재 상태를 확인하고, 사용자가 해야 하는 콘솔 작업은 정확한 페이지를 열어 준다.

## 앱 개발부터 배포까지

Forge가 코드를, Runway가 리소스와 배포를 소유한다. 실제 진행은 `app-delivery` Skill이 있으면 그것을 따른다.

| 단계 | 누가 | 무엇을 | 확인 |
|---|---|---|---|
| 1. 준비 | 사용자 | Forge `/git`에서 GitHub 연결, `/settings`에서 저장소 생성을 허용하는 profile 선택 | `git_connections`, `profile_get` |
| 2. 저장소·코드 | Helper/Agent | `repository_create`, `run_submit`(Git `prepare` → 작업 → 검사 → push → PR). 코드에는 `application.yaml`, `PORT`를 듣는 arm64 `Dockerfile`, health 경로가 있어야 한다 | Run 결과가 Chat으로 돌아온다 |
| 3. merge | 사용자 | `run_submit`의 Git `merge`는 보호된 작업이다. 소유자가 Run 제한 시간 안에 Forge `/git?approval=<id>`에서 승인한다 | `git_approval_get` |
| 4. 리소스 | Helper/Agent | main의 `application.yaml`로 `project_apply` | 결과의 리소스 상태와 secret 링크 |
| 5. secret | 사용자 | Runway secret 링크에서 값 입력 | `project_get`에서 `environment_not_ready`가 사라짐 |
| 6. dev 배포 | Helper/Agent | `deploy(environment="dev", ref="main")`로 Release를 build해 배포 | 결과가 Chat으로 돌아온다. `https://<slug>-dev.<domain>` |
| 7. prod 배포 | Helper/Agent → 사용자 | `promote(from="dev")`로 dev에서 성공한 Release를 prod에 배포. 소유자가 24시간 안에 `approvalUrl`에서 승인 | `deployment_get`, `project_status` |

설정 변경은 PR → merge → `project_apply` → 다시 배포 순서다. 리소스·Project 삭제는 Runway 콘솔에서 사용자가 한다.

## 녹음에서 회의록까지

1. 기본 오디오 profile을 확인한다(`audio_profile_get`). 없으면 콘솔 `/recordings/settings`에서 만들거나 모델을 직접 고른다.
2. 녹음을 Chat에 첨부하게 한다(최대 512 MiB). 더 크면 Knowledge 콘솔 `/recordings`에서 올린다.
3. `recording_import` → `audio_job_submit`. 결과는 Chat으로 돌아온다.
4. 반복해서 쓸 거라면 `agent-knowledge`와 `audio-processing`·`meeting-minutes` Skill을 연결한 회의록 Agent를 만든다.

## 문서 기반 Q&A Agent

1. 문서를 Knowledge에 넣는다: 콘솔 `/documents` 업로드 또는 `document_ingest`. `ready`를 확인한다.
   팀이 함께 쓸 자료는 `team` scope로 둔다.
2. Agent를 만든다: `mcpList`에 `agent-knowledge`(검색 도구만 골라도 된다), Skill `workspace-search`.
3. 프롬프트에 "답은 `context_search` 근거와 출처로 한다. 근거가 없으면 없다고 말한다"를 넣는다.
4. 대표 질문으로 Playground에서 확인하게 안내한다.

## 기억하는 Agent

1. Agent의 `mcpList`에 `agent-memory`를 연결하고 `recall`을 허용한다.
2. `parameters.memoryRecall`을 켠다. 실행 뒤 자동으로 단기 기억을 남기려면 `memoryCapture`도 켜고 `memory_capture`를 허용한다.
3. 프롬프트에 언제 `remember`할지(사용자가 요청할 때, 확인된 선호·결정)와 기본 scope를 적는다.

## 코딩 Agent 준비

1. Forge 처음 설정을 마친다. [forge](forge.md#처음-설정)
2. Agent를 만든다: `mcpList`에 `agent-forge`, Skill `workspace-task`와 필요한 engineering Skill(`implement-feature`, `fix-issue`, `code-review` 등).
   긴 작업이 많으므로 `maxTurn`을 늘린다.
3. 배포까지 하려면 `agent-delivery`와 `app-delivery`도 연결한다.
4. 첫 작업으로 작은 요청(README 수정 PR 등)을 보내 GitHub 연결과 profile을 확인하게 한다.

## 메신저 봇 Agent

1. Agent를 만들거나 고른다.
2. `StudioRequestCredential(kind="slack"|"telegram"|"teams")`로 credential을 받는다.
3. `StudioUpdateIntegration`으로 활성화한다. Slack은 추천 프롬프트·채널 키워드를 함께 정할 수 있다.
4. 정기 보고가 필요하면 `StudioSaveTrigger`로 schedule을 만들고 `deliveries`에 채널을 넣는다.
5. 실제 채널에서 메시지를 보내 응답을 확인하게 안내한다. 저장 성공은 전달 성공이 아니다.
