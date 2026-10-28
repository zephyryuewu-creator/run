# NRC Outdoor Import Implementation Plan

> For agentic workers: execute the approved direct-Nike integration inline.

Goal: Show NRC outdoor runs with real GPS alongside existing Excel treadmill records on GitHub Pages.
Architecture: A small adapter follows upstream Nike endpoints and metrics. A persistent NRC JSON input is merged when Excel is imported. A manual Actions workflow refreshes NRC, commits data and calls the Pages workflow.
Tech Stack: Python 3.12 standard library, openpyxl 3.1.5, existing React Dashboard and GitHub Actions.
Spec: docs/superpowers/specs/2026-10-28-nrc-outdoor-design.md

## Constraints
- Publish to zephyryuewu-creator/run and its existing GitHub Pages URL.
- Preserve Dashboard components, CSS and the existing mile display.
- Credentials stay in Actions Secrets and never enter public source, JSON or logs.
- Preserve Excel indoor records and use actual NRC GPS only.

## Review Focus
- Cached outdoor runs survive later Excel uploads.
- Refreshing NRC does not duplicate the same Nike activity.
- Nike API errors do not overwrite the prior valid input.
- UTC to New York date conversion remains correct across date boundaries.
- Invalid or mismatched GPS points never create a fabricated route.

## Tasks
- [x] Verify credentials with the Nike API and save NIKE_ACCESS_TOKEN as a repository Secret.
- [x] Add regression tests first and observe missing nike_data fail on GitHub Actions (40748832129).
- [ ] Implement normalization, GPX export, validation and deterministic dataset merge.
- [ ] Add secret-backed NRC workflow and update Pages to merge persisted NRC input.
- [ ] Run Python and Node checks, import the real NRC activity, and verify production build on the branch.
- [ ] Review the resulting diff, merge and verify the public Dashboard contains both data sources.

Ruling: Use a separate GitHub branch for implementation and run checks on GitHub, honoring the request to work on the repository and its hosted preview.
Ruling: Retain the latest successful NRC import independently of token expiry; renew the token only when fetching new NRC records.

Review: preserve reusable-workflow secrets with secrets: inherit. All Python tests, real NRC import and frontend build passed in 40749866516. GitHub App cannot push workflow edits; apply those through the authenticated GitHub UI. Deferred minor: HTTP pagination/error paths lack mock regression tests; previously exported GPX files are retained if a later activity loses GPS.
