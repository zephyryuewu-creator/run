import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import polyline from '@mapbox/polyline';
import ts from 'typescript';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const source = await readFile(
  new URL('../src/core/usStates.ts', import.meta.url),
  'utf8'
);
const shapes = await readFile(
  new URL('../src/assets/us-states.json', import.meta.url),
  'utf8'
);
const polylineModule = pathToFileURL(
  createRequire(import.meta.url).resolve('@mapbox/polyline')
).href;
const prepared = source
  .replace(
    /import boundaries from [^;]+;/,
    'const boundaries = ' + shapes.trim() + ';'
  )
  .replace("from '@mapbox/polyline'", "from '" + polylineModule + "'");
const compiled = ts.transpileModule(prepared, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const { US_STATES, findUSState, getActivityUSStates } = await import(
  'data:text/javascript;base64,' + Buffer.from(compiled).toString('base64')
);
test('footprint contains exactly 50 states, including Alaska and Hawaii', () => {
  assert.equal(US_STATES.length, 50);
  assert.equal(new Set(US_STATES.map((s) => s.id)).size, 50);
  for (const name of ['Georgia', 'Alaska', 'Hawaii'])
    assert.ok(US_STATES.some((s) => s.name === name && s.path.startsWith('M')));
  assert.ok(
    !US_STATES.some(
      (s) => s.name === 'District of Columbia' || s.name === 'Puerto Rico'
    )
  );
});
test('longitude/latitude finds mainland states and Alaska/Hawaii', () => {
  for (const [lng, lat, name] of [
    [-84.323, 33.797, 'Georgia'],
    [-74.006, 40.7128, 'New York'],
    [-118.2437, 34.0522, 'California'],
    [-149.9003, 61.2181, 'Alaska'],
    [-157.8583, 21.3069, 'Hawaii'],
  ])
    assert.equal(findUSState(lng, lat), name);
});
test('foreign, ocean, DC and invalid coordinates do not invent a state', () => {
  for (const [lng, lat] of [
    [116.4, 39.9],
    [-79.38, 43.65],
    [-77.0365, 38.8977],
    [0, 0],
    [NaN, 33],
    [181, 33],
    [-84, 91],
  ])
    assert.equal(findUSState(lng, lat), null);
});
test('real NRC GPS lights Georgia once despite repeated route points', async () => {
  const activities = JSON.parse(
    await readFile(
      new URL('../src/static/nike-activities.json', import.meta.url)
    )
  );
  assert.deepEqual(getActivityUSStates(activities[0]), ['Georgia']);
});
test('indoor and missing GPS stay unlocated, without changing the record', () => {
  for (const summary_polyline of [null, '', '_', 'None']) {
    const a = { summary_polyline };
    assert.deepEqual(getActivityUSStates(a), []);
    assert.equal(a.summary_polyline, summary_polyline);
  }
});
test('a recorded cross-state route counts each state only once', () => {
  const a = {
    summary_polyline: polyline.encode([
      [33.797, -84.323],
      [34.0522, -118.2437],
      [33.797, -84.323],
    ]),
  };
  assert.deepEqual(getActivityUSStates(a), ['California', 'Georgia']);
});
