import assert from 'node:assert/strict';
import test from 'node:test';
import { formatDistance, formatPace, formatGoal, goalProgress, displayActivityDate, displayActivityTime } from '../src/core/units.ts';

test('meters render as miles without losing the recorded 20.7 mile total', () => {
  assert.equal(formatDistance(33313.4208), '20.7');
  assert.equal(formatDistance(12391.9488), '7.7');
  assert.equal(formatDistance(0), '0.0');
});
test('pace is per mile and unknown or invalid speed stays unavailable', () => {
  assert.equal(formatPace(3.442208), '7:48');
  assert.equal(formatPace(0), '--');
  assert.equal(formatPace(NaN), '--');
});
test('unset goals never become NaN or completed progress', () => {
  assert.equal(formatGoal(0), '--');
  assert.equal(goalProgress(33313.4208, 0), 0);
  assert.equal(goalProgress(5, 10), 50);
  assert.equal(goalProgress(15, 10), 100);
});
test('date-only activity never invents a clock time', () => {
  assert.equal(displayActivityDate('2026-10-22T00:00:00', 'day'), '2026-10-22');
  assert.equal(displayActivityDate('2026-10-22T18:30:00'), '2026-10-22 18:30');
  assert.equal(displayActivityTime('2026-10-22T00:00:00', 'day'), '--');
  assert.equal(displayActivityTime('2026-10-22T18:30:00'), '18:30');
});
