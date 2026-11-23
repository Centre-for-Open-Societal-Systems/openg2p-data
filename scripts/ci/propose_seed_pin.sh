#!/bin/bash
# Propose the seed image this build published as a pull request on oan-helm.
#
# Runs after the push, on develop builds only. It changes two lines of one file
# on the fixed branch bot/seed-image and opens (or updates) one pull request
# into main. A person reviews and merges it; nothing here merges, pushes to
# main, or touches a cluster.
#
# Needs: GH_USER and GH_TOKEN (Jenkins credential oan-helm-fork-token, bound
# for this stage only), DIST (dist/image.json from publish_image.sh), PYTHON.
# Optional: BUILD_URL, OAN_HELM_URL (tests point it at a local repository).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
OAN_HELM_URL="${OAN_HELM_URL:-https://github.com/Centre-for-Open-Societal-Systems/oan-helm.git}"
BRANCH="bot/seed-image"
VALUES="charts/openg2p-commons-services/values.yaml"
WORK="${WORK_DIR:-${DIST}/oan-helm}"

# Second line behind the stage's `when`: develop, never a pull request.
"${BASH:-bash}" "$HERE/publish_gate.sh"
if [ "${BRANCH_NAME:-}" != develop ] || [ -n "${TAG_NAME:-}" ] || [ -n "${CHANGE_ID:-}" ]; then
    echo "FAIL not proposing a pin: only a develop branch build does (branch '${BRANCH_NAME:-?}', tag '${TAG_NAME:-}')" >&2
    exit 1
fi

[ -s "$DIST/image.json" ] || { echo "no $DIST/image.json: nothing was published"; exit 1; }

# The token travels in the environment of git only, never on a command line.
if [ -n "${GH_TOKEN:-}" ]; then
    auth="$(printf '%s:%s' "$GH_USER" "$GH_TOKEN" | base64 | tr -d '\n')"
    export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraheader
    export GIT_CONFIG_VALUE_0="Authorization: Basic $auth"
fi

rm -rf "$WORK"
git clone --quiet --depth 1 --branch main "$OAN_HELM_URL" "$WORK"
cd "$WORK"
git config user.name "openg2p-data-ci"
git config user.email "openg2p-data-ci@users.noreply.github.com"

# Start from main every time, so the branch is always one commit on top of it.
git checkout --quiet -B "$BRANCH"

result="$("$PYTHON" "$HERE/seed_pin.py" rewrite "$VALUES" "$DIST/image.json")"
echo "$result"
case "$result" in
    changed) ;;
    *) echo "oan-helm main already has this pin or a newer one; no pull request needed."; exit 0 ;;
esac

# Only the chart's values file may change.
changed_files="$(git status --porcelain | awk '{print $2}')"
[ "$changed_files" = "$VALUES" ] || { echo "unexpected changes: $changed_files"; exit 1; }

tag="$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["deploy_values"]["master-data.geoSeed.image.tag"])' "$DIST/image.json")"
short="${tag%%@*}"
git commit --quiet -am "chore(commons): seed Master Data code lists from openg2p-data build ${short}"

"$PYTHON" - "$DIST/image.json" "${BUILD_URL:-}" > "$DIST/seed-pin-pr.md" <<'EOF'
import json, sys
info = json.load(open(sys.argv[1]))
v = info["deploy_values"]
print(f"""Dev reloads its Master Data code lists from `master-data.geoSeed.image` on every Commons services upgrade. This moves the pin to the latest openg2p-data develop build.

| | |
| --- | --- |
| Image | `{v['master-data.geoSeed.image.repository']}` |
| Tag and digest | `{v['master-data.geoSeed.image.tag']}` |
| openg2p-data commit | `{info.get('openg2p_data_commit')}` |
| Master Data service commit | `{info.get('master_data_service_commit')}` |
| Build | {sys.argv[2] or 'n/a'} |

Merging releases a new chart (`release.yaml`) and dev follows it. Dev loads code lists only (`geo: false`) and publishes changed lists at once. Staging keeps its own pin in `environments/staging/values/commons-services.yaml` and is not changed by this pull request.

Opened by the openg2p-data develop build after it published the image. It is the one standing pull request on `{'bot/seed-image'}`: a later build updates it instead of opening another. Nothing is merged or deployed by CI.""")
EOF

git push --quiet --force origin "$BRANCH"
GH_TOKEN="${GH_TOKEN:-}" "$PYTHON" "$HERE/seed_pin.py" pr "$DIST/seed-pin-pr.md"
