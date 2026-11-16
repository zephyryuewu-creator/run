"""Merge runs from a FIT directory into the site’s freshly generated activities."""

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from garmin_fit_sdk import Decoder, Stream
from import_excel import METERS_PER_MILE, write_json
from nike_data import encode_polyline, merge_activities, number

ARTIFACT = Path("src/static/activities.json")
MANIFEST = Path("src/static/data-source.json")
SITE_ZONE = ZoneInfo("America/New_York")
SEMICIRCLE = 180 / 2**31


def duration_in_seconds(activity):
    hours, minutes, seconds = map(int, activity["moving_time"].split(":"))
    return hours * 3600 + minutes * 60 + seconds


def fit_runs(contents, file_hash, name):
    def decoder():
        return Decoder(Stream.from_byte_array(bytearray(contents)))

    if not decoder().check_integrity():
        raise ValueError("invalid or corrupt FIT file")
    messages, errors = decoder().read()
    if errors:
        raise ValueError(f"could not decode FIT ({len(errors)} errors)")
    if not any(
        row.get("type") == "activity" for row in messages.get("file_id_mesgs", [])
    ):
        return

    sessions = messages.get("session_mesgs", [])
    if not sessions:
        raise ValueError("FIT activity has no session records")
    for index, session in enumerate(sessions):
        if session.get("sport") != "running":
            continue
        start = session.get("start_time")
        if not isinstance(start, datetime) or start.utcoffset() is None:
            raise ValueError("running session has no valid start time")
        distance = number(session.get("total_distance"), "distance", positive=True)
        seconds = round(number(session.get("total_timer_time"), "time", positive=True))
        if not seconds:
            raise ValueError("running duration rounds to zero")
        end = session.get("timestamp")
        if not isinstance(end, datetime) or end <= start:
            end = start + timedelta(
                seconds=session.get("total_elapsed_time") or seconds
            )
        # FIT coordinates are integer semicircles, while the map expects degrees.
        allowed = (
            rec
            for rec in messages.get("record_mesgs", [])
            if isinstance(rec.get("timestamp"), datetime)
            and start <= rec["timestamp"] <= end
            and isinstance(rec.get("position_lat"), int)
            and isinstance(rec.get("position_long"), int)
        )
        points = [
            (rec["position_lat"] * SEMICIRCLE, rec["position_long"] * SEMICIRCLE)
            for rec in sorted(allowed, key=lambda rec: rec["timestamp"])
            if abs(rec["position_lat"]) <= 2**30 and abs(rec["position_long"]) <= 2**31
        ]
        treadmill = session.get("sub_sport") == "treadmill"
        record_key = f"{file_hash}:{index}"
        # Use the upper half of the exact JS integer range, away from Excel IDs
        # and Nike's epoch-millisecond IDs.
        digest = hashlib.sha256(record_key.encode("ascii")).hexdigest()
        yield {
            "run_id": 2**52 + int(digest[:13], 16),
            "record_id": f"FIT:{record_key}",
            "name": name,
            "type": "Run",
            "subtype": "Treadmill" if treadmill else "Run",
            "distance": distance,
            "moving_time": f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}",
            "start_date": start.astimezone(UTC)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "start_date_local": start.astimezone(SITE_ZONE)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds"),
            "date_precision": "minute",
            "location_country": None,
            "summary_polyline": (
                encode_polyline(points)
                if not treadmill and len(set(points)) > 1
                else None
            ),
            "average_heartrate": session.get("avg_heart_rate") or None,
            "average_speed": distance / seconds,
            "elevation_gain": session.get("total_ascent"),
            "source": "fit",
            "streak": 1,
        }


def matches_run(row, candidate):
    if row["type"] != "Run":
        return False
    # Allow small recording differences and rounding in manually entered miles.
    return (
        math.isclose(row["distance"], candidate["distance"], rel_tol=0.01, abs_tol=80)
        and abs(duration_in_seconds(row) - duration_in_seconds(candidate)) <= 60
    )


def merge_fit(directory, existing):
    if not directory.is_dir():
        raise ValueError(f"not a directory: {directory}")
    paths = sorted(
        path
        for path in directory.rglob("*")
        if path.suffix.lower() == ".fit" and path.is_file()
    )
    rows, seen = [row.copy() for row in existing], set()
    report = {
        "files": len(paths),
        "added": 0,
        "repeated": 0,
        "enriched": 0,
        "review": 0,
    }
    for path in paths:
        try:
            contents = path.read_bytes()
            digest = hashlib.sha256(contents).hexdigest()
            if digest in seen:
                report["repeated"] += 1
                continue
            seen.add(digest)
            for fit in fit_runs(contents, digest, path.stem):
                confirmed, possible = [], []
                fit_time = datetime.fromisoformat(fit["start_date"])
                for row in rows:
                    if not matches_run(row, fit):
                        continue
                    if row.get("date_precision") == "day":
                        if row["start_date_local"][:10] == fit["start_date_local"][:10]:
                            possible.append(row)
                    elif abs(
                        datetime.fromisoformat(row["start_date"]) - fit_time
                    ) <= timedelta(minutes=1):
                        confirmed.append(row)

                if len(confirmed) == 1:
                    row = confirmed[0]
                    if fit["summary_polyline"] and not row.get("summary_polyline"):
                        row["summary_polyline"] = fit["summary_polyline"]
                        report["enriched"] += 1
                    report["repeated"] += 1
                elif confirmed or possible:
                    candidates = ", ".join(
                        row["record_id"] for row in confirmed + possible
                    )
                    print(
                        f"FIT review: {path} may match {candidates}; kept existing records."
                    )
                    report["review"] += 1
                else:
                    rows.append(fit)
                    report["added"] += 1
        except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
            raise ValueError(f"{path}: {error}") from error
    return (
        merge_activities(rows, []) if report["added"] or report["enriched"] else rows
    ), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("FIT_OUT"))
    parser.add_argument("--activities", type=Path, default=ARTIFACT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    try:
        rows, report = merge_fit(
            args.input_dir, json.loads(args.activities.read_text(encoding="utf-8"))
        )
        if report["files"]:
            summary = json.loads(args.manifest.read_text(encoding="utf-8"))
            summary["sources"]["fit"] = sum(row["source"] == "fit" for row in rows)
            summary["record_count"] = len(rows)
            summary["distance_miles"] = round(
                sum(row["distance"] for row in rows) / METERS_PER_MILE, 6
            )
            summary["duration_seconds"] = sum(duration_in_seconds(row) for row in rows)
            summary["fit_import"] = report
            write_json(args.activities, rows)
            write_json(args.manifest, summary)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"FIT import failed: {error}", file=sys.stderr)
        return 1
    print(
        f"FIT files: {report['files']}; new runs: {report['added']}; "
        f"repeats: {report['repeated']}; enriched routes: {report['enriched']}; "
        f"needs review: {report['review']}; published runs with routes: "
        f"{sum(bool(row.get('summary_polyline')) for row in rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
