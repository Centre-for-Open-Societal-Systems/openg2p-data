#!/bin/bash
# Pull one exact chart package from the oan-helm repository and verify it.
#
#   pull_verified_chart.sh <chart> <version> <dest-dir>
#
# Expects `helm repo add oan $HELM_REPO_URL` to have run, and $TOOLS/bin/helm.
# The archive is checked against the repository's own published SHA256SUMS
# before anything parses it, as oan-helm's docs require of every consumer.
set -euo pipefail

chart=$1 version=$2 dest=$3
archive="$chart-$version.tgz"
mkdir -p "$dest"
rm -f "$dest/$archive"

"$TOOLS/bin/helm" pull "oan/$chart" --version "$version" -d "$dest"

curl -sSfL "$HELM_REPO_URL/SHA256SUMS" > "$dest/SHA256SUMS"
# Lines are "<sha>  <file>" or "<sha> *<file>"; match the filename exactly.
awk -v f="$archive" '{ n = $2; sub(/^\*/, "", n); if (n == f) print $1 "  " f }' \
    "$dest/SHA256SUMS" > "$dest/expected.sha256"
[ -s "$dest/expected.sha256" ] || { echo "$archive is not listed in $HELM_REPO_URL/SHA256SUMS"; exit 1; }
(cd "$dest" && sha256sum -c expected.sha256)
