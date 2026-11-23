"""The oan-helm seed-pin proposal: python scripts/ci/tests/test_seed_pin.py

Unit tests for the values.yaml rewrite, and an end-to-end run of
propose_seed_pin.sh against a local git repository standing in for oan-helm
and a fake GitHub API. No network, no real credentials.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import seed_pin  # noqa: E402

# LF in, LF out: the Linux agent has no autocrlf, and these tests compare bytes.
os.environ.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.autocrlf", GIT_CONFIG_VALUE_0="false")

# On Windows `bash` on PATH can be WSL; Git for Windows ships the one these scripts are written for.
BASH = next((b for b in ("C:/Program Files/Git/usr/bin/bash.exe",) if os.name == "nt" and os.path.exists(b)), "bash")

REPO = seed_pin.SEED_REPOSITORY
OLD = "1.0.0-develop.67@sha256:" + "a" * 64
NEW = "1.0.0-develop.70@sha256:" + "b" * 64
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


def image_json(tag=NEW, repository=REPO):
    return {"deploy_values": {"master-data.geoSeed.image.repository": repository,
                              "master-data.geoSeed.image.tag": tag},
            "openg2p_data_commit": "c" * 40, "master_data_service_commit": "d" * 40}


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


class Fake(BaseHTTPRequestHandler):
    calls = []
    open_pr = False

    def log_message(self, format, *args):
        pass

    def _send(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        Fake.calls.append(("GET", self.path))
        self._send([{"number": 9}] if Fake.open_pr else [])

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_POST(self):
        Fake.calls.append(("POST", self.path, self._body()))
        self._send({"number": 12})

    def do_PATCH(self):
        Fake.calls.append(("PATCH", self.path, self._body()))
        self._send({"number": 9})


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.remote = self.tmp / "oan-helm.git"
        seed = self.tmp / "seed"
        (seed / "charts/openg2p-commons-services").mkdir(parents=True)
        (seed / "charts/openg2p-commons-services/values.yaml").write_bytes(VALUES.encode())
        subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
        git("-c", "user.name=t", "-c", "user.email=t@t", "add", "-A", cwd=seed)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init", cwd=seed)
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(self.remote)], check=True)
        self.dist = self.tmp / "dist"
        self.dist.mkdir()
        (self.dist / "image.json").write_text(json.dumps(image_json()), encoding="utf-8")
        Fake.calls = []
        Fake.open_pr = False
        self.server = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()

    def run_script(self, branch="develop", change_id=None):
        env = dict(os.environ, DIST=str(self.dist), PYTHON=sys.executable, BRANCH_NAME=branch,
                   BUILD_NUMBER="70", JENKINS_URL="http://j/", JOB_NAME="x", BUILD_URL="http://j/job/70/",
                   OAN_HELM_URL=self.remote.as_posix(), WORK_DIR=str(self.tmp / "work"),
                   GH_USER="bot", GH_TOKEN="", GITHUB_API=f"http://127.0.0.1:{self.server.server_port}")
        env.pop("CHANGE_ID", None)
        if change_id:
            env["CHANGE_ID"] = change_id
        return subprocess.run([BASH, str(CI / "propose_seed_pin.sh")], env=env, capture_output=True, text=True)

    def branch_tip(self, name):
        r = subprocess.run(["git", "--git-dir", str(self.remote), "rev-parse", "--verify", "-q", name],
                           capture_output=True, text=True)
        return r.stdout.strip()

    def test_opens_one_pull_request_and_touches_only_the_bot_branch(self):
        main_before = self.branch_tip("main")
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.branch_tip("main"), main_before, "main must not move")
        self.assertTrue(self.branch_tip("bot/seed-image"))
        shown = subprocess.run(["git", "--git-dir", str(self.remote), "show", "bot/seed-image:charts/openg2p-commons-services/values.yaml"],
                               capture_output=True).stdout.decode()
        self.assertEqual(shown, VALUES.replace(OLD, NEW))
        posts = [c for c in Fake.calls if c[0] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][1], f"/repos/{seed_pin.REPO}/pulls")
        self.assertEqual((posts[0][2]["head"], posts[0][2]["base"]), ("bot/seed-image", "main"))
        self.assertIn(NEW, posts[0][2]["body"])
        self.assertFalse([c for c in Fake.calls if "merge" in c[1]], "no merge call")

    def test_updates_the_open_pull_request_instead_of_opening_another(self):
        Fake.open_pr = True
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([c[0] for c in Fake.calls if c[0] != "GET"], ["PATCH"])

    def test_a_pin_already_on_main_opens_nothing(self):
        (self.dist / "image.json").write_text(json.dumps(image_json(tag=OLD)), encoding="utf-8")
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(Fake.calls, [])
        self.assertFalse(self.branch_tip("bot/seed-image"))

    def test_a_pull_request_or_feature_branch_build_does_nothing(self):
        for branch, change in (("feature/x", None), ("develop", "75"), ("PR-75", "75")):
            r = self.run_script(branch=branch, change_id=change)
            self.assertNotEqual(r.returncode, 0, branch)
        self.assertEqual(Fake.calls, [])
        self.assertFalse(self.branch_tip("bot/seed-image"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
