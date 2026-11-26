"""The oan-helm seed-pin update: python scripts/ci/tests/test_seed_pin.py

Unit tests for the file edits, and an end-to-end run of update_seed_pin.sh against a local
git repository standing in for oan-helm. No network, no real credentials.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import seed_pin  # noqa: E402

# On Windows `bash` on PATH can be WSL; Git for Windows ships the one these scripts are written for.
BASH = next((b for b in ("C:/Program Files/Git/usr/bin/bash.exe",) if os.name == "nt" and os.path.exists(b)), "bash")
# LF in, LF out: the Linux agent has no autocrlf, and these tests compare bytes.
os.environ.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.autocrlf", GIT_CONFIG_VALUE_0="false")

REPO = seed_pin.SEED_REPOSITORY
OLD = "1.0.0-develop.67@sha256:" + "a" * 64
NEW = "1.0.0-develop.70@sha256:" + "b" * 64
BASE = "openg2p/master-data-db-seed:0.0.0-develop.118@sha256:" + "e" * 64
PREVIOUS_RECORD = f"""chartVersion: 1.0.0-dev.51
charts:
- name: openg2p-commons-services
  masterDataImageVersion: 0.0.0-develop.118
  masterDataSeedImage:
    repository: {REPO}
    tag: 1.0.0-develop.67
    digest: sha256:{"a" * 64}
    base: {BASE}
"""
VALUES = f"""master-data:
  geoSeed:
    countryPack: ETH-OAN
    image:
      repository: {REPO}
      tag: {OLD}
    enabled: false
  other:
    image:
      repository: example/other
      tag: keep
