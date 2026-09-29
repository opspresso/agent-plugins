# PR과 Workspace 리뷰

Review Pull Request는 기본적으로 읽기 작업이다. PR의 설명이나 CI가 녹색인 것만으로 승인하지 않는다.

## 원격 자료와 revision

저장소·PR 번호·base/head repo·branch·SHA를 확인한다. 변경 파일·diff·관련 코드를 동일한
head SHA에서 읽고, 이미 제기된 리뷰와 CI가 어느 revision을 가리키는지 확인한다.
리뷰 도중 HEAD가 바뀌면 최신 변경을 확인하거나 검토한 SHA를 명시한다.
fork PR을 base 저장소의 같은 이름 브랜치로 잘못 읽지 않는다.

호스트가 `ReviewSource`를 제공하면 고정된 PR 자료를 그 도구로 읽는다. 수동 리뷰에서
GitHub MCP를 쓰면 실제 제공 도구와 `pull_request_read`의 methods·paging을 확인한다.
큰 diff는 파일별로 좁히고 결과가 잘렸으면 읽은 범위에서만 판단한다.

## Webhook 자동 리뷰

호스트가 서명과 PR HEAD를 검증한 뒤 Workspace를 자동으로 준비한다. `ReviewSource`로
누락·잘린 diff와 고정 revision의 자료를 읽고, 준비된 `Workspace`의 `run`으로 관련 코드와
저장소 지침을 읽거나 격리 검사를 실행한다. `status`·`wait`로 실행 결과를 끝까지 확인한다.
다른 Workspace를 선택하거나 저장소·런타임·revision을 바꾸지 않는다.
소스 tree를 바꾸지 않고 임시 재현 스크립트는 `/tmp`에 둔다. 게시 전 호스트가 실제 HEAD와
tree를 확인하므로 변경된 소스에서 실행한 결과는 게시할 수 없다.
미완료 작업이나 읽지 못한 자료를 검증했다고 보고하지 않는다. 최종 본문에는 결함의
파일·줄·영향과 실제 검토·검사 범위, 미확인 사항을 적는다. 게시와 Workspace 종료는 호스트가
담당하므로 GitHub 게시 도구나 종료 도구를 중복 호출하지 않는다.

## 수동 리뷰에서 Sandbox가 필요한 경우

MCP의 자료만으로 충분하면 Workspace를 만들지 않는다. 재현·테스트가 필요하면 연결된
`workspace-task`로 현재 선택과 허용 저장소를 확인한다. 호스트 앱의 start는 branch를 기준으로 clone하며
임의 commit checkout이나 PR ref fetch를 제공하지 않는다.

대상 head repo/branch를 연결할 수 있고 현재 작업과 맞을 때만 실행한다. task의 첫 단계에서
읽기 전용 Git 검사로 실제 HEAD가 검토 대상 SHA와 일치하는지 확인한다. 다르면 멈추고 그 차이를 보고한다.
기존 Workspace의 다른 코드에서 통과한 테스트를 PR 검증으로 사용하지 않는다.
허용 목록에 없는 fork나 확인할 수 없는 revision은 원격 파일·diff로 검토하고 실행 검증의 한계를 알린다.

검사에는 허가된 격리 자원과 테스트 데이터만 사용한다. 리뷰 요청으로 소스 수정·자동 fix·snapshot 갱신을
하지 않는다. 설치·테스트가 파일을 만들 수 있으므로 전후 Diff를 확인하고 사용자의 기존 변경을 되돌리지 않는다.
Git 메타데이터 쓰기나 인증된 fetch·checkout을 native task로 우회하지 않는다.

## 결과와 게시

근거가 있는 지적, 파일·줄·발생 조건·영향과 필요한 검증을 보고한다. 코드가 아니라
질문이나 취향인 내용은 결함으로 포장하지 않는다. 지적이 없으면 검토 범위와 미검증 영역을 함께 적는다.

사용자가 리뷰 제출·코멘트 게시를 요청했을 때만 해당 PR의 현재 HEAD와 기존 pending review를
확인하고 제공된 GitHub 리뷰 도구를 사용한다. approve/request-changes 판정도 사용자가 요청한 범위다.
리뷰 요청을 파일 수정·새 브랜치 생성·PR 병합으로 확대하지 않는다.
