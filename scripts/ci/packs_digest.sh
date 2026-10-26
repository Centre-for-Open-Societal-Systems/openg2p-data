#!/bin/bash
# Digest of the committed packs: sha256 of `sha256sum` over every tracked file
# under packs/, sorted by path.
#
#   packs_digest.sh            # run from the repo root
#
# The fetch-openg2p-data init container (seed_job_from_release.py --data-ref,
# the no-image-build alternative) computes the same thing over its checkout and
# refuses to seed when the two disagree, so the database gets exactly the packs
# CI validated. Keep the two in step.
set -euo pipefail
git ls-files -z packs | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1
