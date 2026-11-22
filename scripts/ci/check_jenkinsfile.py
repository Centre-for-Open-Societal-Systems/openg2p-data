#!/usr/bin/env python3
"""Guard the Jenkinsfile's scope: build and publish the db-seed image, never deploy.

    python scripts/ci/check_jenkinsfile.py [Jenkinsfile]

This repository's CI validates the data, builds the Master Data db-seed image
with it baked in and pushes that image to ECR. Seeding an environment (Master
Data, a registry, the services) from an image is a separate, approved
deployment that names an explicit image tag or digest. It is not something a
merge does as a side effect, and no parameter can turn it back on.

Checked:

  - no command that changes a cluster: helm upgrade/install/rollback/uninstall,
    kubectl, a kubeconfig, --reuse-values / --atomic
  - no stage that deploys or reseeds, and no parameter that would enable one
  - the only credentials bound are the ECR push ones
  - the image has the OAN name and tag standard (oan-helm naming-standard.md,
    section 6): eoan/openg2p-data/master-data-db-seed:<version>-<branch>.<build>,
    the tag taken from scripts/ci/image_names.py, not a commit-derived tag
  - the data and master-data-service commits stay in the image's OCI labels
  - the build and push stages run only for develop (not a pull request) and
    tags, with no parameter that widens that (the OAN standard never publishes
    a pull request or other branch build); the push stage runs
    scripts/ci/publish_gate.sh before any ECR call
  - the push never overwrites a published tag, and records the pushed reference
    (tag@digest) in dist/image.json for whoever deploys it

Comments are ignored, so the file can say what it does not do.
Exits non-zero on any failure.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ECR_REPOSITORY = "eoan/openg2p-data/master-data-db-seed"
LABELS = (
    "org.opencontainers.image.revision",
    "org.openg2p.master-data-service.revision",
    "org.openg2p.master-data-service.source",
)
ALLOWED_CREDENTIALS = {"AWS_ACCOUNT_ID", "aws-ecr-creds"}

# Code that reaches or changes a cluster. Matched against code, not comments.
FORBIDDEN_CODE = [
    (r"\bhelm\b[^\n]*\b(upgrade|install|rollback|uninstall|delete)\b", "runs helm against a release"),
    (r"\(\s*(upgrade|install|rollback)\b", "builds helm upgrade/install arguments"),
    (r"--reuse-values|--atomic|--dry-run=server", "uses release-changing helm flags"),
    (r"\bkubectl\b", "calls kubectl"),
    (r"(?i)kubeconfig", "uses a kubeconfig"),
    (r"\bfile\s*\(\s*credentialsId", "binds a secret file (kubeconfig) credential"),
]
FORBIDDEN_STAGE = re.compile(r"(?i)deploy|reseed|seed (dev|staging|prod)|rollout|upgrade")
FORBIDDEN_PARAM = re.compile(r"(?i)deploy|reseed|_DEV$|publish|rollout")


def strip_comments(text: str) -> str:
    """Blank // Groovy comments and whole-line # shell comments, keeping line numbers.

    A shebang ('#!/bin/bash') is kept; it is not prose. A '//' preceded by ':'
    is a URL, not a comment. /* */ is not stripped: shell globs such as
    packs/*/ would read as one.
    """
    out = []
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("//") or (s.startswith("#") and not s.startswith("#!")):
            out.append("")
            continue
        out.append(re.sub(r"(?<!:)//.*$", "", line))
    return "\n".join(out)


def stage_body(code: str, name: str) -> str | None:
    """Text of stage('<name>') up to the next stage( or the end."""
    m = re.search(r"stage\(\s*'" + re.escape(name) + r"'\s*\)", code)
    if not m:
        return None
    nxt = re.search(r"\n\s*stage\(", code[m.end():])
    return code[m.start(): m.end() + (nxt.start() if nxt else len(code))]


def check(path: str) -> list[str]:
    raw = open(path, encoding="utf-8").read()
    code = strip_comments(raw)
    errors = []

    for pattern, what in FORBIDDEN_CODE:
        for m in re.finditer(pattern, code):
            line = code.count("\n", 0, m.start()) + 1
            errors.append(f"line {line}: {what}: {m.group(0).strip()!r}")

    stages = re.findall(r"stage\(\s*'([^']+)'\s*\)", code)
    for name in stages:
        if FORBIDDEN_STAGE.search(name):
            errors.append(f"stage '{name}' deploys or reseeds; data CI only builds and publishes")

    params = re.findall(r"(?:string|booleanParam|choice|text|password)\s*\(\s*name:\s*'([^']+)'", code)
    params += re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*:", _block(code, "def PARAM_DEFAULTS"), flags=re.M)
    for name in sorted(set(params)):
        if FORBIDDEN_PARAM.search(name):
            errors.append(f"parameter {name} would let a build deploy or reseed")

    for cred in re.findall(r"credentialsId:\s*['\"]([^'\"]+)['\"]", code):
        if cred not in ALLOWED_CREDENTIALS:
            errors.append(f"binds credential {cred!r}; only {sorted(ALLOWED_CREDENTIALS)} are allowed")

    if not re.search(r"ECR_REPOSITORY\s*=\s*'" + re.escape(ECR_REPOSITORY) + "'", code):
        errors.append(f"ECR_REPOSITORY is not '{ECR_REPOSITORY}' (eoan/<repository>/<image>)")
    if not re.search(r"env\.IMAGE_TAG\s*=\s*sh\([^)]*scripts/ci/image_names\.py tag \"\$BRANCH_NAME\" \"\$BUILD_NUMBER\"", code, flags=re.S):
        errors.append("IMAGE_TAG is not taken from scripts/ci/image_names.py tag \"$BRANCH_NAME\" \"$BUILD_NUMBER\"")
    if re.search(r"env\.IMAGE_TAG\s*=[^\n]*(DATA_SHA|MDS_SHA)", code):
        errors.append("IMAGE_TAG is derived from a commit; the tag is <version>-<branch>.<build>, commits are labels")

    build = stage_body(code, "Build db-seed image")
    push = stage_body(code, "Push to ECR")
    if build is None:
        errors.append("no 'Build db-seed image' stage")
    else:
        when = re.search(r"when\s*\{(.*?)\n\s*\}\s*\n\s*steps", build, flags=re.S)
        errors += _gate_errors("'Build db-seed image'", when.group(1) if when else "")
        if "packs-image.diff" not in build:
            errors.append("'Build db-seed image' no longer proves the image's packs match the validated ones")
        for label in LABELS:
            if label not in build:
                errors.append(f"'Build db-seed image' no longer labels the image {label}")
    if push is None:
        errors.append("no 'Push to ECR' stage")
    else:
        when = re.search(r"when\s*\{(.*?)\n\s*\}\s*\n\s*steps", push, flags=re.S)
        gate = when.group(1) if when else ""
        errors += _gate_errors("'Push to ECR'", gate)
        first_aws = min((m.start() for m in re.finditer(r"aws", push)), default=len(push))
        gate_call = push.find("scripts/ci/publish_gate.sh")
        if gate_call < 0 or gate_call > first_aws:
            errors.append("'Push to ECR' does not run scripts/ci/publish_gate.sh before its first aws call")
        # The push may live in a script the stage calls; read those too.
        for script in re.findall(r"\bscripts/ci/[\w.-]+\.sh\b", push):
            p = os.path.join(ROOT, script)
            if os.path.isfile(p):
                push += "\n" + strip_comments(open(p, encoding="utf-8").read())
        if "describe-images" not in push:
            errors.append("'Push to ECR' does not check for an already published tag before pushing")
        if '"reference"' not in push:
            errors.append("'Push to ECR' does not record the pushed reference in dist/image.json")
    if stages and stages[-1] != "Push to ECR":
        errors.append(f"'{stages[-1]}' runs after 'Push to ECR'; publishing is the last thing CI does")
    return errors


PUBLISH_GATE = "anyOf { allOf { branch 'develop'; not { changeRequest() } }; buildingTag() }"


def _gate_errors(stage: str, gate: str) -> list[str]:
    """The stage's `when` must be develop (not a PR) or a tag, and nothing else."""
    if " ".join(gate.split()) != PUBLISH_GATE:
        extra = " (PUSH_IMAGE or another expression widens it)" if re.search(r"expression|PUSH_IMAGE", gate) else ""
        return [f"{stage} is not gated exactly on `{PUBLISH_GATE}`{extra}"]
    return []


def _block(code: str, opener: str) -> str:
    i = code.find(opener)
    if i < 0:
        return ""
    j = code.find("]", i)
    return code[i:j]


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else os.path.join(ROOT, "Jenkinsfile")
    errors = check(path)
    for e in errors:
        print(f"FAIL {e}")
    try:
        shown = os.path.relpath(path, ROOT)
    except ValueError:  # another drive on Windows
        shown = path
    if errors:
        print(f"{len(errors)} problem(s) in {shown}")
        return 1
    print(f"ok   {shown}: builds and publishes the db-seed image, deploys nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
