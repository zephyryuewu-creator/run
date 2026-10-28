"""Download your own NRC runs using the original project's Nike API endpoints."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from import_excel import write_json
from nike_data import gpx_document, normalize_nike

BASE_URL = "https://api.nike.com/plus/v3/"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "src/static/nike-activities.json"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def download_runs(token):
    opener = urllib.request.build_opener(NoRedirect)
    def request(resource):
        req = urllib.request.Request(BASE_URL + resource, headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
        try:
            with opener.open(req, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise ValueError(f"Nike API returned HTTP {error.code}; update NIKE_ACCESS_TOKEN if authorization expired") from None
        except urllib.error.URLError:
            raise ValueError("Could not reach Nike API; the previous dataset was preserved") from None
    cursor, pages, seen, raw_runs = "*", set(), set(), []
    while cursor:
        if cursor in pages:
            raise ValueError("Nike pagination repeated; preserving previous dataset")
        pages.add(cursor)
        page = request("activities/before_id/v3/" + urllib.parse.quote(cursor, safe="*") + "?limit=30&types=run%2Cjogging&include_deleted=false")
        if not isinstance(page.get("activities"), list):
            raise ValueError("Nike returned an invalid activity list")
        for summary in page["activities"]:
            activity_id = str(summary["id"])
            if activity_id in seen:
                continue
            seen.add(activity_id)
            if summary.get("app_id") in {"com.nike.ntc.brand.ios", "com.nike.ntc.brand.droid"}:
                continue
            raw = request("activity/" + urllib.parse.quote(activity_id, safe="") + "?metrics=ALL")
            if raw.get("delete_indicator") in (True, 1, "true"):
                continue
            if raw.get("type") in {"run", "jogging"}:
                raw_runs.append(raw)
        cursor = page.get("paging", {}).get("before_id")
    return raw_runs


def main():
    token = os.environ.get("NIKE_ACCESS_TOKEN", "").strip()
    if not token:
        print("NIKE_ACCESS_TOKEN repository secret is required", file=sys.stderr)
        return 1
    try:
        raw_runs = download_runs(token)
        rows = [normalize_nike(raw) for raw in raw_runs]
        if not rows:
            raise ValueError("Nike returned no completed runs; preserving previous dataset")
        rows.sort(key=lambda row: (row["start_date_local"], row["run_id"]), reverse=True)
        # Download and validate every run before modifying any persisted input.
        archives = []
        allowed = {"id", "type", "app_id", "start_epoch_ms", "end_epoch_ms", "active_duration_ms", "summaries", "tags", "metrics"}
        for raw, row in zip(raw_runs, [normalize_nike(raw) for raw in raw_runs]):
            archive = {key: value for key, value in raw.items() if key in allowed}
            archives.append((row["nike_activity_id"], archive, gpx_document(raw)))
        for activity_id, archive, gpx in archives:
            write_json(ROOT / "activities" / ("nike-" + activity_id + ".json"), archive)
            if gpx is not None:
                path = ROOT / "GPX_OUT" / ("nike-" + activity_id + ".gpx")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(gpx, encoding="utf-8")
        write_json(CACHE, rows)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print("NRC import failed: " + str(error), file=sys.stderr)
        return 1
    print(f"Saved {len(rows)} NRC runs; {sum(bool(row['summary_polyline']) for row in rows)} with GPS routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
