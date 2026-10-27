#!/usr/bin/env python3
"""Turn the geo-seed Helm hook into a one-off Job that seeds THIS repo's packs.

    helm template <release> <chart> -f <installed values> \\
        --set master-data.geoSeed.image.repository=<ecr repo> \\
        --set master-data.geoSeed.image.tag=<tag>@<digest> \\
        --show-only charts/master-data/templates/geo-seed-job.yaml \\
      | python seed_job_from_release.py --suffix ci-42 --pull-secret ecr-pull-secret

Why not `helm upgrade`: geo-seed is a post-install/post-upgrade hook of the
whole commons-services umbrella, so an upgrade to reseed geography also re-runs
every other Commons hook (IAM, Keycloak and database bootstrap) and touches a
release other services share. Rendering the hook from the installed chart and
values reseeds the same database the same way and leaves the release alone. The
loader upserts on level_value_id, so a rerun refreshes the pack in place.

The image: Jenkins builds a db-seed image with this commit's packs baked in,
pushes it to ECR and sets it at render time (--set ...geoSeed.image.*), so the
Job seeds exactly that image. --pull-secret adds the namespace's ECR pull
Secret, which the installed values do not carry for a Docker Hub image.

Alternatively, without an image build: --data-repo, --data-ref and
--packs-sha256 (all three) keep the image dev already runs and add an init
container that replaces its openg2p-data directory with one commit of this
repo, fetched by SHA. It checks the fetched packs hash to --packs-sha256 and
fails the Job, unseeded, if they do not.

Changes made to the rendered Job:
  - name gets --suffix, so it never collides with the release's own hook Job
  - helm.sh/hook* annotations are removed: applied by kubectl, they mean nothing
  - --pull-secret, if given, is added to the pod's imagePullSecrets
  - with --data-ref: an emptyDir over the image's openg2p-data directory,
    filled by the fetch-openg2p-data init container (same image, so no new pull)
  - ttlSecondsAfterFinished, so finished CI Jobs clean themselves up
  - restartPolicy Never and backoffLimit 0: one attempt, and a failed pod is
    kept (until the TTL) so its logs can be read. With the chart's OnFailure the
    container restarts in place, and the Job controller deletes that pod, logs
    and all, once the backoff limit is hit

The digest is the sha256 of `sha256sum` over every file under packs/, sorted
by path; see packs_digest.sh, which computes the same thing in CI.
"""

from __future__ import annotations

import argparse
import posixpath
import sys

import yaml

FETCH = """\
set -eu
cd "$OPENG2P_DATA_DIR"
git init -q
git remote add origin "$OPENG2P_DATA_REPO"
git fetch -q --depth 1 origin "$OPENG2P_DATA_REF"
git checkout -q FETCH_HEAD
echo "openg2p-data $(git rev-parse HEAD) from $OPENG2P_DATA_REPO"
rm -rf .git
actual=$(find packs -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
echo "packs sha256 $actual"
if [ "$actual" != "$EXPECTED_PACKS_SHA256" ]; then
  echo "packs differ from the ones CI validated ($EXPECTED_PACKS_SHA256); not seeding" >&2
  exit 1
fi
"""


def data_dir_of(container):
    """The image's openg2p-data directory, from the pack path the loader is given."""
    for arg in (container.get("args") or []) + (container.get("command") or []):
        if isinstance(arg, str) and "/packs/" in arg:
            return posixpath.dirname(posixpath.dirname(arg.rstrip("/")))
    sys.exit("the geo-seed container is given no .../packs/<pack> path")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suffix", required=True, help="appended to the Job name, e.g. ci-42")
    p.add_argument("--pull-secret", help="imagePullSecret to add to the pod, e.g. ecr-pull-secret")
    p.add_argument("--data-repo", help="openg2p-data git URL to fetch from (with --data-ref)")
    p.add_argument("--data-ref", help="commit SHA (or tag) to fetch over the image's packs")
    p.add_argument("--packs-sha256", help="digest the fetched packs must match (with --data-ref)")
    p.add_argument("--container", default="geo-seed", help="name of the loader container")
    p.add_argument("--ttl", type=int, default=86400, help="ttlSecondsAfterFinished")
    p.add_argument("--label", action="append", default=[], metavar="KEY=VALUE",
                   help="extra label on the Job and its pod (repeatable)")
    args = p.parse_args()
    fetch_args = (args.data_repo, args.data_ref, args.packs_sha256)
    if any(fetch_args) and not all(fetch_args):
        p.error("--data-repo, --data-ref and --packs-sha256 go together")

    docs = [d for d in yaml.safe_load_all(sys.stdin) if d]
    if len(docs) != 1 or docs[0].get("kind") != "Job":
        sys.exit(f"expected exactly one Job in the rendered template, got {[d.get('kind') for d in docs]}")
    job = docs[0]

    meta = job["metadata"]
    # Kubernetes names are at most 63 characters.
    base = meta["name"][: 63 - len(args.suffix) - 1].rstrip("-")
    meta["name"] = f"{base}-{args.suffix}"
    annotations = {k: v for k, v in (meta.get("annotations") or {}).items()
                   if not k.startswith("helm.sh/hook")}
    if annotations:
        meta["annotations"] = annotations
    else:
        meta.pop("annotations", None)

    extra = dict(kv.split("=", 1) for kv in args.label)
    pod_meta = job["spec"]["template"].setdefault("metadata", {})
    for m in (meta, pod_meta):
        m.setdefault("labels", {}).update(extra)

    spec = job["spec"]
    spec["ttlSecondsAfterFinished"] = args.ttl
    pod = spec["template"]["spec"]
    # Rerunning the build is the retry.
    spec["backoffLimit"] = 0
    pod["restartPolicy"] = "Never"
    seed = next((c for c in pod["containers"] if c["name"] == args.container), None)
    if seed is None:
        sys.exit(f"no container named {args.container} in the Job")

    if args.pull_secret:
        secrets = pod.setdefault("imagePullSecrets", [])
        if {"name": args.pull_secret} not in secrets:
            secrets.append({"name": args.pull_secret})

    if args.data_ref:
        add_fetch(pod, seed, args)

    yaml.safe_dump(job, sys.stdout, sort_keys=False)


def add_fetch(pod, seed, args):
    """Replace the image's openg2p-data directory with one fetched commit."""
    data_dir = data_dir_of(seed)
    pod.setdefault("volumes", []).append({"name": "openg2p-data", "emptyDir": {}})
    mount = {"name": "openg2p-data", "mountPath": data_dir}
    seed.setdefault("volumeMounts", []).append(mount)
    fetch = {
        "name": "fetch-openg2p-data",
        "image": seed["image"],
        "command": ["sh", "-c", FETCH],
        "env": [
            {"name": "OPENG2P_DATA_DIR", "value": data_dir},
            {"name": "OPENG2P_DATA_REPO", "value": args.data_repo},
            {"name": "OPENG2P_DATA_REF", "value": args.data_ref},
            {"name": "EXPECTED_PACKS_SHA256", "value": args.packs_sha256},
            {"name": "HOME", "value": "/tmp"},
        ],
        "volumeMounts": [mount],
    }
    if seed.get("imagePullPolicy"):
        fetch["imagePullPolicy"] = seed["imagePullPolicy"]
    # Last, so it runs after wait-for-postgres and immediately before the loader.
    pod.setdefault("initContainers", []).append(fetch)


if __name__ == "__main__":
    main()
