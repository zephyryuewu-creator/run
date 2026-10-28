# Route map repair

The previous Route map used Mapbox GL JS 3 without a Mapbox token. That renderer revokes rendering without valid Mapbox authorization, including when its style is served by a different provider. The configured CARTO fallback also now documents a separate key requirement.

Use MapLibre GL JS 6.16.0 and the standard OpenStreetMap raster service for this component. Keep the existing card, real GPS lines, Fit routes, navigation, imperial scale, fullscreen and locale controls. Keep attribution visible and use normal browser caching. The China footprint component and running datasets are unchanged. Existing Mapbox dependencies/configuration remain available to other parts of the upstream application.

Alternatives: supplying Mapbox credentials would retain the old renderer but requires a separate account/key. MapLibre with CARTO would require a CARTO key. The chosen MapLibre/OpenStreetMap combination works for the current personal website without either key.

Regression case before the change: Tracks contains one valid NRC GPS route but displays “Basemap failed to load” and an empty canvas. This was reproduced with the browser before changing code.

Verification: targeted TypeScript, ESLint and Prettier checks; existing frontend unit tests; production build; then verify visible street tiles and the GPS line on Home and Tracks, Fit routes, zoom, fullscreen and light/dark themes on the deployed website.

References:
- https://github.com/mapbox/mapbox-gl-js/blob/v3.23.0/src/ui/map.ts
- https://github.com/CartoDB/basemap-styles
- https://maplibre.org/maplibre-gl-js/docs/
- https://operations.osmfoundation.org/policies/tiles/

## Vite worker deployment

MapLibre 6 requires an explicit worker URL when bundled with Vite. Import maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url and call setWorkerUrl before creating any maps. The production build now runs tests/map-worker.test.mjs to verify that the worker is emitted and referenced under the correct site base path.

Reference: https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/
