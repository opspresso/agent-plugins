# 디자인 시스템

기존 브랜드나 제품의 design token이 있으면 그것을 우선한다. 없으면 아래 기본값을 사용한다.
색상 값은 SVG 곳곳에 직접 반복하지 말고 CSS custom property로 선언한다.

## 토큰

```css
:root {
  --bg: #FFFFFF;
  --surface: #F5F7F8;
  --surface-strong: #EAF1F3;
  --rule: #CBD5DB;
  --ink: #18222B;
  --ink-muted: #4F5D68;
  --brand: #17324D;
  --brand-light: #2D6A78;
  --brand-deep: #0B5D7A;
  --on-brand: #FFFFFF;
  --positive: #147D64;
  --negative: #B8433F;
  --font-sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
```

외부 웹폰트를 불러오지 않는다. 한국어를 포함하면 `<html lang="ko">`를 선언하고 시스템이
적절한 glyph를 선택하게 한다.

## 색의 역할

- `--bg`: 전체 canvas와 연결선 label mask
- `--surface`: zone과 보조 container
- `--surface-strong`: 선택 영역, callout, 약한 강조
- `--rule`: 경계와 보조선
- `--ink`: 제목, 핵심 label, 주요 connector
- `--ink-muted`: 설명, 보조 label, 비강조 connector
- `--brand`: 제목과 중심 요소
- `--brand-light`: 강조선과 선택한 흐름
- `--brand-deep`: 외부 연결이나 링크 의미
- `--positive`, `--negative`: 명시적인 결과 상태에만 사용

좋음·나쁨을 색만으로 표현하지 않는다. `PASS`, `BLOCKED`, `DEGRADED` 같은 text label이나
shape 차이를 함께 둔다. 강조색은 1~2개 요소에만 사용한다.

## 글자 위계

| 역할 | 크기 | 굵기 | 글꼴 |
|---|---:|---:|---|
| page title | 28~36px | 700 | sans |
| diagram subtitle | 14~16px | 400 | sans |
| zone title | 12px | 700 | sans |
| node title | 13~15px | 600 | sans |
| node detail | 10~12px | 400 | sans |
| protocol·port·field type | 10~11px | 500 | mono |
| connector label | 10~11px | 600 | sans 또는 mono |

기술 용어라고 모든 글자를 mono로 만들지 않는다. code, port, path, protocol처럼 글자 폭이
의미를 도울 때만 mono를 쓴다.

## 간격과 형태

8px 단위를 기본으로 하고 4px은 정렬 보정에만 사용한다.

- node 내부 padding: 12~16px
- node 사이 최소 간격: 32px
- zone 내부 padding: 24px
- connector와 text 사이: 6px 이상
- corner radius: 4~8px
- node stroke: 1~1.5px
- group boundary: 1px, 필요하면 dashed

모든 상자를 같은 크기·채움으로 만들지 않는다. 역할을 다음처럼 구분한다.

| 의미 | 처리 |
|---|---|
| 중심 요소 | `--surface-strong` fill + `--brand-light` stroke |
| 일반 처리 요소 | 흰 fill + `--ink` stroke |
| 저장소·상태 | `--surface` fill + `--ink-muted` stroke |
| 외부 시스템 | 흰 fill + dashed `--ink-muted` stroke |
| zone·trust boundary | `--surface`의 옅은 fill + `--rule` stroke |
| 비활성·선택 사항 | 낮은 대비 + dashed stroke |

## 화면 구성

1. 짧은 kicker와 결론형 제목
2. 필요한 경우 한 문장 설명
3. 넓은 SVG figure
4. 범례가 꼭 필요하면 figure 아래의 한 줄 strip
5. 입력에서 생략·통합한 내용이 있으면 짧은 note

그림 주변에 동일한 카드 세 개를 관성적으로 붙이지 않는다. shadow와 gradient는 정보 구조를
설명할 때가 아니면 쓰지 않는다. 기본 지면은 밝게 유지하고 dark theme은 사용자가 명시적으로
요청했을 때만 별도 token으로 만든다.
