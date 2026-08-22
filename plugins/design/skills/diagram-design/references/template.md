# HTML 템플릿

단독 다이어그램은 아래 골격에서 시작한다. 제목, 설명, `viewBox`, SVG id와 실제 node를
내용에 맞게 바꾼다. 사용하지 않는 예시 요소는 남겨 두지 않는다.

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>처리 경계와 주요 흐름</title>
<style>
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
  --font-sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
}
main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 48px 24px 64px;
}
.kicker {
  margin: 0 0 8px;
  color: var(--ink-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  color: var(--brand);
  font-size: clamp(28px, 5vw, 40px);
  line-height: 1.15;
}
.dek {
  max-width: 68ch;
  margin: 16px 0 32px;
  color: var(--ink-muted);
  font-size: 16px;
  line-height: 1.5;
}
.diagram-frame {
  overflow-x: auto;
  border-top: 2px solid var(--brand-light);
  border-bottom: 1px solid var(--rule);
  padding: 24px 0;
}
.diagram-frame svg {
  display: block;
  width: 100%;
  min-width: 720px;
  height: auto;
}
.note {
  margin: 16px 0 0;
  color: var(--ink-muted);
  font-size: 13px;
  line-height: 1.5;
}
@media (max-width: 760px) {
  main { padding: 32px 16px 48px; }
  .diagram-frame svg { width: 900px; }
}
@media print {
  main { max-width: none; padding: 0; }
  .diagram-frame { overflow: visible; }
  .diagram-frame svg { min-width: 0; max-width: 100%; }
}
</style>
</head>
<body>
<main>
  <p class="kicker">SYSTEM VIEW</p>
  <h1>요청은 검증과 처리를 거쳐 저장된다</h1>
  <p class="dek">외부 요청이 신뢰 경계를 통과해 처리되고 상태를 남기는 핵심 경로다.</p>

  <figure>
    <div class="diagram-frame">
      <svg viewBox="0 0 960 520" role="img"
           aria-labelledby="request-path-title request-path-desc">
        <title id="request-path-title">요청 처리의 핵심 경로</title>
        <desc id="request-path-desc">외부 요청이 진입점, 처리 서비스, 저장소 순서로 이동한다</desc>
        <defs>
          <marker id="request-path-arrow" viewBox="0 0 10 10" refX="9" refY="5"
                  markerWidth="7" markerHeight="7" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink-muted)"/>
          </marker>
        </defs>

        <rect x="280" y="72" width="600" height="360" rx="8"
              fill="var(--surface)" stroke="var(--rule)" stroke-dasharray="6 5"/>
        <text x="304" y="104" fill="var(--ink-muted)" font-size="12" font-weight="700">
          TRUSTED ZONE
        </text>

        <path d="M 216 252 H 352" fill="none" stroke="var(--ink-muted)"
              stroke-width="1.5" marker-end="url(#request-path-arrow)"/>
        <path d="M 544 252 H 672" fill="none" stroke="var(--ink-muted)"
              stroke-width="1.5" marker-end="url(#request-path-arrow)"/>

        <rect x="248" y="224" width="72" height="20" rx="3" fill="var(--bg)"/>
        <text x="284" y="238" text-anchor="middle" fill="var(--ink-muted)"
              font-size="10" font-family="var(--font-mono)">HTTPS</text>
        <rect x="580" y="224" width="56" height="20" rx="3" fill="var(--surface)"/>
        <text x="608" y="238" text-anchor="middle" fill="var(--ink-muted)"
              font-size="10" font-family="var(--font-mono)">WRITE</text>

        <g>
          <rect x="48" y="204" width="168" height="96" rx="6"
                fill="var(--bg)" stroke="var(--ink-muted)" stroke-dasharray="5 4"/>
          <text x="64" y="240" fill="var(--ink)" font-size="14" font-weight="600">외부 요청</text>
          <text x="64" y="264" fill="var(--ink-muted)" font-size="11">인증 정보와 payload</text>
        </g>
        <g>
          <rect x="352" y="204" width="192" height="96" rx="6"
                fill="var(--surface-strong)" stroke="var(--brand-light)"/>
          <text x="368" y="240" fill="var(--brand)" font-size="14" font-weight="600">처리 서비스</text>
          <text x="368" y="264" fill="var(--ink-muted)" font-size="11">검증과 업무 규칙 수행</text>
        </g>
        <g>
          <rect x="672" y="204" width="160" height="96" rx="6"
                fill="var(--bg)" stroke="var(--ink)"/>
          <text x="688" y="240" fill="var(--ink)" font-size="14" font-weight="600">상태 저장소</text>
          <text x="688" y="264" fill="var(--brand-deep)" font-size="11"
                font-family="var(--font-mono)">transaction state</text>
        </g>
      </svg>
    </div>
    <figcaption class="note">신뢰 경계와 주요 데이터 이동만 보인 overview다.</figcaption>
  </figure>
</main>
</body>
</html>
```

## 바꾸는 순서

1. 제목과 `<title>`·`<desc>`를 실제 결론으로 바꾼다.
2. 선택한 유형의 content model에 맞게 zone, node, connector를 다시 구성한다.
3. diagram slug를 정하고 SVG 내부 id에 같은 prefix를 사용한다.
4. `viewBox`를 요소 수와 사용 위치에 맞춘다.
5. 사용하지 않는 CSS와 예시 요소를 제거한다.
6. `svg-implementation.md`의 육안 검사를 수행한다.
