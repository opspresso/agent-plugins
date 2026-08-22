# 시스템 다이어그램

시스템 계열은 구성 요소의 이름보다 **경계와 관계의 의미**가 먼저 읽혀야 한다. 입력에서
확인되지 않은 protocol, datastore, replica를 관례라는 이유로 추가하지 않는다.

## Architecture

**내용 모델:** actor, entry point, service, store, external system, zone, connection.

- 기본 읽기 방향은 왼쪽에서 오른쪽이다.
- public entry, application, data, external zone 순으로 배치하되 실제 경계를 우선한다.
- 호출과 event 흐름이 섞이면 solid/dashed처럼 두 종류까지만 사용하고 직접 label을 붙인다.
- 같은 zone 안의 내부 요소를 모두 연결하지 않는다. 독자가 알아야 할 호출만 남긴다.
- 기술 이름은 node detail에, 책임은 node title에 둔다.

**권장 예산:** zone 4개, node 12개, connection 16개.

**피할 것:** 모든 요소를 동일한 service box로 표현하기, network 경계를 제목만으로 암시하기,
양방향 관계를 설명 없이 화살표 두 개로 그리기.

## Deployment

**내용 모델:** environment, region/zone, host/runtime, artifact, replica, endpoint.

- 바깥에서 안쪽으로 environment → zone → runtime의 포함 관계를 만든다.
- logical service 관계보다 실제 실행 위치와 배포 단위를 우선한다.
- replica는 같은 상자를 여러 개 복제하기보다 `×N`으로 표현한다. 개별 차이가 있을 때만 나눈다.
- port와 protocol은 해당 경계를 통과하는 connector 가까이에 둔다.
- shared infrastructure와 application workload의 경계를 구분한다.

**권장 예산:** zone 4개, workload 10개, external endpoint 4개.

## Dependency graph

**내용 모델:** component, directed dependency, optional/required kind, cycle.

- 의존 방향을 제목이나 legend에 명시한다. 예: `A → B`는 A가 B를 필요로 한다.
- 가능한 한 rank를 만들어 왼쪽에서 오른쪽으로 정렬한다.
- fan-in이 큰 node는 중앙에 두지 말고 읽기 방향 끝쪽에 둔다.
- cycle은 숨기지 말고 다른 stroke나 annotation으로 표시한다.
- transitive edge가 핵심 정보를 더하지 않으면 생략한다.

**권장 예산:** node 12개, direct edge 18개, cycle 1개.

## Data flow

**내용 모델:** source, transform, store, sink, payload, batch/stream kind.

- 데이터가 이동하는 방향을 한 방향으로 유지한다.
- node에는 시스템 이름보다 수행하는 변환을 먼저 적는다.
- connector label은 `event`, `file`, `record`, `query`처럼 전달물을 말한다.
- control call과 data movement를 섞지 않는다. 둘 다 필요하면 line style을 분리한다.
- batch와 stream을 색만으로 구분하지 않는다.

**권장 예산:** stage 6개, source/sink 6개, flow 14개.

## ER diagram

**내용 모델:** entity, identifier, important attribute, cardinality, optionality.

- 업무 개념 이름을 사용하고 DB type이나 index는 넣지 않는다.
- 각 entity에는 식별자와 관계 이해에 필요한 attribute만 보인다.
- 관계 이름을 동사로 적으면 양쪽 entity를 읽을 때 문장이 되어야 한다.
- cardinality와 optionality를 생략하지 않는다.
- 다대다 관계에 실제 associative entity가 주어졌으면 별도 entity로 표현한다.

**권장 예산:** entity 8개, entity당 attribute 6개, relation 12개.

## Database schema

**내용 모델:** table, column, type, PK/UK/FK, column-level relation.

- table header와 column 영역을 시각적으로 분리한다.
- key badge는 `PK`, `FK`, `UK`처럼 짧게 통일한다.
- FK connector는 table 중앙이 아니라 실제 column 행에서 출발하고 도착한다.
- 모든 column을 담기 어렵다면 key와 관계에 필요한 column만 보이고 생략을 표시한다.
- index나 constraint가 질문과 관계없으면 별도 note로 빼거나 생략한다.

**권장 예산:** table 6개, table당 표시 column 8개, FK 10개.

## UML class

**내용 모델:** class/interface, responsibility, selected field, selected operation, relation kind.

- class 이름, field, operation compartment를 구분한다.
- visibility와 type은 사용자가 주었거나 코드에서 확인된 경우에만 적는다.
- inheritance, implementation, composition, aggregation, association의 line style을 섞지 않는다.
- method 목록을 API 문서처럼 전부 옮기지 않는다. 책임 이해에 필요한 것만 남긴다.
- package가 중요하면 옅은 zone으로 묶되 class relation보다 강하게 보이지 않게 한다.

**권장 예산:** class 8개, class당 member 6개, relation 12개.

## 공통 배치 판단

1. zone을 먼저 계산한다.
2. 연결이 많은 node의 위치를 정한다.
3. 나머지를 읽기 방향 rank에 배치한다.
4. connector 경로를 정한 뒤 label 자리를 확보한다.
5. 마지막에 note와 legend를 넣는다.

선이 세 번 이상 꺾이거나 여러 zone을 왕복하면 node 배치가 잘못된 것이다. connector를
미세 조정하기 전에 구조를 다시 잡는다.