"""
VALUES_PATH = "charts/openg2p-commons-services/values.yaml"
MDS = "e569a59b8e9f61f809e07791e9263e50b2a7e0da"


def image_json(tag=NEW, repository=REPO):
    return {"deploy_values": {"master-data.geoSeed.image.repository": repository,
                              "master-data.geoSeed.image.tag": tag},
            "openg2p_data_commit": "c" * 40, "master_data_service_commit": "d" * 40,
            "master_data_service_ref": MDS}


class Rewrite(unittest.TestCase):
    def test_changes_only_the_two_lines(self):
        out = seed_pin.set_pin(VALUES, REPO, NEW)
        self.assertEqual(out, VALUES.replace(OLD, NEW))
        self.assertIn("tag: keep", out)

    def test_same_pin_is_unchanged(self):
        self.assertEqual(seed_pin.set_pin(VALUES, REPO, OLD), VALUES)

    def test_rejects_another_repository_or_a_bad_tag(self):
        with self.assertRaises(ValueError):
            seed_pin.set_pin(VALUES, "example/other", NEW)
        for bad in ("latest", "1.0.0-develop.70", "1.0.0-develop.70@sha256:abc", "f929965ce2a9-mds-e569a59b@sha256:" + "a" * 64):
            with self.assertRaises(ValueError):
                seed_pin.set_pin(VALUES, REPO, bad)

    def test_needs_exactly_one_block(self):
        with self.assertRaises(ValueError):
            seed_pin.set_pin("master-data:\n  other: 1\n", REPO, NEW)
        with self.assertRaises(ValueError):
            seed_pin.set_pin(VALUES + VALUES, REPO, NEW)

    def test_an_older_build_does_not_move_the_pin_back(self):
        d = tempfile.mkdtemp()
        v, j = Path(d, "values.yaml"), Path(d, "image.json")
        v.write_bytes(VALUES.replace(OLD, NEW).encode())
        j.write_text(json.dumps(image_json(tag=OLD)), encoding="utf-8")
        self.assertEqual(seed_pin.cmd_rewrite(str(v), str(j)), 0)
        self.assertIn(NEW, v.read_text(encoding="utf-8"))


    def test_a_higher_version_moves_the_pin_even_with_a_lower_build_number(self):
        # A recreated job restarts BUILD_NUMBER at 1; init.yaml's version is bumped to stay ahead.
        before = "1.0.1-develop.75@sha256:" + "a" * 64
        after = "1.0.2-develop.3@sha256:" + "b" * 64
        d = tempfile.mkdtemp()
        v, j = Path(d, "values.yaml"), Path(d, "image.json")
        v.write_bytes(VALUES.replace(OLD, before).encode())
        j.write_text(json.dumps(image_json(tag=after)), encoding="utf-8")
        self.assertEqual(seed_pin.cmd_rewrite(str(v), str(j)), 0)
        self.assertIn(after, v.read_text(encoding="utf-8"))
        # and the older version cannot take it back, whatever its build number
        j.write_text(json.dumps(image_json(tag=before)), encoding="utf-8")
        self.assertEqual(seed_pin.cmd_rewrite(str(v), str(j)), 0)
        self.assertIn(after, v.read_text(encoding="utf-8"))

def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        seed = self.tmp / "seed"
        (seed / "charts/openg2p-commons-services").mkdir(parents=True)
        (seed / VALUES_PATH).write_bytes(VALUES.encode())
        (seed / "charts/openg2p-commons-services/Chart.yaml").write_bytes(b"name: x\nversion: 1.0.0-dev.51\n")
        (seed / "releases").mkdir()
        (seed / "releases/1.0.0-dev.51.yaml").write_bytes(PREVIOUS_RECORD.encode())
        (seed / "releases/1.0.0-dev.40.yaml").write_bytes(b"chartVersion: 1.0.0-dev.40\ncharts: []\n")
        subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
        ident = ["-c", "user.name=t", "-c", "user.email=t@t"]
        git(*ident, "add", "-A", cwd=seed)
        git(*ident, "commit", "-q", "-m", "init", cwd=seed)
        self.remote = self.tmp / "oan-helm.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(self.remote)], check=True)
        self.dist = self.tmp / "dist"
        self.dist.mkdir()
        (self.dist / "image.json").write_text(json.dumps(image_json()), encoding="utf-8")

    def run_script(self, branch="develop", change_id=None, tag_name=None, mds_ref=MDS, default=MDS):
        env = dict(os.environ, DIST=str(self.dist), PYTHON=sys.executable, BRANCH_NAME=branch,
                   BUILD_NUMBER="70", JENKINS_URL="http://j/", JOB_NAME="x", BUILD_URL="http://j/job/70/",
                   OAN_HELM_URL=self.remote.as_posix(), WORK_DIR=str(self.tmp / "work"), GH_USER="bot", GH_TOKEN="", RETRY_SLEEP="0", MDS_REF=mds_ref, MDS_REF_DEFAULT=default)
        for k in ("CHANGE_ID", "TAG_NAME"):
            env.pop(k, None)
        if change_id:
            env["CHANGE_ID"] = change_id
        if tag_name:
            env["TAG_NAME"] = tag_name
        return subprocess.run([BASH, str(CI / "update_seed_pin.sh")], env=env, capture_output=True, text=True)

    def remote_git(self, *args):
        return subprocess.run(["git", "--git-dir", str(self.remote), *args], capture_output=True, text=True).stdout

    def commits(self):
        return int(self.remote_git("rev-list", "--count", "main").strip())

    def test_commits_straight_to_main_and_nothing_else(self):
        before = self.commits()
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before + 1, "exactly one new commit on main")
        self.assertEqual(self.remote_git("branch", "--list").split(), ["*", "main"] if "*" in self.remote_git("branch", "--list") else ["main"])
        self.assertEqual(sorted(self.remote_git("diff", "--name-only", "HEAD~1", "HEAD").split()),
                         [VALUES_PATH, "releases/1.0.0-dev.52.yaml"])
        self.assertEqual(self.remote_git("show", f"main:{VALUES_PATH}"), VALUES.replace(OLD, NEW))
        rec = self.remote_git("show", "main:releases/1.0.0-dev.52.yaml")
        self.assertIn("chartVersion: 1.0.0-dev.52", rec)
        self.assertIn("    tag: 1.0.0-develop.70\n", rec)
        self.assertIn("    digest: sha256:" + "b" * 64 + "\n", rec)
        self.assertIn(f"    base: {BASE}\n", rec)
        self.assertIn("  masterDataImageVersion: 0.0.0-develop.118\n", rec)
        msg = self.remote_git("log", "-1", "--format=%an <%ae>%n%B", "main")
        self.assertIn("oan-seed-pinner", msg)
        self.assertIn("1.0.0-develop.70", msg)
        self.assertIn("sha256:" + "b" * 64, msg)
        self.assertIn("http://j/job/70/", msg)

    def test_a_build_on_another_master_data_ref_is_published_but_never_pinned(self):
        before = self.commits()
        # a manual build with another MDS_REF
        r = self.run_script(mds_ref="f" * 40)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("not pinning", r.stdout)
        self.assertEqual(self.commits(), before)
        # an image that was built on another ref than the build says
        info = image_json()
        info["master_data_service_ref"] = "f" * 40
        (self.dist / "image.json").write_text(json.dumps(info), encoding="utf-8")
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.commits(), before)
        # no default given: nothing is pinned
        (self.dist / "image.json").write_text(json.dumps(image_json()), encoding="utf-8")
        self.assertEqual(self.run_script(default="").returncode, 0)
        self.assertEqual(self.commits(), before)

    def test_a_pin_already_on_main_commits_nothing(self):
        (self.dist / "image.json").write_text(json.dumps(image_json(tag=OLD)), encoding="utf-8")
        before = self.commits()
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.commits(), before)

    def test_a_second_run_of_the_same_build_commits_nothing(self):
        self.assertEqual(self.run_script().returncode, 0)
        after_first = self.commits()
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.commits(), after_first)

    def test_a_rejected_push_is_retried_on_top_of_the_new_main(self):
        hook = self.remote / "hooks" / "pre-receive"
        counter = (self.tmp / "pushes").as_posix()
        hook.write_text(f'#!/bin/sh\nn=$(cat "{counter}" 2>/dev/null || echo 0)\necho $((n+1)) > "{counter}"\n'
                        '[ "$n" -ge 1 ] || { echo rejected; exit 1; }\n', encoding="utf-8", newline="")
        hook.chmod(0o755)
        before = self.commits()
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("retrying", r.stdout)
        self.assertEqual(self.commits(), before + 1)

    def test_it_gives_up_instead_of_overwriting(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho rejected\nexit 1\n", encoding="utf-8", newline="")
        hook.chmod(0o755)
        before = self.commits()
        r = self.run_script()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.commits(), before)

    def test_a_pull_request_tag_or_feature_branch_build_does_nothing(self):
        before = self.commits()
        for kwargs in ({"branch": "feature/x"}, {"change_id": "75"}, {"branch": "PR-75", "change_id": "75"},
                       {"tag_name": "1.0.0"}):
            self.assertNotEqual(self.run_script(**kwargs).returncode, 0, kwargs)
        self.assertEqual(self.commits(), before)

    def test_an_existing_record_is_never_overwritten(self):
        # Two bumps before the release workflow has run: the record for the next version is
        # already there, so this bump takes the one after it.
        seed = self.tmp / "seed"
        existing = b"chartVersion: 1.0.0-dev.52\ncharts: []\n"
        (seed / "releases/1.0.0-dev.52.yaml").write_bytes(existing)
        ident = ["-c", "user.name=t", "-c", "user.email=t@t"]
        git(*ident, "add", "-A", cwd=seed)
        git(*ident, "commit", "-q", "-m", "a record that is already there", cwd=seed)
        git("push", "-q", str(self.remote), "main", cwd=seed)
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.remote_git("show", "main:releases/1.0.0-dev.52.yaml").encode(), existing)
        self.assertIn("chartVersion: 1.0.0-dev.53", self.remote_git("show", "main:releases/1.0.0-dev.53.yaml"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
