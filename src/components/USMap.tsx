import { memo, useMemo, useState } from 'react';
import type { Activity, SportFilter } from '../types';
import { useLocale } from '../hooks/useLocale';
import { US_STATES, getActivityUSStates } from '../core/usStates';
interface USMapProps {
  activities: Activity[];
  filter: SportFilter;
  onSelectState?: (state: string | null) => void;
  selectedState?: string | null;
}
export const USMap = memo(function USMap({
  activities,
  filter,
  onSelectState,
  selectedState,
}: USMapProps) {
  const { locale } = useLocale();
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const SVG_W = 975;
  const SVG_H = 610;
  const paths = US_STATES;

  // Build state → activity count map
  const stateCount = useMemo(() => {
    const map = new Map<string, number>();
    for (const a of activities) {
      for (const name of getActivityUSStates(a)) {
        map.set(name, (map.get(name) ?? 0) + 1);
      }
    }
    return map;
  }, [activities]);

  const visitedCount = stateCount.size;
  const displayState = hoveredState ?? selectedState;
  const displayCount = displayState ? (stateCount.get(displayState) ?? 0) : 0;

  function handleClick(name: string) {
    if (!onSelectState) return;
    const visited = (stateCount.get(name) ?? 0) > 0;
    if (!visited) return;
    onSelectState(selectedState === name ? null : name);
  }

  return (
    <div
      role="region"
      aria-label={locale === 'zh' ? '足迹地图' : 'Footprint map'}
      className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5"
    >
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">
          {locale === 'zh' ? '足迹地图' : 'Footprint Map'}
        </h2>
        <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
          {selectedState ? (
            <button
              onClick={() => onSelectState?.(null)}
              className="flex items-center gap-1 text-[var(--color-accent)] transition-opacity hover:opacity-70"
            >
              <svg
                className="h-3 w-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              {locale === 'zh' ? '清除筛选' : 'Clear'}
            </button>
          ) : (
            <>
              <span className="font-mono font-bold text-[var(--color-accent)]">
                {visitedCount}
              </span>
              <span>
                / {50} {locale === 'zh' ? '州' : 'states'}
              </span>
            </>
          )}
        </div>
      </div>

      {/* SVG Map — aspect-ratio wrapper prevents stretching */}
      <div className="relative" style={{ aspectRatio: `${SVG_W} / ${SVG_H}` }}>
        <svg
          key={filter}
          role="group"
          aria-label={
            locale === 'zh' ? '按州筛选路线' : 'Filter routes by state'
          }
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          preserveAspectRatio="xMidYMid meet"
          width="100%"
          height="100%"
          style={{ display: 'block', position: 'absolute', inset: 0 }}
        >
          {paths.map((feature) => {
            const name = feature.name;
            const count = stateCount.get(name) ?? 0;
            const visited = count > 0;
            const isHovered = hoveredState === name;
            const isSelected = selectedState === name;

            let fill: string;
            if (visited) {
              if (isSelected) {
                fill = 'var(--color-accent)';
              } else if (isHovered) {
                fill =
                  'color-mix(in srgb, var(--color-accent) 80%, transparent)';
              } else if (selectedState) {
                // dim other states when one is selected
                fill =
                  'color-mix(in srgb, var(--color-accent) 25%, transparent)';
              } else {
                fill =
                  'color-mix(in srgb, var(--color-accent) 55%, transparent)';
              }
            } else {
              fill = 'var(--color-border)';
            }

            return (
              <path
                key={feature.id}
                d={feature.path}
                fill={fill}
                stroke="var(--color-bg)"
                strokeWidth="1.5"
                fillRule="evenodd"
                className={`transition-all duration-150 ${visited ? 'cursor-pointer focus:outline-2 focus:outline-[var(--color-accent)]' : 'cursor-default'}`}
                onMouseEnter={() => setHoveredState(name)}
                onMouseLeave={() => setHoveredState(null)}
                role={visited && onSelectState ? 'button' : undefined}
                tabIndex={visited && onSelectState ? 0 : undefined}
                aria-label={`${name} · ${count} ${locale === 'zh' ? '次活动' : 'activities'}`}
                aria-pressed={visited && onSelectState ? isSelected : undefined}
                onFocus={() => setHoveredState(name)}
                onBlur={() => setHoveredState(null)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    handleClick(name);
                  }
                }}
                onClick={() => handleClick(name)}
              />
            );
          })}
        </svg>
      </div>

      {/* Tooltip */}
      <div className="mt-1.5 h-4 text-xs text-[var(--color-muted)]">
        {displayState && (
          <>
            <span className="font-medium text-[var(--color-text)]">
              {displayState}
            </span>
            {displayCount > 0 && (
              <span className="ml-1.5">
                {displayCount} {locale === 'zh' ? '次' : 'activities'}
              </span>
            )}
            {selectedState === displayState && !hoveredState && (
              <span className="ml-1.5 text-[var(--color-accent)]">
                {locale === 'zh' ? '（已筛选）' : '(filtered)'}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
});
