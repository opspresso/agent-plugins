# 템플릿

아래 HTML을 그대로 복사해 내용만 채운다. 토큰, 목차 스크롤 추적, 표 정렬, 인쇄와
모션 축소 스타일이 이미 들어 있으니 이 배관을 다시 짜지 않는다. 값의 근거는 같은
디렉터리의 `design-system.md`에 있고, 색은 `document` MCP의 `executive` 프로파일과
같은 값이다.

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>리포트 제목</title>
<style>
:root {
  --bg: #FFFFFF; --surface-tint: #F5F7F8; --brand-tint: #EAF1F3; --rule: #CBD5DB;
  --ink: #18222B; --ink-muted: #4F5D68;
  --brand: #17324D; --brand-light: #2D6A78; --brand-deep: #0B5D7A; --on-brand: #FFFFFF;
  --positive: #147D64; --negative: #B8433F;
  --c1: #2A78D6; --c2: #EB6834; --c3: #1BAF7A; --c4: #EDA100;
  --c5: #E87BA4; --c6: #4A3AA7; --c7: #E34948; --c8: #898781;

  --font-sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-serif: Georgia, "Times New Roman", serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  --s-1: .25rem; --s-2: .5rem; --s-3: .75rem; --s-4: 1rem;
  --s-5: 1.5rem; --s-6: 2rem; --s-7: 3rem; --s-8: 4rem;
  --measure: 68ch; --wide: 1100px; --page: 1400px;
}

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--font-serif); font-size: 1.0625rem; line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, .kicker, .meta, .stat, figcaption, table, .toc, .sources { font-family: var(--font-sans); }
a { color: var(--brand-deep); text-underline-offset: .18em; text-decoration-thickness: 1px; }
code { font-family: var(--font-mono); font-size: .875em; color: var(--brand-deep); background: var(--brand-tint); padding: .1em .35em; border-radius: 2px; }
pre { background: var(--brand-tint); padding: var(--s-4); overflow-x: auto; font-size: .875rem; line-height: 1.35; }
pre code { background: none; padding: 0; color: inherit; }

/* 지면 ------------------------------------------------------------------ */
.page { max-width: var(--page); margin: 0 auto; padding: var(--s-7) var(--s-5) var(--s-8); }
.layout { display: block; }
.prose > * { max-width: var(--measure); }
.prose > .wide, .prose > figure, .prose > .stats { max-width: var(--wide); }

@media (min-width: 1024px) {
  .layout { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: var(--s-8); align-items: start; }
}

/* 제목 블록 -------------------------------------------------------------- */
header.title { max-width: var(--wide); margin-bottom: var(--s-8); background: var(--surface-tint); padding: var(--s-7) var(--s-6); }
.kicker { font-size: .75rem; line-height: 1.4; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-muted); margin: 0 0 var(--s-3); }
h1 { font-size: clamp(2rem, 5vw, 2.5rem); line-height: 1.15; color: var(--brand); margin: 0; }
h1::after { content: ""; display: block; width: 64px; height: 3px; background: var(--brand-light); margin-top: var(--s-4); }
.dek { font-size: 1.25rem; line-height: 1.4; color: var(--ink-muted); max-width: var(--measure); margin: var(--s-5) 0 0; }
.meta { font-size: .8125rem; color: var(--ink-muted); margin: var(--s-5) 0 0; }

/* 목차 ------------------------------------------------------------------- */
.toc { font-size: .8125rem; }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0 0 var(--s-2); }
.toc a { display: block; padding: .15rem 0 .15rem var(--s-3); color: var(--ink-muted); text-decoration: none; border-left: 2px solid var(--rule); }
.toc a:hover { color: var(--ink); }
.toc a[aria-current="true"] { color: var(--brand-deep); border-left-color: var(--brand-light); }
@media (min-width: 1024px) { .toc { position: sticky; top: var(--s-6); } }
@media (max-width: 1023px) { .toc { margin-bottom: var(--s-7); padding-bottom: var(--s-5); border-bottom: 1px solid var(--rule); } }

/* 본문 ------------------------------------------------------------------- */
h2 { font-size: 1.5rem; line-height: 1.2; color: var(--brand); margin: var(--s-8) 0 var(--s-3); padding-bottom: var(--s-2); border-bottom: 2px solid var(--brand-light); scroll-margin-top: var(--s-6); }
h3 { font-size: 1.125rem; line-height: 1.3; margin: var(--s-6) 0 var(--s-2); }
p { margin: 0 0 var(--s-4); }
.lead { font-size: 1.125rem; }
ul, ol { padding-left: 1.2em; margin: 0 0 var(--s-4); }
li { margin-bottom: var(--s-2); }
hr { border: 0; border-top: 1px solid var(--rule); margin: var(--s-7) 0; }

