#!/bin/bash
# Digest of the committed packs: sha256 of `sha256sum` over every tracked file
# under packs/, sorted by path.
#
#   packs_digest.sh            # run from the repo root
#
# Jenkins compares this digest with the one computed over the image's packs,
# so the database gets exactly the packs CI validated.
set -euo pipefail
git ls-files -z packs | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1
