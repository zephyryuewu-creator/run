import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/import_excel.py"
SOURCE = ROOT / "scripts/tests/fixtures/Running_Log_V1.1.xlsx"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def patched_xlsx(target, edits):
    # Mutate test fixtures at the OOXML level, never author user workbooks.
    with ZipFile(SOURCE) as source, ZipFile(target, "w", ZIP_DEFLATED) as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                tree = ET.fromstring(data)
                for address, value in edits.items():
                    cell = tree.find(f'.//s:c[@r="{address}"]', NS)
                    for child in list(cell):
                        cell.remove(child)
                    cell.attrib.pop("t", None)
                    if value is not None:
                        if isinstance(value, str):
                            cell.set("t", "inlineStr")
                            ET.SubElement(
                                ET.SubElement(cell, f'{{{NS["s"]}}}is'),
                                f'{{{NS["s"]}}}t',
                            ).text = value
                        else:
                            ET.SubElement(cell, f'{{{NS["s"]}}}v').text = str(value)
                data = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
            out.writestr(item, data)


class ImportExcelTests(unittest.TestCase):
    def run_import(self, workbook=SOURCE, initial=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        output = Path(tmp.name) / "activities.json"
        manifest = Path(tmp.name) / "source.json"
        if initial is not None:
            output.write_text(initial, encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(workbook),
                "--output",
                str(output),
                "--manifest",
                str(manifest),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result, output, manifest

    def test_actual_records_keep_miles_dates_missing_measurements_and_classification(
        self,
    ):
        result, output, manifest = self.run_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["record_id"] for r in rows], ["R0002", "R0001"])
        by_id = {r["record_id"]: r for r in rows}
        self.assertAlmostEqual(by_id["R0001"]["distance"], 12391.9488, places=5)
        self.assertAlmostEqual(by_id["R0002"]["distance"], 20921.472, places=5)
        self.assertEqual(by_id["R0001"]["moving_time"], "1:00:00")
        self.assertEqual(by_id["R0002"]["moving_time"], "1:56:00")
        self.assertEqual(by_id["R0001"]["start_date_local"][:10], "2026-10-22")
        self.assertEqual(by_id["R0001"]["date_precision"], "day")
        self.assertEqual(by_id["R0001"]["subtype"], "Long run")
        for row in rows:
            self.assertEqual(row["type"], "Run")
            for field in [
                "summary_polyline",
                "location_country",
                "average_heartrate",
                "elevation_gain",
            ]:
                self.assertIsNone(row[field])
        info = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(info["record_count"], 2)
        self.assertAlmostEqual(info["distance_miles"], 20.7)
        self.assertEqual(info["duration_seconds"], 10560)
        self.assertEqual(info["weekly_check_ins"][0]["status"], "In progress")

    def test_invalid_partial_duplicate_and_wrong_unit_do_not_replace_last_good_json(
        self,
    ):
        variants = [
            {"D14": -1},
            {"E14": None},
            {"A15": "R0001"},
            {"D8": "Distance (km)"},
            {"B16": 46320},
            {"I15": None},
            {"I15": "Actaul"},
        ]
        for edits in variants:
            with self.subTest(edits=edits), tempfile.TemporaryDirectory() as tmp:
                workbook = Path(tmp) / "bad.xlsx"
                patched_xlsx(workbook, edits)
                result, output, _ = self.run_import(
                    workbook, initial='[{"last_good":true}]'
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Workbook validation failed", result.stderr)
                self.assertEqual(
                    output.read_text(encoding="utf-8"), '[{"last_good":true}]'
                )

    def test_reserved_blank_rows_are_skipped_and_fractional_minutes_are_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook = Path(tmp) / "seconds.xlsx"
            patched_xlsx(workbook, {"E14": 60.5})
            result, output, _ = self.run_import(workbook)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                next(r for r in rows if r["record_id"] == "R0001")["moving_time"],
                "1:00:30",
            )


if __name__ == "__main__":
    unittest.main()
