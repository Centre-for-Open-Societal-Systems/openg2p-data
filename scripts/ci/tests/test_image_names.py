"""Tag generation of scripts/ci/image_names.py: python scripts/ci/tests/test_image_names.py"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import image_names


class Names(unittest.TestCase):
    def init(self, text):
        d = tempfile.mkdtemp()
        p = Path(d) / "init.yaml"
        p.write_text(text, encoding="utf-8")
        return p

    def test_repository_is_the_eoan_path(self):
        self.assertEqual(image_names.REPOSITORY, "eoan/openg2p-data/master-data-db-seed")

    def test_develop_build(self):
        self.assertEqual(image_names.tag("develop", "57"), image_names.version() + "-develop.57")

    def test_pull_request_build(self):
        self.assertTrue(image_names.tag("PR-75", 3).endswith("-pr-75.3"))

    def test_branch_slug(self):
        self.assertTrue(image_names.tag("fix/Roster_List", "3").endswith("-fix-roster-list.3"))

    def test_tag_is_not_a_commit_scheme(self):
        t = image_names.tag("develop", "1")
        self.assertNotIn("-mds-", t)
        self.assertRegex(t, r"^\d+\.\d+\.\d+-[a-z0-9-]+\.[1-9]\d*$")

    def test_rejects_bad_build_or_branch(self):
        for branch, build in (("develop", "0"), ("develop", "x"), ("develop", ""), ("///", "1"), ("", "1")):
            with self.assertRaises(ValueError):
                image_names.tag(branch, build)

    def test_init_yaml_errors(self):
        for text in ("", "version: 1.0\n", "version: 1.0.0\nversion: 1.0.1\n", "other: 1\n"):
            with self.assertRaises(ValueError):
                image_names.version(self.init(text))
        self.assertEqual(image_names.version(self.init('# c\nversion: "2.1.3"  # x\n')), "2.1.3")

    def test_cli(self):
        run = lambda *a: subprocess.run([sys.executable, str(CI / "image_names.py"), *a], capture_output=True, text=True, check=False)
        self.assertEqual(run("repository").stdout.strip(), image_names.REPOSITORY)
        self.assertEqual(run("tag", "develop", "7").stdout.strip(), image_names.version() + "-develop.7")
        self.assertNotEqual(run("tag", "develop", "0").returncode, 0)


if __name__ == "__main__":
    unittest.main()
