---
name: ci-failure-investigator
description: >
  실패한 CI·GitHub Actions 실행의 로그와 revision을 조사해 원인과 해결 방법을 찾을 때 쓴다.
  코드·테스트·의존성·실행 환경·일시적 실패를 구별하고 요청된 경우에만 수정한다.
  서비스의 운영 장애는 incident-triage, 단순 PR 검토는 code-review를 쓴다.
---

# CI 실패 조사

실패한 실행을 증거로 삼는다. 최신 브랜치가 아니라 실패한 run·attempt·commit을 먼저 식별한다.

## 증거 수집

1. 저장소, workflow/run URL 또는 ID, attempt, event, branch와 head SHA를 확인한다.
2. 실패한 job·step과 처음 나타난 의미 있는 오류를 읽고 이후의 연쇄 실패와 분리한다.
   로그는 필요한 구간부터 제한해서 읽고 누락·잘림·취소·진행 중 상태를 구별한다.
3. 해당 SHA의 workflow, Runtime·OS·패키지 관리자 버전, lockfile과 관련 변경을 확인한다.
   마지막 성공 실행과 비교할 때도 event·matrix·환경 차이를 함께 본다.

GitHub에서는 실제 제공된 Actions 조회·job 로그 도구를 사용한다. 현재 이름·인자는 schema가 정한다.
`pull_request_read`의 check/status는 CI 결과를 보여 줄 수 있지만 전체 Actions step 로그를 보장하지 않는다.
도구가 없거나 로그가 만료됐다면 사용자 제공 로그로 좁히고 미확인 원인을 성공·실패로 단정하지 않는다.

## 원인 판정과 재현

코드 결함, 검사 설정, 의존성·Runtime 불일치, 권한·시크릿·네트워크·리소스 문제와 일시적 오류를
관찰 근거로 구분한다. 테스트 이름만 보고 flaky라고 하지 않는다. 조사 요청만이면 보고서로 끝낸다.

수정까지 요청됐으면 기존 Workspace에서 관련 코딩 task를 수행한다. 실패 SHA와 다른 HEAD라면
같은 실행을 재현했다고 하지 않는다. 접근 가능한 branch와 정확한 SHA를 검증할 수 없으면
원격 자료를 사용하거나 재현 환경의 차이를 보고한다. Git fetch·checkout을 보호된 메타데이터에서 우회하지 않는다.
운영 자격증명 없이 재현 가능한 범위만 실행하고 로그의 시크릿은 값 대신 위치·유형으로 설명한다.

## 완료 기준

실패 위치·원인 근거·수정 또는 운영 조치·검증 결과·남은 불확실성을 제시한다.
로컬 재현 통과와 해당 수정 SHA의 CI 성공은 별개다. `checks=[]`는 Workspace 검사 설정만 뜻한다.
GitHub run의 status/conclusion과 commit을 새로 확인하고 재실행했다면 attempt도 기록한다.

단순 조사를 위해 workflow를 재실행·취소·배포하거나 시크릿·권한·검사를 변경하지 않는다.
재실행도 사용자가 요청한 run에 한정하며 무제한 반복하지 않는다. 코드 게시에는 `prepare_git`와 승인 화면을 사용한다.
