# 프로세스 다이어그램

프로세스 계열은 box의 모양보다 **진행 조건, 책임 주체, 종료 상태**가 정확해야 한다.
단계를 명사 대신 동사구로 쓰고, 모든 분기는 다시 합류하거나 명확한 종료점에 닿게 한다.

## Flowchart

- 시작과 종료를 명시한다.
- 작업은 동사구, 판단은 답할 수 있는 질문으로 쓴다.
- decision에서 나가는 모든 선에 조건 label을 붙인다.
- 기본 경로는 직선에 가깝게, 예외 경로는 옆으로 분기한다.
- 여러 조건을 하나의 diamond 안에 쉼표로 나열하지 않는다.

**예산:** step 12개, decision 4개, exception branch 3개.

## Sequence

- actor/lifeline을 요청이 시작되는 쪽에서 종속 대상 순으로 배치한다.
- 위에서 아래가 시간 순서이며, 실제 지연 시간을 y 간격으로 암시하지 않는다.
- message label은 동사와 핵심 payload를 포함한다.
- synchronous call, asynchronous message, response를 line style과 arrowhead로 구분한다.
- 반복·조건 구간은 frame 하나로 묶고 guard를 적는다.
- 내부 구현 호출을 모두 나열하지 말고 경계 사이의 의미 있는 message만 남긴다.

**예산:** lifeline 6개, message 16개, condition/repeat frame 2개.

## State machine

- 상태는 지속되는 조건, transition은 사건이나 guard다.
- action을 상태 이름으로 쓰지 않는다. `결제 처리 중`은 상태, `결제 처리`는 action이다.
- initial state와 terminal state를 구분한다.
- 자기 전이는 실제 의미가 있을 때만 보인다.
- 동일 event가 여러 상태에서 다른 결과를 만들면 guard를 함께 적는다.
- 도달 불가능하거나 나갈 수 없는 상태가 입력에 있으면 감추지 말고 note로 알린다.

**예산:** state 10개, transition 16개, terminal state 3개.

## Swimlane

- lane은 사람·팀·시스템처럼 책임을 가진 주체다. 단계 유형을 lane으로 쓰지 않는다.
- 각 작업은 실제 수행 주체의 lane 안에 둔다.
- handoff는 lane 경계에서 명확히 교차하게 한다.
- 승인 대기와 실제 검토를 별도 상태로 보여야 하는지 판단한다.
- lane 안에서 긴 세로 connector가 생기면 단계 순서를 다시 정리한다.

**예산:** lane 5개, step 15개, handoff 10개.

## Journey map

- column은 시간 순서의 stage, row는 `행동`, `접점`, `문제`, `기회`처럼 같은 기준이다.
- 감정은 실제 입력이 있을 때만 표시하고 임의의 곡선을 만들지 않는다.
- pain point는 원인과 영향을 짧게 연결한다.
- 개선 아이디어는 현재 경험과 다른 row에 둔다.
- 사용자의 경험과 내부 운영 절차를 한 row에 섞지 않는다.

**예산:** stage 6개, row 4개, 강조 pain point 3개.

## Kanban

- column은 작업 상태이며 진행 방향을 일관되게 둔다.
- WIP limit가 있으면 column header에 표시하고 초과를 text로 알린다.
- card에는 식별자, 짧은 제목, blocker처럼 흐름 판단에 필요한 것만 둔다.
- 우선순위와 진행 상태를 같은 색 체계로 표현하지 않는다.
- 완료된 항목을 너무 많이 보여 전체 흐름을 가리지 않는다.

**예산:** column 5개, card 15개, card당 metadata 2개.

## Story map

- 맨 위에는 사용자 활동의 backbone을 순서대로 둔다.
- 각 활동 아래에 세부 task를 세로로 배치한다.
- release slice는 가로 cut line과 label로 구분한다.
- 우선순위와 release를 같은 축으로 중복 표현하지 않는다.
- 활동이 서로 독립적이면 억지로 순서 화살표를 넣지 않는다.

**예산:** activity 6개, release 3개, task 18개.

## Timeline

- 실제 시간 간격이 의미 있으면 비례 축을, 순서만 중요하면 균등 간격을 사용하고 이를 밝힌다.
- 같은 시점 사건은 위아래로 번갈아 배치하되 연결 순서를 흐리지 않는다.
- 기간은 점이 아니라 span으로 표현한다.
- 미래 계획, 실제 발생, 불확실한 날짜를 style과 label로 구분한다.
- 긴 설명은 timeline 밖 note로 빼고 사건에는 짧은 결론만 둔다.

**예산:** event 12개, concurrent track 3개, period 4개.

## 공통 완결성 검사

- 모든 경로가 시작과 종료 사이에 연결되는가?
- 판단 조건이 빠진 branch가 없는가?
- 같은 단계가 이름만 다르게 중복되지 않는가?
- 예외와 retry가 정상 경로로 잘못 보이지 않는가?
- actor와 책임이 입력에서 추적 가능한가?
