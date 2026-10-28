# NRC outdoor runs and Excel treadmill runs

The existing Dashboard reads a combined Activity dataset. Distance is displayed in miles and pace in min/mi. Excel remains the source for indoor treadmill records; NRC supplies real outdoor GPS.

## Import a new NRC run
1. Sign in to nike.com with the same account used by NRC. Follow upstream README “Nike Run Club New” to obtain your current access_token.
2. Save the complete token as repository Actions Secret NIKE_ACCESS_TOKEN.
3. Open Actions → Sync Nike Run Club → Run workflow on master.
4. Wait for both the sync job and the GitHub Pages publishing job to succeed, then refresh your public website.

This is a temporary access token. It does not automatically refresh; if Nike returns HTTP 401, replace the Secret with a current token and rerun the workflow. Updating a Secret alone does not start a sync. The code never embeds the token in source or generated running data.

## Files
- Running_Log_EN.xlsx: your cumulative indoor log. Uploading a replacement on master continues to publish automatically.
- src/static/nike-activities.json: last successfully imported NRC records. Kept when Excel is updated or Nike credentials expire.
- src/static/activities.json: combined normalized Activity dataset. Also regenerated during Pages builds.
- activities/nike-*.json: archived activity measurements, with authentication/session fields excluded.
- GPX_OUT/nike-*.gpx: actual timestamped outdoor GPS routes.
- scripts/sync_nike.py: Nike download, following upstream endpoints.
- scripts/nike_data.py: units, dates, GPS normalization and deterministic merge.

Runs are distinguished by stable source-specific record IDs. Re-running the import does not add duplicates. Do not also enter the same NRC outdoor run into the indoor Excel log. Missing GPS, heart rate and country remain unknown; no indoor route is fabricated. The original China footprint map remains unchanged. Route map uses MapLibre and OpenStreetMap independently of NRC authorization.

References: https://github.com/yihong0618/running_page#nike-run-club-new and https://github.com/yihong0618/running_page/issues/692
