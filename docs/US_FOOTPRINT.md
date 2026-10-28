# US footprint map
The Dashboard footprint now shows the 50 US states, including inset Alaska and Hawaii. DC and territories are outside the 50-state total.
Each activity counts once per state containing one of its recorded GPS points. An activity with points in several states counts once in each. Missing GPS (including the indoor Excel records) does not invent a location. The Excel and NRC source data are unchanged.
The state highlight and profile state count use the same function. Clicking a visited state filters the Home route map; Clear restores all routes. Existing year selection still applies to the footprint and route map.
Boundaries and projected SVG paths are vendored from us-atlas 3.0.1, a redistribution of the US Census Bureau 2017 cartographic boundaries. Point-in-polygon uses geographic coordinates; display uses the packaged Albers USA projection (975 x 610). Generalized state/coast boundaries are approximate. No location is sent to a geocoding service and no API key is needed.
Sources: https://github.com/topojson/us-atlas and https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
ISC notice: docs/licenses/us-atlas-LICENSE.txt.
Tests run before every build: node --test tests/us-states.test.mjs. They cover 50 states, the real Georgia NRC track, missing GPS, multiple states, foreign/invalid coordinates, DC exclusion, Alaska and Hawaii.
