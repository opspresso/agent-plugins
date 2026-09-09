# 템플릿

아래 HTML을 복사해 단계와 그림만 채운다. 단계 전환, 키보드, 진행 알림, 초기화, 모션
축소, 인쇄 배관이 이미 들어 있으니 다시 짜지 않는다. 장치를 더 붙일 때는 같은
디렉터리의 `interaction-patterns.md`를 본다.

제목과 단계·그림을 채운 뒤 필요한 컨트롤만 남긴다. 슬라이더의 `draw`에 값과 SVG를
연결하는 코드를 작성한다. 추가한 조작도 초기화에 포함하고 `id`·`for`를 고유하게 맞춘다.

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>무엇을 설명하는지</title>
<style>
:root {
  color-scheme: light dark;
  --bg:      light-dark(#FCFCFB, #14171A);
  --ink:     light-dark(#1B2126, #E8ECEF);
  --ink-dim: light-dark(#5C666E, #A3ADB5);
  --rule:    light-dark(#DFE3E6, #2C3238);
  --quiet:   light-dark(#EFF2F4, #1E2429);
  --accent:  light-dark(#1F6FEB, #6FA8FF);

  --font: system-ui, -apple-system, "Segoe UI", sans-serif;
  --s-2: .5rem; --s-3: .75rem; --s-4: 1rem; --s-5: 1.5rem; --s-6: 2rem; --s-7: 3rem;
  --stage: 760px;
}

*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--font); line-height: 1.5; -webkit-font-smoothing: antialiased;
}
.page { max-width: var(--stage); margin: 0 auto; padding: var(--s-6) var(--s-4) var(--s-7); }

/* 들머리 — 여기까지가 글자다 -------------------------------------------- */
.intro { margin-bottom: var(--s-6); }
.kicker { margin: 0 0 var(--s-2); font-size: .75rem; letter-spacing: .12em;
          text-transform: uppercase; color: var(--ink-dim); }
h1 { margin: 0 0 var(--s-3); font-size: clamp(1.6rem, 5vw, 2.2rem); line-height: 1.2;
     text-wrap: balance; }
.intro p { margin: 0; max-width: 32em; color: var(--ink-dim); font-size: 1.0625rem; }

/* 단계 ------------------------------------------------------------------ */
.steps { list-style: none; margin: 0; padding: 0; }
.step:focus { outline: 2px solid var(--accent); outline-offset: var(--s-3); }

/* 무대 — 그림이 주인공이다. 좁아져도 그림을 먼저 지킨다 */
.stage { position: relative; margin: 0 0 var(--s-5); }
.stage svg { display: block; width: 100%; height: auto; }
.stage figcaption { margin-top: var(--s-3); font-size: .875rem; color: var(--ink-dim); }

/* 설명 — 두 문장을 넘기지 않는다 */
.say { margin: 0 0 var(--s-5); max-width: 26em; font-size: 1.125rem; }
.term { font-weight: 600; }

/* 조작 */
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s-3);
            padding: var(--s-3) 0; border-top: 1px solid var(--rule); }
.controls label { font-size: .9375rem; color: var(--ink-dim); }
output { font-variant-numeric: tabular-nums; font-weight: 600; }

/* 그림 위 조작 대상 */
.hotspot { position: absolute; transform: translate(-50%, -50%);
           min-width: 44px; min-height: 44px; padding: var(--s-2) var(--s-3);
           font: inherit; font-size: .8125rem; color: var(--ink);
           background: var(--bg); border: 1px solid var(--rule); border-radius: 999px;
           cursor: pointer; }
.hotspot[aria-pressed="true"] { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
.stage svg .dimmed { opacity: .25; }

/* 단계 이동 ------------------------------------------------------------- */
.stepper { position: sticky; bottom: 0; display: flex; align-items: center;
           gap: var(--s-4); margin-top: var(--s-6); padding: var(--s-3) var(--s-4);
           background: var(--quiet); border-top: 1px solid var(--rule); }
.progress { flex: 1; margin: 0; font-size: .9375rem; color: var(--ink-dim);
            font-variant-numeric: tabular-nums; }
button { font: inherit; padding: var(--s-2) var(--s-4); color: var(--ink);
         background: var(--bg); border: 1px solid var(--rule); border-radius: 6px;
         cursor: pointer; }
button:disabled { opacity: .4; cursor: default; }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.reset { margin-left: auto; border: none; background: none; color: var(--ink-dim);
         text-decoration: underline; text-underline-offset: .2em; }

/* 모션 — 끄는 게 아니라 최종 상태를 즉시 보여 준다 ---------------------- */
.movable { transition: transform 260ms ease; }
@media (prefers-reduced-motion: reduce) { .movable { transition: none; } }

/* 인쇄 — 만지지 않고도 전체를 볼 수 있는 경로 --------------------------- */
@media print {
  :root { color-scheme: light; }
  .stepper, .controls, .hotspot { display: none; }
  .step[hidden] { display: block !important; }
  .stage svg .dimmed { opacity: 1; }
  .step { break-inside: avoid; margin-bottom: var(--s-6); }
}
</style>
</head>
<body>
<main class="page">

  <header class="intro">
    <p class="kicker">머리말</p>
    <h1>무엇을 설명하는지 한 문장으로</h1>
    <p>독자가 이미 아는 것에서 출발하는 한 줄. 여기까지가 글자다.</p>
  </header>

  <ol class="steps">
    <li class="step" tabindex="-1" data-title="이 단계에서 알게 되는 것">
      <figure class="stage">
        <svg viewBox="0 0 720 400" role="img" aria-labelledby="t1 d1">
          <title id="t1">이 그림이 말하는 결론</title>
          <desc id="d1">그림에 무엇이 어떻게 놓여 있는지 한두 문장.</desc>
          <!-- 그림. 라벨은 <text>로 그림 안에 직접 붙인다 -->
        </svg>
        <figcaption>그림이 스스로 말하지 못하는 것만 적는다.</figcaption>
      </figure>

      <p class="say">알게 되는 것 한 문장. 필요하면 한 문장 더.</p>

      <div class="controls">
        <label for="v1">값 이름</label>
        <input type="range" id="v1" min="1" max="6" step="1" value="1" data-initial="1">
        <output for="v1" id="v1-out">1</output>
      </div>
    </li>

    <li class="step" tabindex="-1" data-title="다음 단계에서 알게 되는 것">
      <figure class="stage">
        <svg viewBox="0 0 720 400" role="img" aria-labelledby="t2 d2">
          <title id="t2">두 번째 그림의 결론</title>
          <desc id="d2">무엇이 달라졌는지.</desc>
        </svg>
      </figure>
      <p class="say">앞 단계에서 무엇이 달라졌는지.</p>
    </li>
  </ol>

  <nav class="stepper" aria-label="설명 단계">
    <button type="button" data-move="-1">이전</button>
    <p class="progress" role="status"></p>
    <button type="button" data-move="1">다음</button>
    <button type="button" class="reset">처음으로</button>
  </nav>

</main>

<script>
(function () {
  var steps = Array.prototype.slice.call(document.querySelectorAll('.step'));
  var progress = document.querySelector('.progress');
  var prev = document.querySelector('[data-move="-1"]');
  var next = document.querySelector('[data-move="1"]');
  var at = 0;

  function show(index, moveFocus) {
    at = Math.max(0, Math.min(steps.length - 1, index));
    steps.forEach(function (step, i) { step.hidden = i !== at; });
    prev.disabled = at === 0;
    next.disabled = at === steps.length - 1;
    progress.textContent = (at + 1) + ' / ' + steps.length + ' · ' + steps[at].dataset.title;
    if (moveFocus) { steps[at].focus(); }
  }

  prev.addEventListener('click', function () { show(at - 1, true); });
  next.addEventListener('click', function () { show(at + 1, true); });

  document.addEventListener('keydown', function (event) {
    if (event.target.closest('input, textarea, select')) { return; }
    if (event.key === 'ArrowRight') { show(at + 1, true); }
    if (event.key === 'ArrowLeft') { show(at - 1, true); }
  });

  // 슬라이더 — 값이 바뀌면 그림이 즉시 반응한다
  document.querySelectorAll('input[type="range"]').forEach(function (range) {
    var out = document.getElementById(range.id + '-out');
    function draw() {
      if (out) { out.textContent = range.value; }
      // 여기서 SVG 요소의 속성을 바꾼다. 노드를 새로 만들지 않는다
    }
    range.addEventListener('input', draw);
    range._draw = draw;
    draw();
  });

  // 그림 위 조작 대상
  document.querySelectorAll('.hotspot').forEach(function (spot) {
    spot.addEventListener('click', function () {
      var on = spot.getAttribute('aria-pressed') === 'true';
      var stage = spot.closest('.stage');
      stage.querySelectorAll('.hotspot').forEach(function (other) {
        other.setAttribute('aria-pressed', 'false');
      });
      spot.setAttribute('aria-pressed', on ? 'false' : 'true');
      stage.querySelectorAll('svg [data-part]').forEach(function (part) {
        part.classList.toggle('dimmed', !on && part.dataset.part !== spot.dataset.part);
      });
    });
  });

  // 되돌리기 — 조작은 언제나 원위치할 수 있어야 한다
  document.querySelector('.reset').addEventListener('click', function () {
    document.querySelectorAll('input[type="range"]').forEach(function (range) {
      range.value = range.dataset.initial;
      if (range._draw) { range._draw(); }
    });
    document.querySelectorAll('.hotspot').forEach(function (spot) {
      spot.setAttribute('aria-pressed', 'false');
    });
    document.querySelectorAll('.stage svg .dimmed').forEach(function (part) {
      part.classList.remove('dimmed');
    });
    show(0, true);
  });

  show(0, false);   // 여기서 처음으로 hidden 이 걸린다. 스크립트가 없으면 전부 보인다
})();
</script>
</body>
</html>
```

## 바꾸는 순서

1. `lang`·버튼·접근성 라벨을 문서 언어에 맞추고 `<title>`과 들머리를 채운다.
2. `설명 계단` 표의 행 수만큼 `<li class="step">`을 복제하고 `data-title`에 그 단계에서
   알게 되는 것을 적는다. 진행 표시가 이 값을 읽는다.
3. 단계마다 `<svg>`를 그린다. `<title>`은 주제가 아니라 **그 그림의 결론**을 쓰고
   `id`가 겹치지 않게 한다.
4. `.say`는 두 문장 안팎에서 시작하고 언어·내용에 맞게 조정한다. 과밀하면 단계를 나눈다.
5. 필요한 단계에만 `.controls`를 남긴다. 쓰지 않는 슬라이더 블록은 지운다.
6. 그림 위 조작이 없으면 `.hotspot` 관련 CSS와 스크립트를 지운다.
7. 조작 대상은 `data-part`가 있는 SVG 그룹으로 묶고 각 버튼 값과 일치시킨다.
   추가한 토글·선택 문제의 상태도 초기화 함수에서 복원한다.
8. 처음·마지막 단계, 키보드 조작, 입력 최솟값·최댓값, 초기화와 인쇄를 확인한다.
