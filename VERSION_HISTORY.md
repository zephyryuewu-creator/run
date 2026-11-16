# Version history

## V1.1 → V1.2 — 2026-11-15

- **Previous baseline:** `b54a9a3ba20b3fadf1f57faad3c566441ed14970`.
  The previous workflow and Tracks component are preserved at
  `versions/V1.1/.github/workflows/gh-pages.yml` and
  `versions/V1.1/src/components/TracksPage.tsx.snapshot`.
- **Changed:** `scripts/import_fit.py` scans `FIT_OUT/` and merges validated
  runs into the Pages build data. Repeated FIT files count once, ambiguous
  overlaps are reported, and a confirmed match can add a missing route.
  `.github/workflows/gh-pages.yml` imports FIT on publication and triggers on
  uploads to `master`; manual reruns remain available.
  `src/components/TracksPage.tsx` no longer rejects valid short routes solely
  because of their encoded length. `FIT_OUT/README.md` explains the upload
  and publishing steps; `scripts/tests/test_import_fit.py` tests the importer.
- **Preserved:** original FIT files, the Excel workbook, Nike data and sync
  workflow, output units, existing map layout, language setting, and
  the original Excel importer. No sample activity was committed.
- **Verified locally:** 14 Python import tests, 4 units tests, and all 8
  map/build tests passed; the production build completed. Black and Ruff
  checked the two new Python files. The two-stage import left the empty-FIT
  build unchanged and imported one short route from two identical FIT copies.
  On Windows, the initial Prettier run reported checkout CRLF differences;
  `pnpm run check --end-of-line auto` passed.
- **Limitations:** FIT tests use synthetic outdoor and indoor files; no user
  FIT was published for testing. Historical FITs remain inputs for every build.
