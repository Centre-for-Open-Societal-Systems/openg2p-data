#!/bin/bash
# Decide whether this Jenkins build may publish the db-seed image. Calls neither
# aws nor docker; run it before anything that talks to ECR.
#
#   publish_gate.sh        exit 0: publish; exit 1: refused, with the reason
#
# The OAN naming standard (oan-helm docs/release/naming-standard.md, section 6)
# publishes the develop build and releases only: a pull request build or any
# other branch build "is never published". So a build publishes only when it is
#   - a tag build (TAG_NAME set), or
#   - the develop branch (BRANCH_NAME=develop),
# and never when it belongs to a pull request (CHANGE_ID set), whatever its
# branch is called. There is no parameter that overrides this. The Jenkinsfile's
# `when` skips the stages for every other build; this is the second line, for a
# build that reaches them anyway. An unknown build (no Jenkins environment) is
# refused.
set -u

refuse() { echo "FAIL not publishing: $1" >&2; exit 1; }

if [ -n "${CHANGE_ID:-}" ]; then
    refuse "pull request build (${BRANCH_NAME:-?}, change ${CHANGE_ID}); a pull request build is never published"
elif [ -n "${TAG_NAME:-}" ]; then
    echo "ok   tag build ${TAG_NAME} may publish"
elif [ "${BRANCH_NAME:-}" = develop ]; then
    echo "ok   develop build may publish"
else
    refuse "branch build '${BRANCH_NAME:-unknown}'; only develop and tag builds are published"
fi
