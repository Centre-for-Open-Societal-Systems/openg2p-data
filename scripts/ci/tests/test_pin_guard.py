"""check_jenkinsfile.py keeps the seed-pin stage to a pull request: python scripts/ci/tests/test_pin_guard.py

Each case edits a copy of the real Jenkinsfile (or one pin script) and expects the guard to refuse it.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CI = Path(__file__).resolve().parents[1]
ROOT = CI.parents[1]
sys.path.insert(0, str(CI))
import check_jenkinsfile  # noqa: E402


def problems(edit=None, script_edit=None):
    tmp = Path(tempfile.mkdtemp())
    text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
    if edit:
        new = edit(text)
        assert new != text, "the edit changed nothing"
        text = new
    jf = tmp / "Jenkinsfile"
    jf.write_text(text, encoding="utf-8")
    saved = None
    sh = CI / "update_seed_pin.sh"
    if script_edit:
        saved = sh.read_text(encoding="utf-8")
        sh.write_text(script_edit(saved), encoding="utf-8", newline="")
    try:
        return check_jenkinsfile.check(str(jf))
    finally:
        if saved is not None:
            sh.write_text(saved, encoding="utf-8", newline="")
        shutil.rmtree(tmp, ignore_errors=True)


class PinGuard(unittest.TestCase):
    def test_the_real_jenkinsfile_passes(self):
        self.assertEqual(problems(), [])

    def test_the_stage_is_required_and_last(self):
        self.assertTrue(problems(lambda t: t.replace("stage('Update seed pin in oan-helm')", "stage('Something else')")))

    def test_the_gate_cannot_widen_to_tags_or_other_branches(self):
        gate = "allOf { branch 'develop'; not { changeRequest() } }"
        self.assertTrue(problems(lambda t: t.replace("when {\n                " + gate + "\n            }", "when { anyOf { branch 'develop'; buildingTag() } }")))
        self.assertTrue(problems(lambda t: t.replace("when {\n                " + gate + "\n            }", "when { expression { true } }")))

    def test_the_token_cannot_be_bound_in_another_stage(self):
        extra = ("withCredentials([usernamePassword(credentialsId: 'oan-helm-fork-token', "
                 "usernameVariable: 'U', passwordVariable: 'P')]) { sh 'true' }\n                    script {\n                        env.ECR_REGISTRY")
        self.assertTrue(problems(lambda t: t.replace("script {\n                        env.ECR_REGISTRY", extra, 1)))

    def test_the_token_must_be_a_username_password_credential(self):
        self.assertTrue(problems(lambda t: t.replace("usernamePassword(credentialsId: 'oan-helm-fork-token',", "string(credentialsId: 'oan-helm-fork-token',")))

    def test_other_credentials_are_still_refused(self):
        self.assertTrue(problems(lambda t: t.replace("credentialsId: 'aws-ecr-creds'", "credentialsId: 'dev-kubeconfig'")))

    def test_the_script_cannot_merge_or_open_pull_requests(self):
        for text in ('curl -X PUT "$API/pulls/1/merge"', "gh pr merge 1", "gh pr create", "git merge origin/main"):
            self.assertTrue(problems(script_edit=lambda s, t=text: s + "\n" + t + "\n"), text)

    def test_the_one_allowed_push_is_exactly_a_plain_push_of_the_commit_to_main(self):
        push = "git push --quiet origin HEAD:main"
        self.assertEqual(problems(), [])
        for text in ("git push --quiet --force origin HEAD:main", "git push --quiet origin +HEAD:main",
                     "git push --quiet --force-with-lease origin HEAD:main", "git push --quiet origin HEAD:other",
                     "git push --quiet origin main", "git push --quiet origin --delete main",
                     "git push --quiet origin --tags"):
            self.assertTrue(problems(script_edit=lambda s, t=text: s.replace(push, t)), text)

    def test_a_second_push_is_refused(self):
        self.assertTrue(problems(script_edit=lambda s: s + "\ngit push --quiet origin HEAD:main\n"))

    def test_the_script_cannot_call_a_web_api(self):
        for text in ("curl -s https://api.github.com/user", "wget http://x", "python -c 'import urllib.request'"):
            self.assertTrue(problems(script_edit=lambda s, t=text: s + "\n" + t + "\n"), text)

    def test_the_script_cannot_touch_a_cluster(self):
        self.assertTrue(problems(script_edit=lambda s: s + "\nkubectl get pods\n"))

    def test_only_a_default_master_data_ref_is_pinned(self):
        self.assertTrue(problems(lambda t: t.replace("MDS_REF_DEFAULT=${PARAM_DEFAULTS.MDS_REF}", "MDS_REF_DEFAULT=x")))
        self.assertTrue(problems(script_edit=lambda s: s.replace("MDS_REF_DEFAULT", "OTHER")))

    def test_the_script_keeps_the_gate(self):
        self.assertTrue(problems(script_edit=lambda s: s.replace("publish_gate.sh", "x.sh")))


if __name__ == "__main__":
    unittest.main(verbosity=1)
