"""The ECR name of the Master Data seed image, in the OAN standard (oan-helm docs/release/naming-standard.md, section 6).

    eoan/<repository>/<image>:<version>-<branch slug>.<BUILD_NUMBER>

    eoan/openg2p-data/master-data-db-seed:1.0.0-develop.57

<repository> is the GitHub repository that builds the image (openg2p-data), <image> the component (master-data-db-seed;
it is not an OpenG2P registry-platform role, so it has no -<rpVersion> suffix). <version> is in init.yaml at the root of
this repository. <branch slug> is Jenkins' BRANCH_NAME lower-cased with every run of other characters as '-', so a pull
request build (BRANCH_NAME PR-75) is 1.0.0-pr-75.3, and <BUILD_NUMBER> is the Jenkins build number of that job. A tag
carries no commit: the openg2p-data commit and the master-data-service commit are the image's OCI labels and are
recorded with the digest in dist/image.json.

    image_names.py tag <branch> <build>     the image tag of a build
    image_names.py repository               the ECR repository, without the registry host

Standard library only: it runs on the Jenkins agent's stock Python.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "init.yaml"
REPOSITORY = "eoan/openg2p-data/master-data-db-seed"
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
LINE = re.compile(r"^version\s*:\s*(\"[^\"]*\"|'[^']*'|[^#\s]+)\s*(?:#.*)?$")


def version(path=None):
    """`version` of init.yaml: flat `version: N.N.N` plus comments, nothing else."""
    found = None
    for number, line in enumerate(Path(path or INIT).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = LINE.match(line)
        if not match or found is not None:
            raise ValueError(f"init.yaml line {number}: expected a single `version: N.N.N`")
        found = match.group(1).strip("\"'")
    if found is None or not VERSION.fullmatch(found):
        raise ValueError("init.yaml: version is missing or not N.N.N")
    return found


def tag(branch, build, path=None):
    slug = re.sub(r"[^a-z0-9]+", "-", str(branch).lower()).strip("-")
    if not slug or not re.fullmatch(r"[1-9]\d*", str(build)):
        raise ValueError("an image tag needs a branch and a build number")
    return f"{version(path)}-{slug}.{build}"


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "tag":
            print(tag(sys.argv[2], sys.argv[3]))
        elif len(sys.argv) == 2 and sys.argv[1] == "repository":
            print(REPOSITORY)
        else:
            sys.exit("usage: image_names.py tag <branch> <build> | repository")
    except (ValueError, OSError) as error:
        sys.exit(f"FAIL: {error}")
