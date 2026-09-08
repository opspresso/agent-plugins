import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const template = readFileSync(new URL('../plugins/design/skills/html-report/references/template.md', import.meta.url), 'utf8');
const start = template.indexOf('// 표 정렬.');
assert.notEqual(start, -1);
const script = template.slice(start, template.indexOf('</script>', start));

function sortable(values) {
  const attributes = new Map();
  const events = new Map();
  const body = {
    rows: values.map(([text, value]) => ({
      cells: [{ textContent: text, getAttribute: () => value ?? null }],
    })),
    appendChild(row) {
      this.rows.splice(this.rows.indexOf(row), 1);
      this.rows.push(row);
    },
  };
  const table = { tBodies: [body], querySelectorAll: () => [header] };
  const header = {
    dataset: { sort: 'num' },
    setAttribute: (name, value) => attributes.set(name, value),
    getAttribute: (name) => attributes.get(name) ?? null,
    removeAttribute: (name) => attributes.delete(name),
    addEventListener: (name, callback) => events.set(name, callback),
    closest: () => table,
  };
  header.parentNode = { children: [header] };
  runInNewContext(script, { document: { querySelectorAll: () => [header] } });
  return {
    click: () => events.get('click')(),
    key: (key) => events.get('keydown')({ key, preventDefault() {} }),
    values: () => body.rows.map((row) => row.cells[0].textContent),
    order: () => attributes.get('aria-sort'),
  };
}

test('numeric sort preserves zero, signed values and missing values in both directions', () => {
  const table = sortable(['—', '0', '−3', '2', '-10', 'N/A', ''].map((value) => [value]));
  table.click();
  assert.deepEqual(table.values(), ['-10', '−3', '0', '2', '—', 'N/A', '']);
  assert.equal(table.order(), 'ascending');
  table.key('Enter');
  assert.deepEqual(table.values(), ['2', '0', '−3', '-10', '—', 'N/A', '']);
  assert.equal(table.order(), 'descending');
});

test('commas, currency and percentages retain their displayed numeric magnitude', () => {
  // These are parser fixtures; a real column uses one unit consistently.
  const table = sortable(['₩1,000', '$2,000.50', '12.4%', '0%', '−2.5%', '€30', '£40', '¥50', '-$5', '$−4'].map((value) => [value]));
  table.click();
  assert.deepEqual(table.values(), ['-$5', '$−4', '−2.5%', '0%', '12.4%', '€30', '£40', '¥50', '₩1,000', '$2,000.50']);
  table.click();
  assert.deepEqual(table.values(), ['$2,000.50', '₩1,000', '¥50', '£40', '€30', '12.4%', '0%', '−2.5%', '$−4', '-$5']);
});

test('unsupported or malformed display values are not guessed; explicit keys are honored', () => {
  const table = sortable([
    ['1.2M'], ['1,2'], ['2026-01-01'], ['12 ms'], ['Infinity'], ['2x'],
    ['0'], ['1.5K', '1500'], ['missing', ''], ['bad key', 'unknown'],
  ]);
  table.click();
  const missing = ['1.2M', '1,2', '2026-01-01', '12 ms', 'Infinity', '2x', 'missing', 'bad key'];
  assert.deepEqual(table.values(), ['0', '1.5K', ...missing]);
  table.click();
  assert.deepEqual(table.values(), ['1.5K', '0', ...missing]);
});
