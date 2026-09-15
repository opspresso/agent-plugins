# Git 검토와 승인

Agent Studio의 Workspace Git 동작 계약이다. 실제 제공된 schema가 우선하며 사용자의 요청 범위만 준비한다.
조회·파일 수정·커밋·작업 브랜치 푸시·PR·main 반영·배포는 서로 다른 단계다.

| 요청 | prepare_git의 action | 전제·결과 |
|---|---|---|
| 로컬 커밋 | kind=commit, message | 실제 변경을 커밋하고 체크포인트에 저장 |
| 커밋과 작업 브랜치 푸시 | kind=commit-and-push, message | 검토한 변경을 커밋·보존한 뒤 같은 HEAD 게시 |
| 이미 커밋된 작업 브랜치 푸시 | kind=push | 깨끗한 트리 필요, PR은 만들지 않음 |
| PR 생성·기존 PR 설명/Draft 변경 | kind=pull-request, title, body, draft | 커밋 필요, 작업 브랜치 게시 포함, 해당 브랜치의 열린 PR 재사용 |
| 이 Workspace의 PR을 main으로 병합 | kind=merge, pullRequestNumber, headSha | status.pull_request의 number/headSha 사용, 열린 Ready PR의 정확한 HEAD 필요 |
| PR 없이 main 직접 푸시 | kind=push-main | 먼저 작업 브랜치에 커밋·푸시, 검토한 main에 fast-forward만 허용 |

```json
{"request":{"operation":"prepare_git","action":{"kind":"commit-and-push","message":"feat: implement requested changes"}}}
```

```json
{"request":{"operation":"prepare_git","action":{"kind":"pull-request","title":"Implement requested changes","body":"Actual change and validation results","draft":false}}}
```

선택된 Workspace가 없을 때만 명시적인 workspace_id가 필요하다. 예시의 제목·본문은 실제 결과로 바꾼다.
PR 설명의 형식이 필요하고 `pr-description`이 연결됐으면 해당 Skill을 사용한다.

pending은 실행 성공이 아니다. 반환된 approval_url(없으면 상대 approval_path)을 그대로 링크로 전달하고 승인까지 멈춘다.
`source_chat_url`이 반환된 Chat 요청은 승인 성공·실패·거절 결과가 원래 채팅에 전달되고 Agent가 자동 재개된다.
사용자에게 같은 요청을 다시 보내도록 요구하거나 승인 여부를 계속 polling하지 않는다. 재개 시
`status.git_action`의 action·status·result를 읽고 PR URL·commit SHA를 확인한다.

사용자가 커밋·푸시 → PR → main 병합을 요청했다면 승인된 단계의 성공 뒤 다음 단계의 `prepare_git`를
준비한다. 커밋·푸시가 끝났다는 이유로 PR 요청까지 완료했다고 하지 않으며, PR 생성이 끝났다는 이유로
main 병합 요청까지 완료했다고 하지 않는다. 각 승인은 해당 action만 실행한다. 다음 승인 링크를 제공할 때
그 동작과 이미 완료한 단계를 정확히 구분한다. 최종 요청이 끝나면 실제 결과를 보고한다.

`source_chat_url`이 없는 Playground·직접 Workspace 요청은 자동으로 이어질 원래 Chat이 없다.
자동 진행을 약속하지 않고 같은 공간의 상태 확인 방법을 제공한다. 재개가 실패·중단됐다는 상태가 있으면
저장된 채팅 답변과 Workspace의 실제 결과를 먼저 확인한다. 성공한 Git 동작은 다시 실행하지 않는다.
이 도구는 승인 결정을 대신 내리지 않는다. 새 요청을 위해 아직 대기 중인 다른 검토를 임의로 승인하지 않는다.

main 반영은 대기 중·실패한 검사가 있으면 막힌다. ci=none은 **보고된 검사 없음**이며 성공이 아니다.
검사 미보고 상태로 승인하는 의미를 알리고 GitHub의 브랜치 보호 규칙을 따른다. Branch가 갈라지면
force push로 덮지 않는다. PR 경로에서 충돌과 필요한 수정·검증을 확인한다.
사용자가 PR 병합을 요청했는데 직접 main 푸시로 대체하지 않는다.

Workspace가 소유하지 않은 외부 PR은 이 merge 동작의 대상이 아니다. 그 PR의 읽기·리뷰는 MCP로
수행할 수 있지만 로컬 Workspace가 해당 HEAD를 소유한다고 가정하지 않는다.
배포는 Git·배포 화면에 설정된 workflow 경로를 사용한다. Skill이나 Sandbox에 배포 권한이 생기는 것은 아니다.

/control/git와 index.lock 쓰기 거절은 보호된 Git 경계다. native task에 git add·commit·push·merge·fetch·checkout을
시키거나 chmod·임시 index·다른 Git 디렉터리·GitHub 파일 쓰기로 우회하지 않는다. 필요한 파일 수정과
읽기 전용 Git 검사는 가능하다. 실패한 인자를 바로잡을 수 없으면 실제 오류와 필요한 기능을 설명한다.

uncertain은 외부 결과가 불명확한 상태다. 새 승인·새 공간·다른 API로 같은 게시를 반복하지 않는다.
failed라면 원인을 확인하고 수정한 뒤 새 검토를 준비한다. 성공한 단계를 실패한 것처럼 다시 실행하지 않는다.
