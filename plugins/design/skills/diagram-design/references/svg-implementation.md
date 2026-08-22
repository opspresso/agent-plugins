# SVG 구현

SVG는 그림 파일이 아니라 의미 구조를 담은 문서로 작성한다. 좌표를 쓰기 전에 영역과
연결 순서를 정하고, connector가 겹치면 path를 계속 꺾기보다 node 배치를 바꾼다.

## DOM 순서

다음 순서로 그리면 가림 관계를 예측하기 쉽다.

1. `<title>`, `<desc>`, `<defs>`
2. 전체 배경과 zone
3. connector와 arrowhead
4. connector label의 배경 mask와 text
5. node
6. node 내부 text와 badge
7. annotation과 legend

node를 connector보다 뒤에 그려 선의 끝이 box 안으로 파고든 것처럼 보이지 않게 한다.
공통 legend는 어느 zone에도 포함되지 않는 별도 하단 strip에 둔다. 특정 zone 안에 놓으면
그 zone에만 적용되는 설명으로 오해된다.

## 접근성

```svg
<svg viewBox="0 0 960 600" role="img"
     aria-labelledby="checkout-flow-title checkout-flow-desc">
  <title id="checkout-flow-title">주문 승인과 결제 처리 흐름</title>
  <desc id="checkout-flow-desc">고객 요청이 재고 확인과 결제 승인을 거쳐 주문으로 저장되는 흐름</desc>
  <defs>...</defs>
</svg>
```

- `title`은 SVG의 첫 child다.
- `desc`는 shape 위치가 아니라 독자가 알아야 할 내용을 설명한다.
- 한 HTML에 여러 SVG가 들어갈 수 있으므로 id에 diagram slug를 붙인다.
- 색만으로 구분한 상태는 text나 line style을 함께 제공한다.
- 복잡한 다이어그램은 SVG 뒤에 짧은 HTML summary를 둘 수 있다.

## Connector

기본 연결은 수평·수직 segment로 만든다. 대각선은 좌표 자체가 의미인 scatter나 Wardley
map이 아니라면 피한다.

```svg
<defs>
  <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink-muted)"/>
  </marker>
</defs>
<path d="M 248 180 H 312 V 260 H 376"
      fill="none" stroke="var(--ink-muted)" stroke-width="1.5"
      marker-end="url(#flow-arrow)"/>
```

- box의 옆면 중앙을 무조건 공유하지 않는다. 여러 선이면 attach point를 분산한다.
- parallel connector 사이는 최소 12px를 둔다.
- connector가 endpoint가 아닌 node를 통과하지 않게 한다.
- 교차가 불가피하면 한 선에 작은 bridge를 만들거나 경로를 다른 corridor로 옮긴다.
- 양방향 의미는 화살표 두 개를 포개지 말고 두 선으로 분리하거나 명확한 양방향 marker를 쓴다.
- connector 종류는 세 가지 이하로 제한하고 legend나 직접 label로 설명한다.

## Connector label

선 위에 text만 올리지 않는다. 배경과 여백을 함께 둔다.

```svg
<rect x="292" y="224" width="72" height="22" rx="3" fill="var(--bg)"/>
<text x="328" y="239" text-anchor="middle" font-size="11"
      fill="var(--ink-muted)">ORDER EVENT</text>
```

- mask가 node 경계에 걸리지 않는 열린 공간을 고른다.
- 선과 글자 사이에 6px 이상 간격을 둔다.
- 세로 선 label은 글자를 회전하지 말고 선 옆에 수평으로 둔다.
- protocol, payload, condition처럼 관계를 이해시키는 내용만 쓴다.

## Node

```svg
<g class="node">
  <rect x="80" y="128" width="168" height="88" rx="6"
        fill="var(--bg)" stroke="var(--ink)"/>
  <text x="96" y="158" font-size="14" font-weight="600" fill="var(--ink)">주문 API</text>
  <text x="96" y="180" font-size="11" fill="var(--ink-muted)">요청 검증과 orchestration</text>
  <text x="96" y="199" font-size="10" fill="var(--brand-deep)">HTTPS :443</text>
</g>
```

- node title은 한두 줄로 제한한다.
- 자동 줄바꿈을 기대하지 말고 `<tspan>`으로 줄을 나눈다.
- 긴 설명은 node 밖 note로 옮긴다.
- badge는 역할을 실제로 구분할 때만 사용한다.
- icon이 없어도 의미가 유지되어야 한다.

## Zone

- zone을 node보다 먼저 그린다.
- label은 왼쪽 위에 고정하고 내부 node와 16px 이상 떨어뜨린다.
- trust boundary는 dashed stroke와 명시적 label을 함께 사용한다.
- zone 안에 zone이 두 단계 이상 들어가면 각 경계의 의미가 다른지 확인한다.

## 좌표 계산

먼저 상수와 식을 정하고 마지막에 숫자를 넣는다.

```text
canvas width = 960
outer padding = 48
column gap = 48
column width = (960 - 2*48 - 2*48) / 3 = 256
node width = 176
node x = column x + (column width - node width) / 2
```

같은 rank의 node 중심을 맞추고 connector corridor를 최소 24px 확보한다. 좌표가 조금씩
흔들리면 눈으로 보정하기 전에 기준선 계산을 다시 확인한다.

## 반응형과 인쇄

```css
.diagram-frame { overflow-x: auto; }
.diagram-frame svg { display: block; width: 100%; min-width: 720px; height: auto; }
@media (max-width: 760px) {
  .diagram-frame svg { width: 900px; }
}
@media print {
  .diagram-frame { overflow: visible; }
  .diagram-frame svg { min-width: 0; max-width: 100%; }
}
```

복잡한 SVG를 모바일 폭에 맞춰 무작정 축소하지 않는다. 가로 scroll이 작은 글자보다 낫다.

## 최종 육안 검사

- marker가 destination box 경계에 닿는가?
- connector가 node fill 뒤에서 사라지는 구간이 없는가?
- label mask가 다른 글자나 node를 가리지 않는가?
- line이 포개져 관계 하나처럼 보이지 않는가?
- 모든 text가 viewBox 안에 들어오는가?
- 100%와 67% zoom에서 label을 읽을 수 있는가?
- 흑백 인쇄에서도 상태를 구분할 수 있는가?