/* 핵심 수치 -------------------------------------------------------------- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--s-5); margin: var(--s-6) 0 var(--s-7); }
.stats > div { padding-left: var(--s-4); border-left: 1px solid var(--rule); }
.stats > div:first-child { padding-left: 0; border-left: 0; }
.stat { font-size: clamp(2rem, 4vw, 2.5rem); line-height: 1.1; color: var(--brand); font-variant-numeric: tabular-nums; }
.stat .unit { font-size: .5em; color: var(--ink-muted); margin-left: .15em; }
.stat-label { font-size: .8125rem; color: var(--ink-muted); margin-top: var(--s-2); }
.stat-note { font-size: .75rem; color: var(--ink-muted); margin-top: var(--s-1); }
.up { color: var(--positive); } .down { color: var(--negative); }

/* 그림 ------------------------------------------------------------------- */
figure { margin: var(--s-6) 0; }
figure svg { width: 100%; height: auto; display: block; font-family: var(--font-sans); }
figcaption { font-size: .8125rem; line-height: 1.5; color: var(--ink-muted); margin-top: var(--s-3); max-width: var(--measure); }

/* 표 — 가로 괘선만 ------------------------------------------------------- */
table { width: 100%; border-collapse: collapse; font-size: .9375rem; line-height: 1.35; margin: var(--s-5) 0; }
th, td { text-align: left; padding: var(--s-2) var(--s-3); }
thead th { background: var(--brand); color: var(--on-brand); font-size: .8125rem; font-weight: 600; }
tbody tr + tr td { border-top: 1px solid var(--rule); }
tbody tr:nth-child(odd) td { background: var(--brand-tint); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
th[data-sort] { cursor: pointer; user-select: none; }
th[aria-sort]::after { content: " ▾"; font-size: .75em; }
th[aria-sort="ascending"]::after { content: " ▴"; }

/* 콜아웃 ----------------------------------------------------------------- */
.callout { background: var(--brand-tint); border-left: 3px solid var(--brand-light); padding: var(--s-4) var(--s-5); margin: var(--s-6) 0; }
.callout > :last-child { margin-bottom: 0; }

/* 출처 ------------------------------------------------------------------- */
.sources { font-size: .8125rem; color: var(--ink-muted); }
.sources ol { padding-left: 1.4em; }
sup a { color: var(--brand-light); text-decoration: none; padding: 0 .1em; }

/* 등장 ------------------------------------------------------------------- */
.reveal { opacity: 0; transform: translateY(8px); transition: opacity .4s ease, transform .4s ease; }
.reveal.shown { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .reveal, .reveal.shown { opacity: 1; transform: none; transition: none; }
}

/* 인쇄 ------------------------------------------------------------------- */
@media print {
  .toc, .no-print { display: none; }
  body { font-size: 10.5pt; }
  .layout { display: block; }
  header.title { background: none; padding: 0; }
  h2, h3, figure, table, .callout { break-inside: avoid; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 8pt; color: #555; }
}
</style>
</head>
<body>
<div class="page">
  <header class="title">
    <p class="kicker">분류 · 기간</p>
    <h1>결론을 담은 제목</h1>
    <p class="dek">이 리포트가 무엇을 보고 무엇을 알아냈는지 한 문장으로.</p>
    <p class="meta">2026-08-21 · 작성자 · 데이터 기준일</p>
  </header>

  <div class="layout">
    <nav class="toc" aria-label="목차">
      <ol>
        <li><a href="#summary">요약</a></li>
        <li><a href="#finding-1">첫 번째 발견</a></li>
        <li><a href="#finding-2">두 번째 발견</a></li>
        <li><a href="#method">방법과 한계</a></li>
        <li><a href="#sources">출처</a></li>
      </ol>
    </nav>

    <main class="prose">
      <section id="summary">
        <h2>요약</h2>
        <p class="lead">결론부터 두세 문장. 무엇이 얼마나 바뀌었고 그래서 무엇을 해야 하는지.</p>

        <div class="stats">
          <div>
            <div class="stat">15.1<span class="unit">%</span></div>
            <div class="stat-label">재방문율</div>
            <div class="stat-note"><span class="up">+2.7%p</span> 지난 분기 대비</div>
          </div>
          <div>
            <div class="stat">4.2<span class="unit">일</span></div>
            <div class="stat-label">평균 재방문 간격</div>
            <div class="stat-note">변화 없음</div>
          </div>
          <div>
            <div class="stat">31.8<span class="unit">만</span></div>
            <div class="stat-label">분석 대상 사용자</div>
            <div class="stat-note">2026-05-01 ~ 07-31</div>
          </div>
        </div>
      </section>

      <section id="finding-1">
        <h2>첫 번째 발견</h2>
        <p>결론을 먼저 쓰고, 그 근거를 이어서 쓴다. 수치는 문장 안에 넣어 무엇과 비교한 값인지 드러낸다.</p>

        <figure class="reveal">
          <svg viewBox="0 0 640 260" role="img" aria-labelledby="chart1-title">
            <title id="chart1-title">3월 이후 재방문율이 12.4%에서 15.1%로 올랐다</title>
            <g style="stroke: var(--rule)" stroke-width="1">
              <line x1="48" y1="40" x2="600" y2="40"/>
              <line x1="48" y1="100" x2="600" y2="100"/>
              <line x1="48" y1="160" x2="600" y2="160"/>
              <line x1="48" y1="220" x2="600" y2="220"/>
            </g>
            <g style="fill: var(--ink-muted)" font-size="11" text-anchor="end">
              <text x="40" y="44">18%</text>
              <text x="40" y="104">15%</text>
              <text x="40" y="164">12%</text>
              <text x="40" y="224">9%</text>
            </g>
            <g style="fill: var(--ink-muted)" font-size="11" text-anchor="middle">
              <text x="80" y="242">3월</text>
              <text x="220" y="242">4월</text>
              <text x="360" y="242">5월</text>
              <text x="500" y="242">6월</text>
            </g>
            <path d="M80 152 L220 138 L360 118 L500 100" style="fill: none; stroke: var(--c1)" stroke-width="2"/>
            <circle cx="500" cy="100" r="3.5" style="fill: var(--c1)"/>
            <text x="512" y="104" style="fill: var(--c1)" font-size="12">15.1%</text>
          </svg>
          <figcaption>월별 재방문율. 2026-03-01 ~ 06-30, 가입 30일 이상 사용자 31.8만 명 기준. 출처<sup><a href="#s1" id="s1-ref">1</a></sup></figcaption>
        </figure>

        <div class="callout">
          <p>본문에서 빼도 되는 보충 설명이나 주의 사항. 한 절에 하나까지.</p>
        </div>
      </section>

      <section id="finding-2">
        <h2>두 번째 발견</h2>
        <table>
          <thead>
            <tr>
              <th data-sort="text">구간</th>
              <th class="num" data-sort="num">사용자</th>
              <th class="num" data-sort="num">재방문율</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>신규</td><td class="num">124,300</td><td class="num">9.4%</td></tr>
            <tr><td>일반</td><td class="num">158,200</td><td class="num">15.8%</td></tr>
            <tr><td>헤비</td><td class="num">35,500</td><td class="num">28.1%</td></tr>
          </tbody>
        </table>
      </section>

      <section id="method">
        <h2>방법과 한계</h2>
        <p>어떤 데이터를 어떻게 집계했는지, 무엇을 보지 못했는지 적는다. 못 본 것을 적지 않으면 독자가 결론을 실제보다 넓게 읽는다.</p>
      </section>

      <section id="sources" class="sources">
        <h2>출처</h2>
        <ol>
          <li id="s1">데이터 출처와 집계 쿼리 위치. <a href="#s1-ref">본문으로</a></li>
        </ol>
      </section>
    </main>
  </div>
</div>

<script>
// 목차 스크롤 추적. 실패해도 링크는 그대로 동작한다.
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var sections = links
    .map(function (a) { return document.querySelector(a.getAttribute('href')); })
    .filter(Boolean);
  if (!sections.length || !('IntersectionObserver' in window)) return;

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      links.forEach(function (a) {
        a.setAttribute('aria-current', a.getAttribute('href') === '#' + entry.target.id ? 'true' : 'false');
      });
    });
  }, { rootMargin: '-10% 0px -70% 0px' });
  sections.forEach(function (section) { observer.observe(section); });
})();

