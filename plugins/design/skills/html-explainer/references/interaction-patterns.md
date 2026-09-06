# 만져서 알게 하는 장치

`SKILL.md`의 장치 표에 나온 다섯 가지의 최소 구현이다. 항목마다 **언제 쓰나 / 지킬 것 /
최소 형태**를 담았다. 골라 쓰고, 필요 없는 배관을 덧붙이지 않는다.

공통 전제가 하나 있다. **단계와 상태를 JavaScript로 만들지 않는다.** 마크업에 전부
두고 보이기만 토글한다. 그래야 스크립트가 죽어도, 인쇄해도, 화면 낭독기로도 내용이
남는다. 그래서 아래 예시의 `hidden`은 **마크업이 아니라 초기화 코드가 건다.**

## 1. 단계 이동

**언제** — 순서대로 일어나는 일을 설명할 때. 이 지면의 기본 골격이다.

**지킬 것**

- 자동으로 넘어가지 않는다. 다음·이전은 독자가 누른다.
- 진행 위치와 현재 단계 제목을 글자로 보여 주고 `role="status"`로 알린다.
- 단계가 바뀌면 새 단계로 focus를 옮긴다. 받을 요소에 `tabindex="-1"`을 둔다.
- 화살표 키를 받되 입력 요소 안에서는 가로채지 않는다.

```html
<ol class="steps">
  <li class="step" tabindex="-1" data-title="요청은 한 번에 한 대에만 간다">…</li>
  <li class="step" tabindex="-1" data-title="대가 늘면 화살표를 나눠야 한다">…</li>
</ol>

<nav class="stepper" aria-label="설명 단계">
  <button type="button" data-move="-1">이전</button>
  <p class="progress" role="status"></p>
  <button type="button" data-move="1">다음</button>
</nav>
```

```js
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

  show(0, false);   // 여기서 처음으로 hidden 이 걸린다. 스크립트가 없으면 전부 보인다
})();
```

인쇄에서는 전 단계를 되살린다.

```css
@media print {
  .stepper { display: none; }
  .step[hidden] { display: list-item !important; }
}
```

## 2. 슬라이더와 그림

**언제** — 값이 바뀌면 결과가 어떻게 바뀌는지 보여줄 때. 이 지면에서 가장 강한 장치다.

**지킬 것**

- 네이티브 `<input type="range">`를 쓴다. 직접 만든 드래그 막대는 키보드에서 죽는다.
- **현재 값을 글자로도 보여 준다.** `<output>`은 값이 바뀌면 스스로 알린다.
- 움직이는 즉시 반응한다. `input` 이벤트를 쓰고 `change`를 기다리지 않는다.
- 범위 양 끝이 의미 있는 값이어야 한다. 극단에서 그림이 깨지면 범위가 잘못된 것이다.

```html
<label for="servers">서버 수</label>
<input type="range" id="servers" min="1" max="6" step="1" value="1">
<output for="servers" id="servers-out">1대</output>
```

```js
var range = document.getElementById('servers');
var out = document.getElementById('servers-out');

function draw() {
  var n = Number(range.value);
  out.textContent = n + '대';
  document.querySelectorAll('.server').forEach(function (node, i) {
    node.setAttribute('opacity', i < n ? '1' : '0.12');
  });
}
range.addEventListener('input', draw);
draw();
```

SVG 안의 요소는 개수를 미리 그려 두고 보이기만 바꾼다. 값에 맞춰 노드를 만들면 앞의
전제를 어기게 된다.

## 3. 토글과 나란히 비교

**언제** — 두 경우의 차이가 요점일 때.

**지킬 것**

- 두 경우를 같은 크기, 같은 자리, 같은 축척으로 둔다. 크기가 다르면 그 차이가 먼저 읽힌다.
- 선택은 라디오 그룹으로 만들고 선택 값에 맞는 패널을 표시한다.
- 무엇이 켜져 있는지 색 말고 글자로도 보인다.

```html
<div class="comparison">
<fieldset class="switch">
  <legend>비교</legend>
  <input type="radio" id="before" name="case" value="before" checked>
  <label for="before">한 대일 때</label>
  <input type="radio" id="after" name="case" value="after">
  <label for="after">세 대일 때</label>
</fieldset>

<div class="pane" data-case="before">…</div>
<div class="pane" data-case="after">…</div>
</div>
```

