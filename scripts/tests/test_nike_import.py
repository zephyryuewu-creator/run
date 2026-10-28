import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from nike_data import encode_polyline, gpx_document, merge_activities, normalize_nike

START = int(datetime(2026, 10, 28, 2, tzinfo=UTC).timestamp() * 1000)

def example():
    return {
        "id": "11111111-1111-4111-8111-111111111111",
        "type": "run", "app_id": "com.nike.sport.running.ios",
        "start_epoch_ms": START, "end_epoch_ms": START + 610000,
        "active_duration_ms": 600500,
        "summaries": [{"metric": "distance", "value": 1.609344},
                      {"metric": "ascent", "value": 12.5},
                      {"metric": "steps", "value": 1000}],
        "tags": {"com.nike.name": "Evening outdoor run"},
        "metrics": [
            {"type": "latitude", "values": [
                {"start_epoch_ms": START + i * 1000, "value": v}
                for i, v in enumerate([38.5, 40.7, 43.252])]},
            {"type": "longitude", "values": [
                {"start_epoch_ms": START + i * 1000, "value": v}
                for i, v in enumerate([-120.2, -120.95, -126.453])]},
        ],
    }

class NikeImportTests(unittest.TestCase):
    def test_nrc_units_active_duration_new_york_date_and_missing_heart_rate(self):
        row = normalize_nike(example())
        self.assertAlmostEqual(row["distance"], 1609.344)
        self.assertEqual(row["moving_time"], "0:10:01")
        self.assertEqual(row["start_date_local"], "2026-10-27T22:00:00")
        self.assertEqual(row["start_date"], "2026-10-28T02:00:00Z")
        self.assertEqual(row["source"], "nike")
        self.assertEqual(row["name"], "Evening outdoor run")
        self.assertEqual(row["running_steps"], 1000)
        self.assertEqual(row["elevation_gain"], 12.5)
        self.assertIsNone(row["average_heartrate"])
        self.assertAlmostEqual(row["average_speed"], 1609.344 / 601)

    def test_gps_matches_google_polyline_reference_and_exports_timed_gpx(self):
        expected = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        row = normalize_nike(example())
        self.assertEqual(row["summary_polyline"], expected)
        self.assertEqual(encode_polyline([(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]), expected)
        document = ET.fromstring(gpx_document(example()))
        points = document.findall(".//{http://www.topografix.com/GPX/1/1}trkpt")
        self.assertEqual(len(points), 3)
        self.assertEqual(float(points[0].attrib["lat"]), 38.5)
        self.assertEqual(float(points[0].attrib["lon"]), -120.2)
        self.assertEqual(points[0].find("{http://www.topografix.com/GPX/1/1}time").text, "2026-10-28T02:00:00Z")

    def test_coordinates_join_by_timestamp_and_no_route_is_invented(self):
        raw = example()
        raw["metrics"][1]["values"].pop(1)
        points = ET.fromstring(gpx_document(raw)).findall(".//{http://www.topografix.com/GPX/1/1}trkpt")
        self.assertEqual(len(points), 2)
        self.assertEqual(float(points[1].attrib["lat"]), 43.252)
        self.assertEqual(float(points[1].attrib["lon"]), -126.453)
        raw["metrics"] = []
        self.assertIsNone(normalize_nike(raw)["summary_polyline"])
        self.assertIsNone(gpx_document(raw))

    def test_invalid_measurements_are_rejected(self):
        for key, value in [("active_duration_ms", 0), ("start_epoch_ms", None)]:
            raw = example()
            raw[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_nike(raw)
        raw = example()
        raw["summaries"][0]["value"] = float("nan")
        with self.assertRaises(ValueError):
            normalize_nike(raw)

    def test_merging_is_idempotent_and_preserves_indoor_missing_gps(self):
        nike = normalize_nike(example())
        indoor = copy.deepcopy(nike)
        indoor.update(run_id=1, record_id="R0001", source="manual_excel_treadmill", name="Treadmill · Easy", summary_polyline=None)
        merged = merge_activities([indoor], [nike])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged, merge_activities([indoor], [nike]))
        self.assertIsNone(next(row for row in merged if row["record_id"] == "R0001")["summary_polyline"])
        with self.assertRaises(ValueError):
            merge_activities([indoor], [nike, nike])
        collision = copy.deepcopy(nike)
        collision["run_id"] = 1
        with self.assertRaises(ValueError):
            merge_activities([indoor], [collision])

    def test_cli_keeps_nrc_when_excel_is_reimported(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cache = tmp / "nike.json"
            cache.write_text(json.dumps([normalize_nike(example())]), encoding="utf-8")
            output, manifest = tmp / "combined.json", tmp / "source.json"
            command = [sys.executable, str(ROOT / "scripts/import_excel.py"),
                str(ROOT / "scripts/tests/fixtures/Running_Log_V1.1.xlsx"),
                "--nike-data", str(cache), "--output", str(output), "--manifest", str(manifest)]
            for _ in range(2):
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = json.loads(output.read_text())
                self.assertEqual(len(rows), 3)
                self.assertEqual(sum(row["source"] == "nike" for row in rows), 1)
                self.assertEqual(sum(row["summary_polyline"] is None for row in rows), 2)
                info = json.loads(manifest.read_text())
                self.assertAlmostEqual(info["distance_miles"], 21.7)
                self.assertEqual(info["sources"], {"excel": 2, "nike": 1})
            cache.write_text('{"invalid":true}')
            previous = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), previous)

if __name__ == "__main__":
    unittest.main()
