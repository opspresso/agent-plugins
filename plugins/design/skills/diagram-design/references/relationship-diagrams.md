# 관계 다이어그램

관계 계열은 연결선 수보다 **공간 배치 자체**로 의미를 전달한다. 포함, 계층, 두 축, 순환을
서로 섞지 말고 주된 문법 하나를 선택한다.

## Tree

- root를 위나 왼쪽에 두고 한 방향으로 깊어진다.
- sibling은 같은 depth에 정렬한다.
- 부모가 하나가 아니면 tree가 아니라 dependency graph를 검토한다.
- subtree가 반복되면 대표 node와 개수로 축약한다.

**예산:** depth 4, node 15개, 한 parent의 child 6개.

## Org chart

- 보고, 위임, escalation 중 선이 의미하는 관계를 제목이나 legend에 명시한다.
- 직책과 이름의 위계를 구분한다.
- assistant, dotted-line report, external advisor는 main reporting line과 다른 style을 사용한다.
- 팀 규모를 모든 개인 box로 표현하지 말고 역할 또는 team 단위로 묶는다.

**예산:** depth 4, node 14개, dotted relation 4개.

## Nested containment

- 가장 큰 scope부터 안쪽으로 배치한다.
- 경계 label은 왼쪽 위의 일정한 위치에 둔다.
- 포함만으로 관계가 설명되면 connector를 추가하지 않는다.
- 중첩 면적을 양이나 중요도로 오해할 수 있으면 caption에서 면적에 의미가 없다고 밝힌다.

**예산:** depth 5, sibling container 6개, leaf 12개.

## Layer stack

- 위아래 방향이 `상위 의존`, `처리 순서`, `방어 깊이` 중 무엇인지 명시한다.
- 모든 layer를 같은 높이로 그리되 중요도처럼 보일 이유가 있으면 의도적으로 다르게 한다.
- cross-cutting concern은 layer 하나로 끼우지 말고 옆이나 아래의 별도 bar로 둔다.
- layer 사이 interface가 핵심이면 경계에 label을 붙인다.

**예산:** layer 7개, cross-cutting bar 3개.

## Quadrant

- x와 y축은 서로 다른 기준이어야 하고 낮음→높음 방향을 label로 쓴다.
- 중간선이 실제 threshold인지 단순 guide인지 구분한다.
- 항목이 겹치면 작은 offset이나 leader line을 사용하고 좌표 의미를 바꾸지 않는다.
- quadrant 이름은 평가가 아니라 해석을 돕는 짧은 문구로 둔다.
- 정량 근거가 없으면 위치가 상대 평가임을 밝힌다.

**예산:** item 14개, 강조 item 2개.

## Venn

- 집합은 최대 세 개로 제한한다.
- 모든 교집합에 의미가 있는지 먼저 확인한다.
- 면적을 수량으로 읽게 할 데이터가 없으면 circle 크기를 비슷하게 유지한다.
- 긴 목록은 원 안에 넣지 말고 대표 항목과 별도 설명을 사용한다.
- 교집합이 복잡하면 matrix나 table이 더 적합하다.

## Loop

- 각 단계는 다음 단계를 일으키는 동사구다.
- 시작 trigger와 관찰 가능한 결과를 표시한다.
- 마지막에서 첫 단계로 돌아오는 연결이 실제 feedback인지 확인한다.
- 중심에 공유 상태가 있다면 모든 단계와 선으로 연결하지 말고 읽기·쓰기 관계만 보인다.
- 나선형이나 장식적 원 대신 연결 방향과 label을 명확히 한다.

**예산:** stage 7개, feedback connector 2개, 중심 상태 1개.

## Fishbone

- 머리에는 분석할 결과를 한 문장으로 둔다.
- 큰 뼈는 원인 category, 작은 가지는 관찰된 원인이다.
- solution이나 action item을 원인과 같은 가지에 섞지 않는다.
- 근거가 없는 원인을 채우기 위해 유명 category를 기계적으로 추가하지 않는다.
- 인과가 아니라 단순 분류라면 tree가 더 적합하다.

**예산:** category 6개, category당 cause 4개.

## Wardley map

- 세로축은 사용자 가치 흐름, 가로축은 진화 단계를 뜻한다.
- 사용자의 필요를 맨 위에 두고 이를 충족하는 component를 아래로 연결한다.
- 위치는 상대 판단이며 근거를 note로 남긴다.
- movement는 현재 위치와 목표 위치를 선으로 구분한다.
- 일반 architecture처럼 배치하지 않는다. 위치 자체가 전략 판단이다.

**예산:** component 12개, value-chain edge 14개, movement 4개.

## 공통 검사

- 위치와 크기가 의도하지 않은 수량 의미를 만들지 않는가?
- 관계가 공간만으로 충분한데 선을 중복해서 넣지 않았는가?
- 축과 방향의 의미가 제목 없이도 찾을 수 있는가?
- 겹침 때문에 label이 다른 집합이나 node 소속처럼 보이지 않는가?
