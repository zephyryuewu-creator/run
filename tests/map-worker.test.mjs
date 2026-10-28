import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { posix } from 'node:path';
import test from 'node:test';

const dist = new URL('../dist/', import.meta.url);
const assets = new URL('assets/', dist);

function emittedWorker() {
  const name = readdirSync(assets).find((file) =>
    /^maplibre-gl-worker-[\w-]+\.m?js$/.test(file)
  );
  assert.ok(
    name,
    'MapLibre worker asset was not emitted by the production build'
  );
  return { name, code: readFileSync(new URL(name, assets), 'utf8') };
}

test('production emits a nonempty JavaScript worker rather than a missing page', () => {
  const worker = emittedWorker();
  assert.ok(worker.code.length > 0);
  assert.doesNotMatch(worker.code, /^\s*<!doctype html/i);
});

test('the map bundle references its emitted worker under the deployed site base', () => {
  const worker = emittedWorker();
  const html = readFileSync(new URL('index.html', dist), 'utf8');
  const entry = html.match(/<script\b[^>]*\bsrc=["']([^"']+)["']/);
  assert.ok(entry, 'The production HTML must reference its application bundle');
  const entryPath = new URL(entry[1], 'https://example.invalid/').pathname;
  const expectedPath = posix.dirname(entryPath) + '/' + worker.name;
  const scripts = readdirSync(assets)
    .filter((file) => /\.m?js$/.test(file))
    .map((file) => readFileSync(new URL(file, assets), 'utf8'))
    .join('\n');
  assert.ok(
    scripts.includes(expectedPath),
    'The map bundle must reference the worker at the deployed asset path: ' +
      expectedPath
  );
});
