// The upstream Activity contract remains meters and meters/second.
export const METERS_PER_MILE = 1609.344;

export function formatDistance(meters: number): string {
  return (meters / METERS_PER_MILE).toFixed(1);
}

export function formatPace(speedMs: number): string {
  if (!Number.isFinite(speedMs) || speedMs <= 0) return '--';
  const seconds = Math.round(METERS_PER_MILE / speedMs);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

export function formatGoal(miles: number): string {
  return Number.isFinite(miles) && miles > 0 ? String(miles) : '--';
}

export function goalProgress(actual: number, target: number): number {
  if (!Number.isFinite(target) || target <= 0) return 0;
  return Math.min(100, Math.max(0, (actual / target) * 100));
}

export function displayActivityDate(
  localDate: string,
  precision?: string
): string {
  return precision === 'day'
    ? localDate.slice(0, 10)
    : localDate.slice(0, 16).replace('T', ' ');
}

export function displayActivityTime(
  localDate: string,
  precision?: string
): string {
  return precision === 'day' ? '--' : localDate.slice(11, 16);
}
