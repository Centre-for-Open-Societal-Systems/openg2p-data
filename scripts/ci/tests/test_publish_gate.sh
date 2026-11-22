#!/bin/bash
# Only develop and tag builds publish (OAN naming standard: a pull request or
# other branch build is never published). Runs the real scripts against fake
# `aws` and `docker` that log every call: a refused build must make none.
#
#   bash scripts/ci/tests/test_publish_gate.sh
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
CI="$HERE/.."
REPO=123456789012.dkr.ecr.ap-south-1.amazonaws.com/eoan/openg2p-data/master-data-db-seed
TAG=1.0.0-develop.57
fails=0

make_fakes() {
    mkdir -p "$1/bin"
    for tool in aws docker; do
        cat > "$1/bin/$tool" <<EOT
#!/bin/bash
echo "$tool \$*" >> "\$STATE/calls"
echo "An error occurred (ImageNotFoundException)" >&2
exit 254
EOT
        chmod +x "$1/bin/$tool"
    done
}

# attempt <name> <want gate exit 0|1> <env assignments...>
# Runs the gate, and the publish script, with the given Jenkins environment.
attempt() {
    local name=$1 want=$2; shift 2
    local dir; dir=$(mktemp -d)
    make_fakes "$dir"; : > "$dir/calls"
    local envs=(env -u CHANGE_ID -u TAG_NAME -u BRANCH_NAME "$@")
    PATH="$dir/bin:$PATH" STATE="$dir" "${envs[@]}" bash "$CI/publish_gate.sh" > "$dir/gate.out" 2>&1
    local grc=$?
    PATH="$dir/bin:$PATH" STATE="$dir" DIST="$dir" AWS_REGION=ap-south-1 \
        ECR_REPOSITORY=eoan/openg2p-data/master-data-db-seed DATA_SHA=aaaa MDS_SHA=bbbb \
        "${envs[@]}" bash "$CI/publish_image.sh" local:img "$REPO" "$TAG" > "$dir/pub.out" 2>&1
    local prc=$?
    RUN_DIR=$dir
    if [ "$want" = 0 ]; then
        if [ $grc -eq 0 ]; then echo "ok   $name: gate allows the build"; else
            echo "FAIL $name: gate refused (exit $grc): $(cat "$dir/gate.out")"; fails=$((fails + 1)); fi
        return
    fi
    if [ $grc -ne 0 ]; then echo "ok   $name: gate refuses ($(head -1 "$dir/gate.out"))"; else
        echo "FAIL $name: gate allowed a build that must not publish"; fails=$((fails + 1)); fi
    if [ $prc -ne 0 ]; then echo "ok   $name: publish_image.sh fails"; else
        echo "FAIL $name: publish_image.sh succeeded"; fails=$((fails + 1)); fi
    if [ ! -s "$dir/calls" ]; then echo "ok   $name: no aws or docker call"; else
        echo "FAIL $name: made calls:"; sed 's/^/     /' "$dir/calls"; fails=$((fails + 1)); fi
    if [ ! -e "$dir/image.json" ]; then echo "ok   $name: no image.json"; else
        echo "FAIL $name: wrote image.json"; fails=$((fails + 1)); fi
}

# Refused, even with the retired PUSH_IMAGE parameter set to true.
attempt feature-branch 1 BRANCH_NAME=fix/roster PUSH_IMAGE=true
attempt feature-branch-default 1 BRANCH_NAME=fix/roster
attempt pull-request 1 BRANCH_NAME=PR-75 CHANGE_ID=75 PUSH_IMAGE=true
attempt pull-request-from-develop-name 1 BRANCH_NAME=develop CHANGE_ID=75 PUSH_IMAGE=true
attempt staging-branch 1 BRANCH_NAME=staging PUSH_IMAGE=true
attempt no-jenkins-environment 1 PUSH_IMAGE=true

# Allowed: develop (default) and a tag build; PUSH_IMAGE neither needed nor read.
attempt develop 0 BRANCH_NAME=develop
attempt develop-push-image-set 0 BRANCH_NAME=develop PUSH_IMAGE=true
attempt tag-build 0 BRANCH_NAME=v1.2.0 TAG_NAME=v1.2.0

# The Jenkinsfile gates its build and push stages on develop and tags alone,
# runs the gate before any ECR call, and offers no PUSH_IMAGE.
guard=$(python3 "$CI/check_jenkinsfile.py" "$CI/../../Jenkinsfile" 2>&1); grc=$?
if [ $grc -eq 0 ]; then echo "ok   Jenkinsfile passes the publish-gate guard"; else
    echo "FAIL Jenkinsfile guard:"; echo "$guard" | sed 's/^/     /'; fails=$((fails + 1)); fi
tmp=$(mktemp -d)
sed "s#anyOf { allOf { branch 'develop'; not { changeRequest() } }; buildingTag() }#anyOf { branch 'develop'; buildingTag(); expression { env.PUSH_IMAGE == 'true' } }#" \
    "$CI/../../Jenkinsfile" > "$tmp/Jenkinsfile"
if ! grep -q "PUSH_IMAGE" "$tmp/Jenkinsfile"; then
    echo "FAIL test setup: the mutated Jenkinsfile has no PUSH_IMAGE gate"; fails=$((fails + 1))
elif python3 "$CI/check_jenkinsfile.py" "$tmp/Jenkinsfile" > "$tmp/out" 2>&1 || ! grep -q "widens it" "$tmp/out"; then
    echo "FAIL guard does not reject a PUSH_IMAGE-gated push:"; sed 's/^/     /' "$tmp/out"; fails=$((fails + 1))
else echo "ok   guard rejects a push gated on PUSH_IMAGE"; fi

[ $fails -eq 0 ] && echo "all publish gate cases pass" || echo "$fails publish gate case(s) failed"
[ $fails -eq 0 ]