// 스크롤 등장. 모션 축소 설정이면 그냥 보여 준다.
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('shown'); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('shown');
      observer.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -10% 0px' });
  items.forEach(function (el) { observer.observe(el); });
})();

// 표 정렬. 행이 스무 개를 넘을 때만 헤더에 data-sort 를 남긴다.
(function () {
  document.querySelectorAll('th[data-sort]').forEach(function (th) {
    th.setAttribute('tabindex', '0');
    function sort() {
      var table = th.closest('table');
      var body = table.tBodies[0];
      var index = Array.prototype.indexOf.call(th.parentNode.children, th);
      var numeric = th.dataset.sort === 'num';
      var asc = th.getAttribute('aria-sort') !== 'ascending';
      var rows = Array.prototype.slice.call(body.rows);
      rows.sort(function (a, b) {
        var x = a.cells[index].textContent.trim();
        var y = b.cells[index].textContent.trim();
        if (numeric) {
          x = parseFloat(x.replace(/[^0-9.-]/g, '')) || 0;
          y = parseFloat(y.replace(/[^0-9.-]/g, '')) || 0;
          return asc ? x - y : y - x;
        }
        return asc ? x.localeCompare(y, 'ko') : y.localeCompare(x, 'ko');
      });
      rows.forEach(function (row) { body.appendChild(row); });
      table.querySelectorAll('th').forEach(function (other) { other.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
    }
    th.addEventListener('click', sort);
    th.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); sort(); }
    });
  });
})();
</script>
</body>
</html>
```
