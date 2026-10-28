import polyline from '@mapbox/polyline';
import boundaries from '../assets/us-states.json' with { type: 'json' };
import type { Activity } from './types';
export const US_STATES = boundaries;
type Position = number[];
// Rings crossing the antimeridian are evaluated in a consistent 0..360 frame.
function inRing(lng: number, lat: number, ring: Position[]): boolean {
  const longitudes = ring.map((p) => p[0]);
  const crossesDateline =
    Math.max(...longitudes) - Math.min(...longitudes) > 180;
  const x = crossesDateline && lng < 0 ? lng + 360 : lng;
  const longitude = (value: number) =>
    crossesDateline && value < 0 ? value + 360 : value;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = longitude(ring[i][0]),
      yi = ring[i][1];
    const xj = longitude(ring[j][0]),
      yj = ring[j][1];
    if (yi > lat !== yj > lat && x < ((xj - xi) * (lat - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}
// Cache polygon bounds once; route-point checks then skip distant states.
const indexedStates = US_STATES.map((state) => ({
  name: state.name,
  polygons: state.polygons.map((rings) => {
    const outer = rings[0];
    return {
      rings,
      minLng: Math.min(...outer.map((p) => p[0])),
      maxLng: Math.max(...outer.map((p) => p[0])),
      minLat: Math.min(...outer.map((p) => p[1])),
      maxLat: Math.max(...outer.map((p) => p[1])),
    };
  }),
}));
export function findUSState(lng: number, lat: number): string | null {
  if (
    !Number.isFinite(lng) ||
    !Number.isFinite(lat) ||
    Math.abs(lng) > 180 ||
    Math.abs(lat) > 90
  )
    return null;
  for (const state of indexedStates) {
    for (const polygon of state.polygons) {
      if (
        lng < polygon.minLng ||
        lng > polygon.maxLng ||
        lat < polygon.minLat ||
        lat > polygon.maxLat
      )
        continue;
      if (
        inRing(lng, lat, polygon.rings[0]) &&
        !polygon.rings.slice(1).some((ring) => inRing(lng, lat, ring))
      )
        return state.name;
    }
  }
  return null;
}
export function getActivityUSStates(
  activity: Pick<Activity, 'summary_polyline'>
): string[] {
  if (!activity.summary_polyline || activity.summary_polyline === 'None')
    return [];
  try {
    const visited = new Set<string>();
    for (const [lat, lng] of polyline.decode(activity.summary_polyline)) {
      const name = findUSState(lng, lat);
      if (name) visited.add(name);
    }
    return [...visited].sort();
  } catch {
    return [];
  }
}
