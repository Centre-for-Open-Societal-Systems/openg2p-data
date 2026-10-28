import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/packs"))
from validate_pack import Report, check_samples


class FarmerSamples(unittest.TestCase):
    def check_case(self, mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            pack = Path(directory) / "ETH-OAN"
            pack.mkdir()
            for folder in ("samples", "codelists"):
                shutil.copytree(ROOT / "packs/ETH-OAN" / folder, pack / folder)
            shutil.copy(ROOT / "packs/ETH-OAN/address.json", pack / "address.json")
            shutil.copy(ROOT / "packs/ETH-OAN/levels.json", pack / "levels.json")
            path = pack / "samples/individuals.json"
            people = json.loads(path.read_text(encoding="utf-8"))
            if mutate:
                mutate(people)
                path.write_text(json.dumps(people), encoding="utf-8")
            geo = {v["level_value_id"] for v in json.loads((ROOT / "packs/ETH-OAN/values.json").read_text(encoding="utf-8"))}
            report = Report("ETH-OAN")
            check_samples(str(pack), report, geo)
            return report.errors

    def test_current_samples(self):
        self.assertEqual(self.check_case(), [])

    def test_missing_third_name(self):
        errors = self.check_case(lambda p: p[0].update(full_name=p[0]["given_name"] + " " + p[0]["fathers_name"]))
        self.assertTrue(any("three-part" in e for e in errors))

    def test_invalid_identity(self):
        errors = self.check_case(lambda p: p[0].update(national_id="bad"))
        self.assertTrue(any("12-digit" in e for e in errors))

    def test_duplicate_identity(self):
        errors = self.check_case(lambda p: p[0].update(national_id=p[1]["national_id"]))
        self.assertTrue(any("duplicates" in e for e in errors))

    def test_missing_birth_date(self):
        errors = self.check_case(lambda p: p[0].update(birth_date=None))
        self.assertTrue(any("needs birth_date" in e for e in errors))
