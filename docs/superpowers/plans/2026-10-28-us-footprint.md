# US Footprint Implementation Plan
Goal: Replace the China footprint with 50 US states in the existing Dashboard.
Architecture: Vendor Census-derived geographic boundaries and projected paths; derive visited states from GPS in the browser. Keep source running data and the Route map implementation intact.
Tech stack: Existing React, TypeScript and polyline dependency, no new runtime dependency.
Constraints: 50 states includes Alaska and Hawaii; no guessed indoor locations; all work on a GitHub branch and verified on GitHub Pages.
- [x] Write behavior tests first and observe RED on the pre-feature branch.
- [x] Generate state boundaries and paths from pinned us-atlas 3.0.1 with ISC notice.
- [x] Add shared GPS state classification and adapt the original footprint card, profile counter and route filter.
- [ ] Run state tests, existing unit tests, type checking, targeted lint and production build.
- [ ] Review the diff, merge and visually verify Georgia highlight, state selection and existing routes on GitHub Pages.
Review focus: coordinate order, dateline, holes/DC exclusion, no-GPS records, repeated and cross-state GPS points, state filtering without changing all-run totals.
