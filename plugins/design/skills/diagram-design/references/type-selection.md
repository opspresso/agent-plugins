# 유형 선택

다이어그램 유형은 모양이 아니라 독자가 따라가야 할 **주된 관계**로 고른다. 두 유형이
겹치면 첫 질문에 답하는 유형 하나를 골라 나머지 의미를 label·group·annotation으로 보탠다.

## 시스템과 데이터 구조

| 독자가 확인할 것 | 유형 | 주된 관계 |
|---|---|---|
| 서비스·모듈이 어떻게 연결되는가 | architecture | 구성과 통신 |
| 소프트웨어가 어느 환경에 배치되는가 | deployment | 실행 위치와 경계 |
| 어떤 모듈이 무엇에 의존하는가 | dependency graph | 방향성 의존 |
| 데이터가 어디서 와서 어디로 가는가 | data flow | 이동과 변환 |
| 개념적 데이터 구조가 무엇인가 | ER diagram | entity와 관계 |
| 실제 DB 테이블이 어떻게 연결되는가 | database schema | column과 FK |
| class의 책임과 관계가 무엇인가 | UML class | 상속·구성·연관 |

architecture에는 구현 파일 목록을 넣지 않는다. deployment에는 논리적 호출 관계보다
zone, host, runtime, replica 같은 실행 경계를 우선한다. ER은 업무 개념, database schema는
물리 이름·type·key를 다룬다.

## 순서와 변화

| 독자가 확인할 것 | 유형 | 주된 관계 |
|---|---|---|
| 조건에 따라 다음 단계가 무엇인가 | flowchart | 분기와 합류 |
| actor 사이 메시지가 어떤 순서인가 | sequence | 시간 순서 |
| 상태가 어떤 사건으로 바뀌는가 | state machine | 상태와 transition |
| 부서·역할 사이 handoff가 어디인가 | swimlane | 책임과 순서 |
| 사용자가 단계마다 무엇을 경험하는가 | journey map | 단계·행동·문제 |
| 일이 어느 상태에 얼마나 쌓였는가 | kanban | 흐름 상태와 WIP |
| 기능이 어느 release에 묶이는가 | story map | 활동과 release slice |
| 사건이나 milestone이 언제 일어나는가 | timeline | 시간 위치 |

순서만 중요하면 sequence나 flowchart를 사용하고, 실제 날짜 간격이 중요할 때만 timeline을
사용한다. 여러 역할의 책임이 핵심이면 일반 flowchart 대신 swimlane을 사용한다.

## 계층과 개념 관계

| 독자가 확인할 것 | 유형 | 주된 관계 |
|---|---|---|
| 상위 항목이 무엇을 거느리는가 | tree | 부모와 자식 |
| 누가 누구에게 보고·위임하는가 | org chart | 소유와 escalation |
| 어떤 범위 안에 무엇이 들어가는가 | nested containment | 포함 |
| 추상화나 방어가 어떤 층으로 쌓이는가 | layer stack | 위아래 순서 |
| 두 기준으로 항목이 어디에 위치하는가 | quadrant | 두 축의 위치 |
| 집합이 어디서 겹치는가 | Venn | 교집합 |
| 단계가 되먹임으로 이어지는가 | loop | 순환과 feedback |
| 한 결과에 어떤 원인군이 기여하는가 | fishbone | 원인 분류 |
| 사용자 가치와 성숙도가 어떻게 연결되는가 | Wardley map | 가치 흐름과 진화 |

tree는 포함 경계를 표현하지 않고, nested는 연결선을 남발하지 않는다. org chart의 선은
데이터 흐름이 아니라 책임 관계다. quadrant의 두 축은 독립적이고 방향 의미가 분명해야 한다.

## 다른 표현이 나은 경우

- 정확한 수치 비교, 추세, 분포: `tufte-charts`
- 행과 열의 교차 값: table 또는 matrix
- 두 상태의 속성 비교: before/after table
- 항목이 세 개 이하이고 연결이 자명함: prose 또는 bullets
- 화면 안에서 사용자가 누를 대상: `frontend-design`

## 기본 크기

| 쓰임 | SVG `viewBox` | 권장 방향 |
|---|---|---|
| 문서 본문 | `0 0 960 600` | 가로 |
| 넓은 architecture | `0 0 1200 675` | 가로 |
| 슬라이드 | `0 0 1280 720` | 가로 16:9 |
| 정사각 게시물 | `0 0 1080 1080` | 중앙 방사 또는 세로 |
| 세로 process | `0 0 720 960` | 위에서 아래 |

사용자가 크기를 지정하지 않으면 문서 본문을 사용한다. 요소 수에 맞추려고 글자를 줄이지
말고 canvas를 넓히거나 다이어그램을 나눈다.

## 공통 예산

| 항목 | 기본 상한 |
|---|---|
| 주요 요소 | 12 |
| 연결선 | 16 |
| 중첩 경계 | 4단계 |
| swimlane | 5 |
| sequence lifeline | 6 |
| 강조 요소 | 2 |
| 별도 annotation | 3 |

상한을 넘는 정보가 모두 필요하면 overview 한 장과 세부 장을 만든다. overview에서 빠진
항목을 숨기지 말고 세부 장으로 이동했다고 밝힌다.
