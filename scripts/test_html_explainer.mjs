import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const template = readFileSync(new URL('../plugins/design/skills/html-explainer/references/template.md', import.meta.url), 'utf8');
const script = template.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script);

function explainer() {
  const events = new Map();
  function control() {
    const callbacks = new Map();
    return {
      addEventListener: (name, callback) => callbacks.set(name, callback),
      fire: (name) => callbacks.get(name)(),
    };
  }
  let focused = null;
  const steps = ['First', 'Second', 'Third'].map((title, index) => ({
    dataset: { title }, hidden: false, focus() { focused = index; },
  }));
  const progress = { textContent: '' };
  const prev = control();
  const next = control();
  const reset = control();
  const range = { ...control(), id: 'value', value: '1', dataset: { initial: '1' } };
  const output = { textContent: '' };
  const selectors = new Map([
    ['.progress', progress], ['[data-move="-1"]', prev], ['[data-move="1"]', next], ['.reset', reset],
  ]);
  runInNewContext(script, {
    document: {
      querySelector: (selector) => selectors.get(selector),
      querySelectorAll: (selector) => selector === '.step' ? steps : selector === 'input[type="range"]' ? [range] : [],
      getElementById: () => output,
      addEventListener: (name, callback) => events.set(name, callback),
    },
  });
  return {
    prev, next, reset, range, output,
    state: () => ({ visible: steps.map((step, index) => step.hidden ? null : index).filter((index) => index !== null), focused, progress: progress.textContent }),
    key(key, { input = false, ...flags } = {}) {
      const event = { key, defaultPrevented: false, target: { closest: () => input ? range : null }, preventDefault() { this.defaultPrevented = true; }, ...flags };
      events.get('keydown')(event);
      return event.defaultPrevented;
    },
  };
}

test('step navigation is bounded and reset restores focus and slider output', () => {
  const page = explainer();
  assert.equal(page.prev.disabled, true);
  assert.equal(page.next.disabled, false);
  page.range.value = '6';
  page.range.fire('input');
  assert.equal(page.output.textContent, '6');
  page.next.fire('click');
  page.next.fire('click');
  page.next.fire('click');
  assert.deepEqual(page.state(), { visible: [2], focused: 2, progress: '3 / 3 · Third' });
  assert.equal(page.next.disabled, true);
  page.reset.fire('click');
  assert.deepEqual(page.state(), { visible: [0], focused: 0, progress: '1 / 3 · First' });
  assert.equal(page.range.value, '1');
  assert.equal(page.output.textContent, '1');
});

test('handled arrows prevent scrolling and preserve native input and browser shortcuts', () => {
  const page = explainer();
  assert.equal(page.key('ArrowRight'), true);
  assert.deepEqual(page.state().visible, [1]);
  for (const flags of [{ input: true }, { altKey: true }, { ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { defaultPrevented: true }]) {
    page.key('ArrowLeft', flags);
    assert.deepEqual(page.state().visible, [1]);
  }
  assert.equal(page.key('ArrowLeft'), true);
  assert.deepEqual(page.state().visible, [0]);
  assert.equal(page.key('Escape'), false);
});
