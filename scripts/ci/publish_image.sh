#!/bin/bash
# Publish the locally built db-seed image to ECR, never overwriting a tag.
#
#   publish_image.sh <local image> <ecr image> <tag> [<more tags>...]
#
#   <ecr image>  registry/repository, e.g. 123.dkr.ecr.ap-south-1.amazonaws.com/openg2p/commons/master-data-db-seed
#   <tag>        the build's own tag, <data sha 12>-mds-<mds sha 8>
#   <more tags>  further names for the same image (the git tag on a tag build)
#
# Env: AWS_REGION, ECR_REPOSITORY, DIST, DATA_SHA, MDS_SHA, MDS_REF; PYTHON
# (default python3). Docker must already be logged in to the registry.
#
# A published tag names one image for good (OpenG2P's rule: a version is
# published exactly once). So:
#   - <tag> already in ECR (a rebuild of the same two commits): keep the
#     published image, push nothing, and report its digest.
#   - a further tag already in ECR: fine if it names the same digest, a failure
#     if it names another image.
# Writes $DIST/image.json: the reference to deploy, repo:tag@digest, for the
# separate, approved deployment that seeds an environment. Nothing here deploys.
set -euo pipefail

local_image=$1 ecr_image=$2 tag=$3
shift 3
more_tags=("$@")

# Digest the tag names in ECR, or nothing when the tag is not there. Any other
# error (no permission, no repository) fails: an unknown answer must not be
# read as "not published" and overwrite.
published_digest() {
    local out rc=0
    out=$(aws ecr describe-images --region "$AWS_REGION" --repository-name "$ECR_REPOSITORY" \
            --image-ids imageTag="$1" --query 'imageDetails[0].imageDigest' --output text 2>&1) || rc=$?
    if [ $rc -eq 0 ]; then
        printf '%s\n' "$out"
    elif ! grep -q ImageNotFoundException <<< "$out"; then
        echo "FAIL could not check whether $ECR_REPOSITORY:$1 is published: $out" >&2
        return 1
    fi
}

digest=$(published_digest "$tag")
if [ -n "$digest" ]; then
    echo "ok   $ecr_image:$tag is already published as $digest; not overwritten (this build's image is not pushed)"
    pushed=false
else
    docker tag "$local_image" "$ecr_image:$tag"
    docker push "$ecr_image:$tag"
    digest=$(published_digest "$tag")
    [ -n "$digest" ] || { echo "FAIL $ecr_image:$tag is not in ECR after the push"; exit 1; }
    echo "ok   pushed $ecr_image:$tag@$digest"
    pushed=true
fi

for t in ${more_tags[@]+"${more_tags[@]}"}; do
    have=$(published_digest "$t")
    if [ -n "$have" ]; then
        if [ "$have" != "$digest" ]; then
            echo "FAIL $ecr_image:$t already names $have, not $digest; a published tag is not overwritten"
            exit 1
        fi
        echo "ok   $ecr_image:$t already names $digest"
        continue
    fi
    # Same image under another name: the bits this build proved, or the ones
    # already published under $tag. Pushing an existing manifest keeps its digest.
    if [ "$pushed" = true ]; then
        src=$local_image
    else
        src="$ecr_image@$digest"
        docker pull "$src"
    fi
    docker tag "$src" "$ecr_image:$t"
    docker push "$ecr_image:$t"
    have=$(published_digest "$t")
    [ "$have" = "$digest" ] || { echo "FAIL $ecr_image:$t is ${have:-missing} after the push, expected $digest"; exit 1; }
    echo "ok   tagged $ecr_image:$t@$digest"
done

"${PYTHON:-python3}" - "$ecr_image" "$tag" "$digest" "$pushed" ${more_tags[@]+"${more_tags[@]}"} <<'EOF'
import json, os, sys
repo, tag, digest, pushed, more = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
info = {
    "repository": repo,
    "tag": tag,
    "tags": [tag, *more],
    "digest": digest,
    "reference": f"{repo}:{tag}@{digest}",
    "pushed_by_this_build": pushed == "true",
    "openg2p_data_commit": os.environ["DATA_SHA"],
    "master_data_service_commit": os.environ["MDS_SHA"],
    "master_data_service_ref": os.environ.get("MDS_REF"),
    # For the separate, approved deployment that seeds an environment from
    # this image (commons-services chart). CI does not apply them.
    "deploy_values": {
        "master-data.geoSeed.image.repository": repo,
        "master-data.geoSeed.image.tag": f"{tag}@{digest}",
    },
}
with open(os.path.join(os.environ["DIST"], "image.json"), "w") as f:
    json.dump(info, f, indent=2)
EOF
cat "$DIST/image.json"
