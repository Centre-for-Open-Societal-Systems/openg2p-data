#!/bin/bash
# Behaviour of scripts/ci/publish_image.sh against fake `aws` and `docker`:
# nothing here reaches AWS or a Docker daemon.
#
#   bash scripts/ci/tests/test_publish_image.sh
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$HERE/../publish_image.sh"
REPO=123456789012.dkr.ecr.ap-south-1.amazonaws.com/eoan/openg2p-data/master-data-db-seed
LOCAL=openg2p-data-ci/master-data-db-seed:1.0.0-develop.57
TAG=1.0.0-develop.57
fails=0

# Fake ECR: $STATE/tags/<tag> holds the digest a tag names. Fake docker: `tag`
# remembers the source, `push` publishes it (a local image gets sha256:local, a
# pulled repo@digest keeps its digest). Every push is logged.
make_fakes() {
    mkdir -p "$1/bin" "$1/tags" "$1/src"
    cat > "$1/bin/aws" <<'EOF'
#!/bin/bash
[ -n "${FAKE_AWS_DENY:-}" ] && { echo "An error occurred (AccessDeniedException) when calling the DescribeImages operation" >&2; exit 254; }
for a in "$@"; do case $a in imageTag=*) t=${a#imageTag=};; esac; done
f="$STATE/tags/$(tr '/:' '__' <<< "$t")"
[ -f "$f" ] && { cat "$f"; exit 0; }
echo "An error occurred (ImageNotFoundException) when calling the DescribeImages operation" >&2; exit 254
EOF
    cat > "$1/bin/docker" <<'EOF'
#!/bin/bash
key() { tr '/:@' '___' <<< "$1"; }
case $1 in
  tag)  echo "$2" > "$STATE/src/$(key "$3")" ;;
  pull) echo "pull $2" >> "$STATE/log" ;;
  push) src=$(cat "$STATE/src/$(key "$2")")
        case $src in *@sha256:*) d=${src#*@} ;; *) d=sha256:local ;; esac
        echo "$d" > "$STATE/tags/$(tr '/:' '__' <<< "${2##*:}")"
        echo "push $2" >> "$STATE/log" ;;
esac
EOF
    chmod +x "$1/bin/aws" "$1/bin/docker"
}

# run <name> <expected exit 0|1> <preset tags as tag=digest ...> -- <extra tags...>
run() {
    local name=$1 want=$2; shift 2
    local dir; dir=$(mktemp -d)
    make_fakes "$dir"
    while [ $# -gt 0 ] && [ "$1" != -- ]; do
        echo "${1#*=}" > "$dir/tags/${1%%=*}"; shift
    done
    [ "${1:-}" = -- ] && shift
    : > "$dir/log"
    out=$(PATH="$dir/bin:$PATH" STATE="$dir" DIST="$dir" AWS_REGION=ap-south-1 \
          ECR_REPOSITORY=eoan/openg2p-data/master-data-db-seed DATA_SHA=aaaaaaaaaaaa0000 \
          MDS_SHA=bbbbbbbb0000 MDS_REF=bbbbbbbb0000 \
          bash "$SCRIPT" "$LOCAL" "$REPO" "$TAG" "$@" 2>&1)
    rc=$?
    RUN_DIR=$dir RUN_OUT=$out
    if { [ "$want" = 0 ] && [ $rc -ne 0 ]; } || { [ "$want" != 0 ] && [ $rc -eq 0 ]; }; then
        echo "FAIL $name: exit $rc, expected $want"; echo "$out" | sed 's/^/     /'; fails=$((fails + 1)); return 1
    fi
    return 0
}

expect() {  # expect <name> <condition description> <test command...>
    local name=$1 what=$2; shift 2
    if "$@"; then echo "ok   $name: $what"; else
        echo "FAIL $name: $what"; echo "$RUN_OUT" | sed 's/^/     /'; fails=$((fails + 1)); fi
}
json() { python3 -c "import json,sys; print(json.load(open(sys.argv[1]))$2)" "$RUN_DIR/image.json"; }

# 1. A new tag is pushed, and image.json carries tag@digest for a deployment.
if run new 0; then
    expect new "pushes the build's tag" grep -qx "push $REPO:$TAG" "$RUN_DIR/log"
    expect new "records repo:tag@digest" [ "$(json x "['reference']")" = "$REPO:$TAG@sha256:local" ]
    expect new "records chart values, not applied" [ "$(json x "['deploy_values']['master-data.geoSeed.image.tag']")" = "$TAG@sha256:local" ]
fi

# 2. The tag is already published (a re-run of the same build): not overwritten.
if run republish 0 "$TAG=sha256:published"; then
    expect republish "pushes nothing" [ ! -s "$RUN_DIR/log" ]
    expect republish "keeps the published digest" [ "$(cat "$RUN_DIR/tags/$TAG")" = sha256:published ]
    expect republish "reports the published digest" [ "$(json x "['digest']")" = sha256:published ]
    expect republish "says it did not push" [ "$(json x "['pushed_by_this_build']")" = False ]
fi

# 3. A git tag build: the git tag names the same image as the build tag.
if run release 0 -- 1.2.0; then
    expect release "pushes both tags" [ "$(wc -l < "$RUN_DIR/log")" -eq 2 ]
    expect release "same digest under both" [ "$(cat "$RUN_DIR/tags/1.2.0")" = sha256:local ]
fi

# 4. A git tag build of an already published commit: retag the published image.
if run release-of-published 0 "$TAG=sha256:published" -- 1.2.0; then
    expect release-of-published "pulls the published image" grep -qx "pull $REPO@sha256:published" "$RUN_DIR/log"
    expect release-of-published "git tag names the published digest" [ "$(cat "$RUN_DIR/tags/1.2.0")" = sha256:published ]
    expect release-of-published "build tag not pushed again" bash -c "! grep -qx 'push $REPO:$TAG' '$RUN_DIR/log'"
fi

# 5. A git tag that already names another image is not moved.
if run moved-release 1 "1.2.0=sha256:other" -- 1.2.0; then
    expect moved-release "git tag keeps its image" [ "$(cat "$RUN_DIR/tags/1.2.0")" = sha256:other ]
    expect moved-release "says why" grep -q "not overwritten" <<< "$RUN_OUT"
fi

# 6. ECR cannot be read (no permission): fail, never assume "not published".
FAKE_AWS_DENY=1 run denied 1 && {
    expect denied "pushes nothing" [ ! -s "$RUN_DIR/log" ]
    expect denied "names the error" grep -q AccessDeniedException <<< "$RUN_OUT"
}
unset FAKE_AWS_DENY

[ $fails -eq 0 ] && echo "all publish_image.sh cases pass" || echo "$fails publish_image.sh case(s) failed"
[ $fails -eq 0 ]
