#!/bin/bash
# Move oan-helm's seed image pin to the image this build published.
#
# Runs after the push, on develop builds only. It commits two files straight to
# oan-helm main as one fast-forward commit: the pin in the commons-services chart
# values, and the release record oan-helm's contract test reads. There is no pull
# request. oan-helm's own gates then decide whether it goes anywhere: its checks
# run on the commit, its release workflow only releases a chart whose tests pass,
# and New Dev is delivered only from a commit whose checks are green. Nothing here
# deploys, merges, force-pushes, or touches a cluster.
#
# Needs: GH_USER and GH_TOKEN (Jenkins credential oan-helm-fork-token, bound for
# this stage only), DIST (dist/image.json from publish_image.sh), PYTHON.
# Optional: BUILD_URL, OAN_HELM_URL and RETRY_SLEEP (tests point the first at a local repository, the second at 0).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
OAN_HELM_URL="${OAN_HELM_URL:-https://github.com/Centre-for-Open-Societal-Systems/oan-helm.git}"
VALUES="charts/openg2p-commons-services/values.yaml"
WORK="${WORK_DIR:-${DIST}/oan-helm}"
ATTEMPTS=4

# Second line behind the stage's `when`: develop, never a pull request.
"${BASH:-bash}" "$HERE/publish_gate.sh"
if [ "${BRANCH_NAME:-}" != develop ] || [ -n "${TAG_NAME:-}" ] || [ -n "${CHANGE_ID:-}" ]; then
    echo "FAIL not updating the pin: only a develop branch build does (branch '${BRANCH_NAME:-?}', tag '${TAG_NAME:-}')" >&2
    exit 1
fi

[ -s "$DIST/image.json" ] || { echo "no $DIST/image.json: nothing was published"; exit 1; }

# The image's Master Data base must be the one New Dev runs: only a build on the default
# MDS_REF is pinned. A manual build with another MDS_REF is published but never pinned.
image_ref="$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("master_data_service_ref") or "")' "$DIST/image.json")"
if [ -z "${MDS_REF_DEFAULT:-}" ] || [ "${MDS_REF:-}" != "$MDS_REF_DEFAULT" ] || [ "$image_ref" != "$MDS_REF_DEFAULT" ]; then
    echo "not pinning: this build's Master Data ref (build '${MDS_REF:-}', image '$image_ref') is not the default '${MDS_REF_DEFAULT:-unset}'"
    exit 0
fi

# The token travels in the environment of git only, never on a command line.
if [ -n "${GH_TOKEN:-}" ]; then
    auth="$(printf '%s:%s' "$GH_USER" "$GH_TOKEN" | base64 | tr -d '\n')"
    export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraheader
    export GIT_CONFIG_VALUE_0="Authorization: Basic $auth"
fi

tag="$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["deploy_values"]["master-data.geoSeed.image.tag"])' "$DIST/image.json")"
short="${tag%%@*}"

attempt=1
while :; do
    # A fresh checkout of main each time: the release workflow also commits to main,
    # so a rejected push is retried on top of whatever landed meanwhile.
    rm -rf "$WORK"
    git clone --quiet --depth 1 --branch main "$OAN_HELM_URL" "$WORK"
    cd "$WORK"
    git config user.name "openg2p-data-ci"
    git config user.email "openg2p-data-ci@users.noreply.github.com"

    result="$("$PYTHON" "$HERE/seed_pin.py" rewrite "$VALUES" "$DIST/image.json")"
    echo "$result"
    case "$result" in
        changed) ;;
        *) echo "oan-helm main already has this pin or a newer one; nothing to commit."; exit 0 ;;
    esac

    # oan-helm's contract test compares the chart's seed image with the newest release
    # record, so the commit carries one: releases/1.0.0-dev.<chart version + 1>.yaml.
    record="$("$PYTHON" "$HERE/seed_pin.py" record . "$DIST/image.json" "${BUILD_URL:-}")"
    git add -- "$record"

    # Only the chart's values file and that one new release record may change.
    changed_files="$(git status --porcelain | awk '{print $2}' | sort | paste -sd' ' -)"
    expected="$(printf '%s\n%s\n' "$VALUES" "$record" | sort | paste -sd' ' -)"
    [ "$changed_files" = "$expected" ] || { echo "unexpected changes: $changed_files (expected $expected)"; exit 1; }

    "$PYTHON" "$HERE/seed_pin.py" message "$DIST/image.json" "${BUILD_URL:-}" > "$DIST/seed-pin-commit.txt"
    git commit --quiet -a -F "$DIST/seed-pin-commit.txt"

    # A plain push: if main moved it is rejected, never overwritten.
    if git push --quiet origin HEAD:main; then
        echo "pinned ${short} on oan-helm main: $(git rev-parse --short HEAD)"
        exit 0
    fi
    if [ "$attempt" -ge "$ATTEMPTS" ]; then
        echo "FAIL: oan-helm main kept moving; gave up after $ATTEMPTS attempts" >&2
        exit 1
    fi
    echo "oan-helm main moved; retrying ($attempt of $ATTEMPTS)"
    attempt=$((attempt + 1))
    cd "$HERE"
    sleep $((attempt * ${RETRY_SLEEP:-3}))
done
