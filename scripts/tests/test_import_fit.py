import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = datetime(2026, 11, 14, 1, tzinfo=UTC)
FIT_EPOCH = datetime(1989, 12, 31, tzinfo=UTC)


def fit_bytes(start, distance, seconds, points=(), *, treadmill=None):
    from garmin_fit_sdk.crc_calculator import CrcCalculator

    def message(local, global_id, fields, values):
        definition = struct.pack("<BBBHB", 0x40 | local, 0, 0, global_id, len(fields))
        definition += bytes(x for field in fields for x in field)
        return definition + bytes([local]) + values

    stamp = int((start - FIT_EPOCH).total_seconds())
    uint32, sint32, uint16, enum = 0x86, 0x85, 0x84, 0
    payload = message(0, 0, [(0, 1, enum)], b"\x04")
    for n, (lat, lon) in enumerate(points):
        payload += message(
            1,
            20,
            [(253, 4, uint32), (0, 4, sint32), (1, 4, sint32)],
            struct.pack(
                "<Iii", stamp + n, round(lat / 180 * 2**31), round(lon / 180 * 2**31)
            ),
        )
    payload += message(
        2,
        18,
        [
            (253, 4, uint32),
            (2, 4, uint32),
            (5, 1, enum),
            (6, 1, enum),
            (7, 4, uint32),
            (8, 4, uint32),
            (9, 4, uint32),
            (16, 1, 2),
            (22, 2, uint16),
        ],
        struct.pack(
            "<IIBBIIIBH",
            stamp + seconds,
            stamp,
            1,
            int(treadmill if treadmill is not None else not points),
            seconds * 1000,
            seconds * 1000,
            round(distance * 100),
            143,
            29,
        ),
    )
    content = struct.pack("<BBHI4s", 12, 16, 100, len(payload), b".FIT") + payload
    return content + struct.pack(
        "<H", CrcCalculator.calculate_crc(content, 0, len(content))
    )


@unittest.skipUnless(importlib.util.find_spec("garmin_fit_sdk"), "FIT SDK required")
class BatchFITTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.fit = root / "FIT_OUT"
        self.fit.mkdir()
        self.data, self.manifest = root / "activities.json", root / "data-source.json"
        self.base = {
            "run_id": 1,
            "record_id": "R0001",
            "source": "manual_excel_treadmill",
            "name": "An existing run",
            "type": "Run",
            "distance": 1609.344,
            "moving_time": "0:12:00",
            "average_speed": 1609.344 / 720,
            "start_date": "2026-11-12T05:00:00Z",
            "start_date_local": "2026-11-12T00:00:00",
            "date_precision": "day",
            "summary_polyline": None,
            "streak": 1,
        }
        self.seed([self.base])

    def seed(self, existing):
        self.data.write_text(json.dumps(existing), encoding="utf-8")
        self.manifest.write_text(
            json.dumps({"sources": {"excel": len(existing), "nike": 0}}),
            encoding="utf-8",
        )

    def run_fit(self):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "import_fit.py"),
                "--input-dir",
                str(self.fit),
                "--activities",
                str(self.data),
                "--manifest",
                str(self.manifest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_batch_keeps_history_and_draws_only_outdoor_route(self):
        outdoor = fit_bytes(
            START, 3218.69, 1200, [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
        )
        (self.fit / "outdoor.fit").write_bytes(outdoor)
        (self.fit / "renamed.FIT").write_bytes(outdoor)
        (self.fit / "indoor.fit").write_bytes(
            fit_bytes(START + timedelta(days=1), 1609.34, 720)
        )
        run = self.run_fit()
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = json.loads(self.data.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2]["record_id"], self.base["record_id"])
        self.assertIsNone(rows[0]["summary_polyline"])
        self.assertEqual(rows[1]["summary_polyline"], "_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        self.assertEqual(rows[1]["average_heartrate"], 143)
        self.assertEqual(rows[1]["elevation_gain"], 29)
        self.assertEqual(rows[1]["start_date_local"], "2026-11-13T20:00:00")
        self.assertEqual(rows[1]["moving_time"], "0:20:00")
        report = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(report["sources"], {"excel": 1, "nike": 0, "fit": 2})
        self.assertAlmostEqual(report["distance_miles"], 4, places=4)

    def test_possible_duplicate_stays_out_of_totals(self):
        (self.fit / "possible.fit").write_bytes(
            fit_bytes(START - timedelta(days=1), 1609.344, 720)
        )
        run = self.run_fit()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("possible.fit", run.stdout)
        self.assertIn("R0001", run.stdout)
        self.assertEqual(len(json.loads(self.data.read_text(encoding="utf-8"))), 1)

    def test_confirmed_duplicate_adds_route_to_existing_record(self):
        self.seed(
            [
                dict(
                    self.base,
                    start_date="2026-11-14T01:00:00Z",
                    start_date_local="2026-11-13T20:00:00",
                    date_precision="minute",
                )
            ]
        )
        (self.fit / "matching.fit").write_bytes(
            fit_bytes(
                START,
                1609.34,
                720,
                [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)],
            )
        )
        run = self.run_fit()
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = json.loads(self.data.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_id"], self.base["record_id"])
        self.assertEqual(rows[0]["summary_polyline"], "_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        self.assertEqual(rows[0]["source"], "manual_excel_treadmill")

    def test_corrupt_file_leaves_both_outputs_unchanged(self):
        before = (self.data.read_bytes(), self.manifest.read_bytes())
        (self.fit / "broken.fit").write_bytes(b"corrupt")
        result = self.run_fit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broken.fit", result.stderr)
        self.assertEqual((self.data.read_bytes(), self.manifest.read_bytes()), before)

    def test_treadmill_coordinates_do_not_draw_a_route(self):
        (self.fit / "treadmill.fit").write_bytes(
            fit_bytes(
                START,
                3218.69,
                1200,
                [(38.5, -120.2), (38.5001, -120.2001)],
                treadmill=True,
            )
        )
        run = self.run_fit()
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = json.loads(self.data.read_text(encoding="utf-8"))
        self.assertEqual(rows[0]["subtype"], "Treadmill")
        self.assertIsNone(rows[0]["summary_polyline"])
