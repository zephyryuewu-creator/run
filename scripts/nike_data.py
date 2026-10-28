"""Adapt NRC metrics to the unchanged running_page Activity contract.
Nike endpoints and metric units follow upstream run_page/nike_sync.py.
"""
import math
import uuid
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo


def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label + " must be a finite number")
    if positive and value <= 0:
        raise ValueError(label + " must be positive")
    return value


def metric_values(activity, kind):
    values = {}
    for metric in activity.get("metrics", []):
        if metric.get("type") == kind:
            for point in metric.get("values", []):
                stamp, value = point.get("start_epoch_ms"), point.get("value")
                if isinstance(stamp, (int, float)) and not isinstance(stamp, bool):
                    values[stamp] = value
    return values


def coordinates(activity):
    latitudes = metric_values(activity, "latitude")
    longitudes = metric_values(activity, "longitude")
    result = []
    for stamp in sorted(latitudes.keys() & longitudes.keys()):
        lat, lon = latitudes[stamp], longitudes[stamp]
        try:
            number(lat, "Latitude")
            number(lon, "Longitude")
        except ValueError:
            continue
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            result.append((stamp, lat, lon))
    return result


def encode_polyline(points):
    encoded, previous = [], [0, 0]
    for point in points:
        for axis, value in enumerate(point):
            current = math.floor(value * 100000 + 0.5)
            delta = current - previous[axis]
            previous[axis] = current
            delta = ~(delta << 1) if delta < 0 else delta << 1
            while delta >= 0x20:
                encoded.append(chr((0x20 | (delta & 0x1F)) + 63))
                delta >>= 5
            encoded.append(chr(delta + 63))
    return "".join(encoded)


def normalize_nike(activity):
    try:
        activity_id = str(uuid.UUID(activity["id"]))
    except (KeyError, ValueError, AttributeError, TypeError) as error:
        raise ValueError("Invalid Nike activity ID") from error
    if activity.get("type") not in {"run", "jogging"}:
        raise ValueError("Nike activity must be a run")
    start = number(activity.get("start_epoch_ms"), "Start timestamp", True)
    end = number(activity.get("end_epoch_ms"), "End timestamp", True)
    duration = number(activity.get("active_duration_ms"), "Active duration", True)
    if end <= start or end != int(end) or end > 9007199254740991:
        raise ValueError("Invalid Nike activity time range")
    summaries = {item["metric"]: item.get("value") for item in activity.get("summaries", [])}
    distance = number(summaries.get("distance"), "Distance", True) * 1000
    seconds = math.floor(duration / 1000 + 0.5)
    if seconds < 1:
        raise ValueError("Nike duration rounds to zero")
    started = datetime.fromtimestamp(start / 1000, UTC)
    local = started.astimezone(ZoneInfo("America/New_York")).replace(tzinfo=None)
    points = coordinates(activity)
    heart_rate = summaries.get("heart_rate")
    if heart_rate is not None:
        number(heart_rate, "Heart rate", True)
    ascent = summaries.get("ascent")
    if ascent is not None:
        number(ascent, "Ascent")
        if ascent < 0:
            raise ValueError("Ascent must be nonnegative")
    steps = summaries.get("steps")
    if steps is not None:
        number(steps, "Steps")
        if steps < 0 or steps != int(steps):
            raise ValueError("Steps must be a nonnegative integer")
    tags = activity.get("tags", {})
    return {
        "run_id": int(end), "record_id": "NRC:" + activity_id,
        "nike_activity_id": activity_id,
        "name": tags.get("com.nike.name") or "NRC outdoor run",
        "type": "Run", "subtype": "Run", "source": "nike",
        "distance": round(distance, 6),
        "moving_time": f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}",
        "start_date": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "start_date_local": local.isoformat(timespec="seconds"), "date_precision": "minute",
        "summary_polyline": encode_polyline([(p[1], p[2]) for p in points]) if len(points) >= 2 else None,
        "location_country": None, "average_heartrate": heart_rate,
        "average_speed": distance / seconds, "elevation_gain": ascent,
        "running_steps": int(steps) if steps is not None else None,
        "streak": 1, "workout_details": None, "notes": "Recorded with Nike Run Club",
    }


def gpx_document(activity):
    points = coordinates(activity)
    if len(points) < 2:
        return None
    namespace = "http://www.topografix.com/GPX/1/1"
    ET.register_namespace("", namespace)
    root = ET.Element("{" + namespace + "}gpx", version="1.1", creator="running_page NRC")
    track = ET.SubElement(root, "{" + namespace + "}trk")
    ET.SubElement(track, "{" + namespace + "}name").text = activity.get("tags", {}).get("com.nike.name") or "NRC run"
    segment = ET.SubElement(track, "{" + namespace + "}trkseg")
    elevations = metric_values(activity, "elevation")
    for stamp, lat, lon in points:
        point = ET.SubElement(segment, "{" + namespace + "}trkpt", lat=str(lat), lon=str(lon))
        elevation = elevations.get(stamp)
        if isinstance(elevation, (int, float)) and math.isfinite(elevation):
            ET.SubElement(point, "{" + namespace + "}ele").text = str(elevation)
        ET.SubElement(point, "{" + namespace + "}time").text = datetime.fromtimestamp(stamp / 1000, UTC).isoformat(timespec="milliseconds").replace(".000+00:00", "Z").replace("+00:00", "Z")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def merge_activities(indoor, nike):
    if not isinstance(nike, list):
        raise ValueError("Nike dataset must be a list")
    ids, records, rows = set(), set(), []
    for row in nike:
        if not isinstance(row, dict) or row.get("source") != "nike" or not str(row.get("record_id", "")).startswith("NRC:"):
            raise ValueError("Invalid cached Nike record")
        number(row.get("distance"), "Cached Nike distance", True)
        number(row.get("average_speed"), "Cached Nike speed", True)
        datetime.fromisoformat(row["start_date_local"])
    for original in indoor + nike:
        row = original.copy()
        run_id, record_id = row["run_id"], row["record_id"]
        number(run_id, "Run ID", True)
        if run_id != int(run_id) or run_id > 9007199254740991:
            raise ValueError("Run ID must be a safe integer")
        if run_id in ids or record_id in records:
            raise ValueError("Duplicate running record or numeric ID")
        ids.add(run_id)
        records.add(record_id)
        rows.append(row)
    rows.sort(key=lambda row: (row["start_date_local"], row["run_id"]))
    previous, streak = None, 0
    for row in rows:
        day = datetime.fromisoformat(row["start_date_local"]).date()
        if day != previous:
            streak = streak + 1 if previous and day == previous + timedelta(days=1) else 1
        row["streak"] = streak
        previous = day
    return list(reversed(rows))