```js
document.querySelectorAll('.comparison').forEach(function (comparison) {
  function showCase() {
    var selected = comparison.querySelector('input[type="radio"]:checked');
    comparison.querySelectorAll('.pane').forEach(function (pane) {
      pane.hidden = pane.dataset.case !== selected.value;
    });
  }
  comparison.addEventListener('change', showCase);
  showCase();
});
```

스크립트가 없으면 두 패널이 모두 보인다. 인쇄에도 두 경우를 남긴다.

```css
@media print { .comparison .pane[hidden] { display: block !important; } }
```

## 4. 그림 위 hotspot

**언제** — 부분과 전체의 관계를 보여줄 때. 큰 그림 하나를 여러 번 쓰게 해 준다.

**지킬 것**

- 겹치는 조작 대상은 HTML `<button>`으로 만들고 `position: absolute`로 얹는다. SVG
  도형에 클릭 핸들러만 붙이면 키보드에서 닿지 않는다.
- 눌린 상태를 `aria-pressed`로 알리고 focus 링을 지우지 않는다.
- 강조는 **나머지를 물러나게 하는 방식**으로 한다. 고른 것만 밝히면 지면이 깜빡인다.
- 터치 대상은 44px 이상으로 둔다.

```html
<div class="figure">
  <svg viewBox="0 0 480 260" role="img" aria-labelledby="fig-t fig-d">
    <title id="fig-t">요청이 갈림길을 지나 서버 세 대로 나뉜다</title>
    <desc id="fig-d">왼쪽에서 들어온 화살표가 가운데 갈림길에서 셋으로 갈라진다.</desc>
    …
  </svg>
  <button type="button" class="hotspot" style="left:42%;top:38%"
          aria-pressed="false" data-part="router">갈림길</button>
</div>
```

```js
document.querySelectorAll('.hotspot').forEach(function (spot) {
  spot.addEventListener('click', function () {
    var on = spot.getAttribute('aria-pressed') === 'true';
    var figure = spot.closest('.figure');
    figure.querySelectorAll('.hotspot').forEach(function (other) {
      other.setAttribute('aria-pressed', 'false');
    });
    spot.setAttribute('aria-pressed', on ? 'false' : 'true');
    figure.querySelectorAll('svg [data-part]').forEach(function (part) {
      part.classList.toggle('dimmed', !on && part.dataset.part !== spot.dataset.part);
    });
  });
});
```

```css
.figure svg .dimmed { opacity: .25; }
```

각 비교 대상은 `<g data-part="router">`처럼 묶는다. 라벨을 해당 그룹에 넣고,
다른 대상을 감싸는 상위 그룹에는 `data-part`를 중복 지정하지 않는다.

## 5. 직접 해보기

**언제** — 왜 그렇게 되는지를 말로 설명하기 어려울 때. 독자가 **틀릴 수 있는** 선택을
하고 결과를 본다.

**지킬 것**

- 맞혀야 다음으로 넘어가는 게 아니다. **틀려도 진행된다.** 틀린 선택의 결과를 보는 것이
  이 장치의 목적이다.
- 정답을 채점하지 말고 결과를 보여 준다. "틀렸습니다" 대신 화면에서 무슨 일이 일어나는지.
- 결과 영역을 `role="status"`로 두어 바뀐 내용이 전달되게 한다.
- 다시 고를 수 있어야 한다.

```html
<p>서버 한 대가 멈추면 요청은 어디로 갈까?</p>
<button type="button" data-pick="drop">사라진다</button>
<button type="button" data-pick="spread">남은 대가 나눠 받는다</button>
<p class="result" role="status"></p>
```

두 선택 모두 그림을 바꾸고, 어느 쪽이든 다음 단계로 갈 수 있게 둔다.

## 6. 초기화와 모션 축소

되돌릴 수 없는 조작은 만지지 않게 된다. 초기화는 장치가 아니라 **전제**다.

```html
<button type="button" class="reset">처음으로</button>
```

초기화는 단계·슬라이더·hotspot의 초깃값을 다시 그리는 함수 하나를 부른다. 각 장치가
자기 초깃값을 아는 형태로 짜 두면 이 함수가 짧아진다.

모션은 CSS에서 끊는다. **`transition`만 없애고 최종 상태는 그대로 둔다.**

```css
.movable { transition: transform 260ms ease; }

@media (prefers-reduced-motion: reduce) {
  .movable { transition: none; }
}
```

이 형태여야 모션을 끈 독자도 같은 것을 알게 된다. 클래스 토글 자체를 막으면 그 단계의
설명이 통째로 사라진다.
