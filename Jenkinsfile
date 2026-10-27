// Jenkins pipeline for openg2p-data.
//
// Master Data's db-seed image bakes this repo in at build time
// (geoSeed.packRoot: /openg2p-data/packs), so this pipeline gates what a seeded
// install contains, builds that image, pushes it to ECR and reseeds dev:
//
//   1. Lint scripts; check every JSON / GeoJSON / CSV is well-formed
//   2. validate_pack.py over every pack; GATED_PACKS (the deployed ones) must
//      pass, the others are reported
//   3. Pull the latest openg2p-commons-services chart from oan-helm and verify
//      its SHA-256 against the repository's published SHA256SUMS
//   4. Check the pack that chart selects (master-data.geoSeed.countryPack)
//      exists here, and that its geo-seed job renders for every pack
//   5. Package and archive the build artifacts (see 'Package artifacts')
//   6. Build master-data-db-seed from OpenG2P/master-data-service with THIS
//      commit of openg2p-data baked in, and prove the image's packs are
//      byte-identical to the ones validated above
//   7. Push it to ECR                                        (develop, tags)
//   8. Reseed dev from it: the geo-seed Job is rendered from the INSTALLED
//      commons-services release with only the image changed, and run as a
//      one-off Job. The Helm release itself is not upgraded — see
//      scripts/ci/seed_job_from_release.py for why.  (develop, RESEED_DEV)
//
// Agent: vpn-agent2 (as the registry pipelines), which has docker, aws and
// kubectl, plus python3 with venv. Helm is downloaded at a pinned version and
// checksum into the workspace.
//
// Jenkins credentials:
//   AWS_ACCOUNT_ID            secret text   (shared with the registry pipelines)
//   aws-ecr-creds             AWS creds     (shared with the registry pipelines)
//   commons-dev-kubeconfig    secret file   kubeconfig for the dev `commons`
//                                           namespace — ASSUMPTION, see DEV_* below

// Parameter defaults. On a job's first build Jenkins has not registered the
// parameters yet, so params.* are null and none of them is in the environment;
// 'Checkout' exports each one from here instead. Stages read env.*, not params.*.
def PARAM_DEFAULTS = [
    CHART_NAME   : 'openg2p-commons-services',
    CHART_VERSION: '',
    HELM_REPO_URL: 'https://raw.githubusercontent.com/Centre-for-Open-Societal-Systems/oan-helm/main/repository',
    // The master-data-service commit of the Master Data API dev runs
    // (0.0.0-develop.118, oan-helm releases/*: masterDataSourceCommit). The
    // loader writes the API's tables directly, so it moves with the API image.
    MDS_REF      : 'e569a59b8e9f61f809e07791e9263e50b2a7e0da',
    STRICT       : false,
    PUSH_IMAGE   : false,
    DEPLOY_DEV   : true,
    // Off until dev's existing geography and lists are reconciled with ETH-OAN
    // (oan-helm docs/refactor-location-and-ownership.md): a first load into
    // unreconciled data retires values that live records still use.
    RESEED_DEV      : false,
    AUTO_PUBLISH_DEV: true,
    // Dev's geography was loaded from the OpenAgriNet source catalog (levels
    // level-region..., units woreda-ET010101...), not from ETH-OAN (l0..l4,
    // P-codes). Loading the pack's geography over it fails on the duplicate
    // level mnemonic, so the dev reseed loads code lists only until dev's
    // registries are migrated with packs/ETH-OAN/migration/id_map.csv.
    SEED_GEO_DEV    : false,
]

pipeline {
    agent { label 'vpn-agent2' }

    options {
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
        // One run at a time: two reseeds of the same database must not overlap.
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'CHART_NAME', defaultValue: PARAM_DEFAULTS.CHART_NAME,
               description: 'oan-helm chart that carries master-data.geoSeed')
        string(name: 'CHART_VERSION', defaultValue: PARAM_DEFAULTS.CHART_VERSION,
               description: 'Chart version to check against; empty = latest published (including -dev prereleases)')
        string(name: 'HELM_REPO_URL', defaultValue: PARAM_DEFAULTS.HELM_REPO_URL,
               description: 'oan-helm chart repository')
        string(name: 'MDS_REF', defaultValue: PARAM_DEFAULTS.MDS_REF,
               description: 'Commit, tag or branch of OpenG2P/master-data-service whose docker/db-seed is built; keep it the deployed API\'s commit')
        booleanParam(name: 'STRICT', defaultValue: PARAM_DEFAULTS.STRICT,
                     description: 'Treat validate_pack.py warnings as failures')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: PARAM_DEFAULTS.PUSH_IMAGE,
                     description: 'Build and push the image from a branch other than develop (it never deploys)')
        booleanParam(name: 'DEPLOY_DEV', defaultValue: PARAM_DEFAULTS.DEPLOY_DEV,
                     description: 'On develop: reseed dev from the pushed image (also needs RESEED_DEV)')
        booleanParam(name: 'RESEED_DEV', defaultValue: PARAM_DEFAULTS.RESEED_DEV,
                     description: 'Allow the dev reseed at all. Off until dev data is reconciled with ETH-OAN')
        booleanParam(name: 'AUTO_PUBLISH_DEV', defaultValue: PARAM_DEFAULTS.AUTO_PUBLISH_DEV,
                     description: 'Dev reseed publishes changed lists and geography at once instead of leaving drafts')
        booleanParam(name: 'SEED_GEO_DEV', defaultValue: PARAM_DEFAULTS.SEED_GEO_DEV,
                     description: 'Dev reseed also loads the pack\'s geography. Off until dev\'s geo ids are migrated to ETH-OAN\'s')
    }

    environment {
        PYTHONUTF8       = '1'
        HELM_VERSION     = 'v3.19.0'
        HELM_SHA256      = 'a7f81ce08007091b86d8bd696eb4d86b8d0f2e1b9f6c714be62f82f96a594496'
        TOOLS            = "${WORKSPACE}/.tools"
        HELM_CACHE_HOME  = "${WORKSPACE}/.tools/helm/cache"
        HELM_CONFIG_HOME = "${WORKSPACE}/.tools/helm/config"
        HELM_DATA_HOME   = "${WORKSPACE}/.tools/helm/data"
        DIST             = "${WORKSPACE}/dist"
        // Packs a deployment selects (geoSeed.countryPack): validate_pack.py must
        // pass for these. Other packs are validated and reported, not gated:
        // upstream's ETH and XKM fail today (no head_of_household value since
        // OpenG2P/openg2p-data e043ffc), and PR checks stop new errors in them.
        GATED_PACKS      = 'ETH-OAN'

        // Image. Same account and naming as the other Commons images
        // (openg2p/commons/consent-manager-api, ...). The ECR repository is
        // created outside CI, like the others.
        AWS_REGION     = 'ap-south-1'
        ECR_REPOSITORY = 'openg2p/commons/master-data-db-seed'
        MDS_REPO       = 'https://github.com/OpenG2P/master-data-service.git'
        // What the image's Dockerfile clones. Must be where Jenkins builds from,
        // so the commit being built can be fetched by SHA.
        DATA_REPO_URL  = 'https://github.com/Centre-for-Open-Societal-Systems/openg2p-data.git'

        // Dev target: the installed Commons release that owns Master Data.
        // ASSUMPTION — release/namespace from oan-helm docs/rancher-dev.md
        // ("Commons `commons-services/commons`"); the kubeconfig credential id
        // follows the registries' <name>-dev-kubeconfig convention. Confirm both.
        DEV_RELEASE            = 'commons-services'
        DEV_NAMESPACE          = 'commons'
        DEV_KUBECONFIG_CRED_ID = 'commons-dev-kubeconfig'
        // Namespace-local ECR pull Secret (oan-helm docs/ecr-pull-access.md).
        DEV_PULL_SECRET        = 'ecr-pull-secret'
        // Private address of the kubeconfig's API host (Rancher). Its public
        // address answers the agent with an nginx 403, so cluster calls run in
        // a container that maps the hostname here, keeping it for TLS and
        // nginx's server_name. Empty = resolve the hostname normally.
        DEV_API_IP             = '10.0.1.58'
        KUBE_TOOLS_IMAGE       = 'alpine:3.20.3'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    for (name in PARAM_DEFAULTS.keySet()) {
                        def value = params[name] != null ? params[name] : PARAM_DEFAULTS[name]
                        env."${name}" = "${value}"
                    }
                    env.DATA_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    def ref = env.TAG_NAME ?: "${env.BRANCH_NAME ?: 'build'}-${env.BUILD_NUMBER}-${env.DATA_SHA.take(8)}"
                    env.DATA_VERSION = ref.replaceAll('[^A-Za-z0-9._-]', '-')
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.DATA_VERSION}"
                }
                sh 'rm -rf "$DIST" && mkdir -p "$DIST/reports"'
            }
        }

        stage('Setup tools') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    mkdir -p "$TOOLS/bin"
                    python3 -m venv "$TOOLS/venv"
                    "$TOOLS/venv/bin/pip" install --quiet --upgrade pip
                    # jsonschema: validate_pack.py checks attribute schemas fully
                    # when it is installed, and only a subset when it is not.
                    "$TOOLS/venv/bin/pip" install --quiet jsonschema ruff pyyaml

                    curl -sSfL -o "$TOOLS/helm.tgz" "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz"
                    echo "${HELM_SHA256}  $TOOLS/helm.tgz" | sha256sum -c -
                    tar -xzf "$TOOLS/helm.tgz" -C "$TOOLS" linux-amd64/helm
                    mv "$TOOLS/linux-amd64/helm" "$TOOLS/bin/helm"
                    "$TOOLS/bin/helm" version --short
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    # Errors only (syntax, undefined names), not style.
                    "$TOOLS/venv/bin/ruff" check scripts --select E9,F63,F7,F82
                    "$TOOLS/venv/bin/python" scripts/ci/check_data_files.py 2>&1 | tee "$DIST/reports/data-files.log"
                '''
            }
        }

        stage('Validate packs') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    packs=()
                    for d in packs/*/; do [ -f "$d/manifest.json" ] && packs+=("$(basename "$d")"); done
                    echo "Packs: ${packs[*]}"
                    printf '%s\n' "${packs[@]}" > "$DIST/reports/packs.txt"
                    strict=""
                    [ "$STRICT" = "true" ] && strict="--strict"
                    cd scripts/packs
                    : > "$DIST/reports/validate-packs.log"
                    status=0
                    for pack in "${packs[@]}"; do
                        rc=0
                        "$TOOLS/venv/bin/python" validate_pack.py $strict "../../packs/$pack" 2>&1 \
                            | tee -a "$DIST/reports/validate-packs.log" || rc=$?
                        [ $rc -eq 0 ] && continue
                        if [[ " $GATED_PACKS " == *" $pack "* ]]; then
                            echo "FAIL $pack is deployed (geoSeed.countryPack) and must pass" \
                                | tee -a "$DIST/reports/validate-packs.log"
                            status=1
                        else
                            echo "WARN $pack fails validate_pack.py; not deployed, so not gating" \
                                | tee -a "$DIST/reports/validate-packs.log"
                        fi
                    done
                    exit $status
                '''
            }
        }

        stage('Fetch latest oan-helm chart') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    helm="$TOOLS/bin/helm"
                    "$helm" repo add oan "$HELM_REPO_URL" --force-update
                    # Jenkins does not export a parameter whose value is empty: default it.
                    version="${CHART_VERSION:-}"
                    if [ -z "$version" ]; then
                        # --devel: every published package is a -dev prerelease so far.
                        version=$("$helm" search repo "oan/$CHART_NAME" --devel -o json \
                            | "$TOOLS/venv/bin/python" -c 'import json,sys; r=json.load(sys.stdin); print(r[0]["version"] if r else "")')
                    fi
                    [ -n "$version" ] || { echo "No chart oan/$CHART_NAME in $HELM_REPO_URL"; exit 1; }
                    echo "Chart: $CHART_NAME $version"
                    bash scripts/ci/pull_verified_chart.sh "$CHART_NAME" "$version" "$TOOLS/chart"
                    cp "$TOOLS/chart/$CHART_NAME-$version.tgz" "$DIST/"
                    echo "$version" > "$TOOLS/chart/version"
                '''
            }
        }

        stage('Chart compatibility') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    helm="$TOOLS/bin/helm"
                    version=$(cat "$TOOLS/chart/version")
                    chart="$TOOLS/chart/$CHART_NAME-$version.tgz"
                    job=charts/master-data/templates/geo-seed-job.yaml
                    report="$DIST/reports/chart-compat.log"

                    # The pack the chart seeds by default, read from the rendered
                    # job rather than values.yaml, so it is what an install really gets.
                    # oan-helm ships geoSeed.enabled=false, which renders no job at
                    # all; enabling it here only renders, nothing is installed.
                    enable=(--set master-data.geoSeed.enabled=true)
                    rendered=$("$helm" template probe "$chart" "${enable[@]}" --show-only "$job")
                    default_path=$(grep -oE '"[^"]*/packs/[^"]+"' <<< "$rendered" | head -1 | tr -d '"' || true)
                    default_pack=${default_path##*/}
                    seed_image=$(grep -oE 'image: [^ ]*db-seed[^ ]*' <<< "$rendered" | head -1 | cut -d' ' -f2 || true)
                    {
                        echo "chart:        $CHART_NAME $version"
                        echo "seed image:   ${seed_image:-unknown}"
                        echo "default pack: ${default_pack:-none}"
                    } | tee "$report"

                    status=0
                    if [ -z "$default_pack" ]; then
                        echo "FAIL could not find a geoSeed pack path in $job" | tee -a "$report"; status=1
                    elif [ ! -f "packs/$default_pack/manifest.json" ]; then
                        echo "FAIL chart selects $default_pack, which is not a pack in this repo" | tee -a "$report"; status=1
                    else
                        echo "ok   chart's default pack $default_pack exists" | tee -a "$report"
                    fi

                    # Every pack here must be selectable through the chart value.
                    while read -r pack; do
                        out=$("$helm" template probe "$chart" "${enable[@]}" \
                                --set "master-data.geoSeed.countryPack=$pack" \
                                --show-only "$job" 2>&1 || true)
                        if grep -q "/packs/$pack\\"" <<< "$out"; then
                            echo "ok   geo-seed job renders for $pack" | tee -a "$report"
                        else
                            echo "FAIL geo-seed job does not render for $pack" | tee -a "$report"; status=1
                        fi
                    done < "$DIST/reports/packs.txt"
                    exit $status
                '''
            }
        }

        stage('Package artifacts') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail
                    while read -r code; do
                        tar -czf "$DIST/openg2p-pack-${code}-${DATA_VERSION}.tar.gz" -C packs "$code" roles.json
                    done < "$DIST/reports/packs.txt"
                    git archive --format=tar.gz --prefix="openg2p-data-${DATA_VERSION}/" \
                        -o "$DIST/openg2p-data-${DATA_VERSION}.tar.gz" HEAD

                    CHART_VERSION_USED=$(cat "$TOOLS/chart/version") "$TOOLS/venv/bin/python" - <<'EOF'
import json, os, subprocess
git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
packs = {}
for code in open(os.path.join(os.environ["DIST"], "reports", "packs.txt")).read().split():
    m = json.load(open(f"packs/{code}/manifest.json", encoding="utf-8"))
    packs[code] = {k: m.get(k) for k in ("country", "version", "license", "unit_counts")}
info = {
    "version": os.environ["DATA_VERSION"],
    "commit": git("rev-parse", "HEAD"),
    "branch": os.environ.get("BRANCH_NAME"),
    "tag": os.environ.get("TAG_NAME"),
    "build_url": os.environ.get("BUILD_URL"),
    "chart": {"name": os.environ["CHART_NAME"], "version": os.environ["CHART_VERSION_USED"],
              "repository": os.environ["HELM_REPO_URL"]},
    "packs": packs,
}
json.dump(info, open(os.path.join(os.environ["DIST"], "build-info.json"), "w"), indent=2)
EOF
                    (cd "$DIST" && sha256sum *.tar.gz *.tgz build-info.json > SHA256SUMS)
                    ls -l "$DIST"
                '''
            }
        }

        stage('Build db-seed image') {
            when {
                anyOf { branch 'develop'; buildingTag(); expression { env.PUSH_IMAGE == 'true' } }
            }
            steps {
                script {
                    // Fetch by ref rather than `git clone --branch`, which takes a
                    // branch or tag but not the commit MDS_REF pins.
                    sh """
                        rm -rf .build/master-data-service && mkdir -p .build/master-data-service
                        cd .build/master-data-service
                        git init --quiet
                        git remote add origin '${MDS_REPO}'
                        git fetch --quiet --depth 1 origin '${env.MDS_REF}'
                        git checkout --quiet FETCH_HEAD
                    """
                    env.MDS_SHA = sh(script: 'git -C .build/master-data-service rev-parse HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.DATA_SHA.take(12)}-mds-${env.MDS_SHA.take(8)}"
                    env.LOCAL_IMAGE = "openg2p-data-ci/master-data-db-seed:${env.IMAGE_TAG}"
                    echo "master-data-service ${env.MDS_REF} @ ${env.MDS_SHA}; image tag ${env.IMAGE_TAG}"
                }
                sh '''#!/bin/bash
                    set -euo pipefail
                    # The Dockerfile clones openg2p-data itself; pinning it to this
                    # commit's SHA makes the image carry exactly what was validated.
                    docker build --pull \
                        --build-arg OPENG2P_DATA_REPO="$DATA_REPO_URL" \
                        --build-arg OPENG2P_DATA_BRANCH="$DATA_SHA" \
                        --label org.opencontainers.image.source="$DATA_REPO_URL" \
                        --label org.opencontainers.image.revision="$DATA_SHA" \
                        --label org.openg2p.master-data-service.source="$MDS_REPO" \
                        --label org.openg2p.master-data-service.revision="$MDS_SHA" \
                        --label org.openg2p.build-url="${BUILD_URL:-}" \
                        -f .build/master-data-service/docker/db-seed/Dockerfile \
                        -t "$LOCAL_IMAGE" .build/master-data-service

                    # Prove it: the packs inside the image are byte-identical to the
                    # ones validate_pack.py just passed. Both lists are sorted here, in
                    # the C locale: the agent's locale and the image's order
                    # packs/ETH/ and packs/ETH-OAN/ differently.
                    git ls-files -z packs | xargs -0 sha256sum | LC_ALL=C sort -k2 > "$DIST/reports/packs-workspace.sha256"
                    docker run --rm --entrypoint sh "$LOCAL_IMAGE" -c \
                        'cd /openg2p-data && find packs -type f -exec sha256sum {} +' \
                        | LC_ALL=C sort -k2 > "$DIST/reports/packs-image.sha256"
                    if ! diff -u "$DIST/reports/packs-workspace.sha256" "$DIST/reports/packs-image.sha256" \
                            > "$DIST/reports/packs-image.diff"; then
                        echo "FAIL packs inside the image differ from the validated workspace:"
                        head -40 "$DIST/reports/packs-image.diff"
                        exit 1
                    fi
                    echo "ok   image carries the validated packs ($(wc -l < "$DIST/reports/packs-image.sha256") files)"
                '''
            }
        }

        stage('Push to ECR') {
            when {
                anyOf { branch 'develop'; buildingTag(); expression { env.PUSH_IMAGE == 'true' } }
            }
            steps {
                withCredentials([
                    string(credentialsId: 'AWS_ACCOUNT_ID', variable: 'AWS_ACCOUNT_ID'),
                    [$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-creds']
                ]) {
                    script {
                        env.ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                        env.ECR_IMAGE = "${env.ECR_REGISTRY}/${ECR_REPOSITORY}"
                    }
                    sh '''#!/bin/bash
                        set -euo pipefail
                        if ! aws ecr describe-repositories --region "$AWS_REGION" \
                                --repository-names "$ECR_REPOSITORY" > /dev/null; then
                            echo "ECR repository $ECR_REPOSITORY does not exist (or is not visible to aws-ecr-creds)."
                            echo "It is created outside CI, like the other Commons repositories."
                            exit 1
                        fi
                        aws ecr get-login-password --region "$AWS_REGION" \
                            | docker login --username AWS --password-stdin "$ECR_REGISTRY"

                        tags=("$IMAGE_TAG")
                        [ -n "${TAG_NAME:-}" ] && tags+=("$TAG_NAME")
                        for t in "${tags[@]}"; do
                            docker tag "$LOCAL_IMAGE" "$ECR_IMAGE:$t"
                            docker push "$ECR_IMAGE:$t"
                        done
                        digest=$(docker inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$ECR_IMAGE:$IMAGE_TAG" \
                            | grep "^$ECR_IMAGE@" | head -1 | cut -d@ -f2)
                        [ -n "$digest" ] || { echo "could not read the pushed digest"; exit 1; }
                        echo "$digest" > "$TOOLS/image.digest"

                        "$TOOLS/venv/bin/python" - "$digest" "${tags[@]}" <<'EOF'
import json, os, sys
digest, tags = sys.argv[1], sys.argv[2:]
repo = os.environ["ECR_IMAGE"]
json.dump({
    "repository": repo,
    "tags": tags,
    "digest": digest,
    "reference": f"{repo}@{digest}",
    "openg2p_data_commit": os.environ["DATA_SHA"],
    "master_data_service_commit": os.environ["MDS_SHA"],
    "master_data_service_ref": os.environ.get("MDS_REF"),
}, open(os.path.join(os.environ["DIST"], "image.json"), "w"), indent=2)
EOF
                        cat "$DIST/image.json"
                    '''
                }
            }
        }

        stage('Deploy to dev') {
            when {
                allOf { branch 'develop'; expression { env.DEPLOY_DEV == 'true' && env.RESEED_DEV == 'true' } }
            }
            steps {
                withCredentials([file(credentialsId: "${DEV_KUBECONFIG_CRED_ID}", variable: 'KUBECONFIG')]) {
                    sh '''#!/bin/bash
                        set -euo pipefail
                        helm="$TOOLS/bin/helm"
                        ns="$DEV_NAMESPACE"; rel="$DEV_RELEASE"
                        report="$DIST/reports/deploy-dev.log"
                        digest=$(cat "$TOOLS/image.digest")
                        mkdir -p "$TOOLS/deploy"

                        # Calls that reach the cluster go through `cluster`. With
                        # DEV_API_IP set they run in a container whose /etc/hosts maps
                        # the API host to it; helm and kubectl are static binaries,
                        # mounted in from the agent.
                        server=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
                        api_host=$(sed -E 's#^[a-z]+://([^/:]+).*#\\1#' <<< "$server")
                        if [ -n "${DEV_API_IP:-}" ]; then
                            code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 \
                                --resolve "$api_host:443:$DEV_API_IP" "https://$api_host/healthz" || true)
                            echo "cluster API: $api_host via $DEV_API_IP, /healthz HTTP ${code:-none}"
                            [ "$code" = "200" ] || { echo "FAIL the agent cannot reach $api_host at $DEV_API_IP"; exit 1; }
                            kubectl_bin=$(readlink -f "$(command -v kubectl)")
                            cluster() {
                                docker run --rm -i --network host --add-host "$api_host:$DEV_API_IP" \
                                    -v "$KUBECONFIG:/kubeconfig:ro" -e KUBECONFIG=/kubeconfig \
                                    -v "$helm:/usr/local/bin/helm:ro" -v "$kubectl_bin:/usr/local/bin/kubectl:ro" \
                                    "$KUBE_TOOLS_IMAGE" "$@"
                            }
                        else
                            cluster() { local tool=$1; shift; [ "$tool" = helm ] && tool=$helm; "$tool" "$@"; }
                        fi

                        # Render from what is INSTALLED — its chart version and its
                        # values — so the only difference is the image.
                        meta=$(cluster helm get metadata "$rel" -n "$ns" -o json)
                        read -r chart_name chart_version revision <<< "$("$TOOLS/venv/bin/python" -c \
                            'import json,sys; m=json.load(sys.stdin); print(m["chart"], m["version"], m["revision"])' <<< "$meta")"
                        echo "installed: $rel in $ns = $chart_name $chart_version (revision $revision)" | tee "$report"
                        [ "$chart_name" = "$CHART_NAME" ] || { echo "FAIL $rel is $chart_name, expected $CHART_NAME" | tee -a "$report"; exit 1; }
                        bash scripts/ci/pull_verified_chart.sh "$chart_name" "$chart_version" "$TOOLS/deploy"

                        # Values stay in .tools (removed in cleanup) and are never
                        # archived: they can hold credentials.
                        cluster helm get values "$rel" -n "$ns" -a -o yaml > "$TOOLS/deploy/values.yaml"

                        # tag@digest renders as repo:tag@sha256:..., which pins the
                        # exact image while keeping the readable tag.
                        # The installed release keeps geoSeed.enabled=false and
                        # publishInitial/autoPublish=false; only this one-off Job
                        # turns them on, so dev shows a change as soon as it lands
                        # (AUTO_PUBLISH_DEV=false leaves drafts to approve instead).
                        # SEED_GEO_DEV=false loads code lists and domains only.
                        "$helm" template "$rel" "$TOOLS/deploy/$chart_name-$chart_version.tgz" -n "$ns" \
                            -f "$TOOLS/deploy/values.yaml" \
                            --set "master-data.geoSeed.enabled=true" \
                            --set "master-data.geoSeed.load.geo=$SEED_GEO_DEV" \
                            --set "master-data.geoSeed.publishInitial=true" \
                            --set "master-data.geoSeed.autoPublish=$AUTO_PUBLISH_DEV" \
                            --set "master-data.geoSeed.image.repository=$ECR_IMAGE" \
                            --set "master-data.geoSeed.image.tag=$IMAGE_TAG@$digest" \
                            --show-only charts/master-data/templates/geo-seed-job.yaml \
                          | "$TOOLS/venv/bin/python" scripts/ci/seed_job_from_release.py \
                                --suffix "ci-$BUILD_NUMBER" --pull-secret "$DEV_PULL_SECRET" \
                                --label "openg2p-data/commit=${DATA_SHA:0:12}" --label "openg2p-data/build=$BUILD_NUMBER" \
                          > "$DIST/reports/geo-seed-job.yaml"

                        job=$("$TOOLS/venv/bin/python" -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["metadata"]["name"])' \
                            "$DIST/reports/geo-seed-job.yaml")
                        # Quoted or not: the Job has been re-serialised by PyYAML.
                        pack=$(grep -oE '/packs/[A-Za-z0-9._-]+' "$DIST/reports/geo-seed-job.yaml" | head -1 || true)
                        echo "job: $job  pack: ${pack##*/}  image: $ECR_IMAGE:$IMAGE_TAG@$digest" | tee -a "$report"
                        [ -f "packs/${pack##*/}/manifest.json" ] || { echo "FAIL dev seeds '${pack##*/}', not a pack in this repo" | tee -a "$report"; exit 1; }

                        cluster kubectl -n "$ns" apply -f - < "$DIST/reports/geo-seed-job.yaml"

                        # Wait for Complete or Failed, whichever comes first.
                        state=""
                        for _ in $(seq 1 90); do
                            state=$(cluster kubectl -n "$ns" get job "$job" \
                                -o jsonpath='{range .status.conditions[?(@.status=="True")]}{.type}{" "}{end}' < /dev/null)
                            case "$state" in *Complete*|*Failed*) break ;; esac
                            sleep 10
                        done
                        cluster kubectl -n "$ns" logs "job/$job" --all-containers --prefix < /dev/null > "$DIST/reports/geo-seed.log" 2>&1 || true
                        tail -40 "$DIST/reports/geo-seed.log"
                        echo "job state: ${state:-timed out}" | tee -a "$report"
                        case "$state" in
                            *Complete*) echo "ok   dev reseeded from $ECR_IMAGE@$digest" | tee -a "$report" ;;
                            *) cluster kubectl -n "$ns" describe job "$job" < /dev/null | tail -30; exit 1 ;;
                        esac
                    '''
                }
            }
        }
    }

    post {
        always {
            // Reports are archived on failure too: they say why.
            archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true, fingerprint: true
        }
        cleanup {
            sh '''
                [ -n "${LOCAL_IMAGE:-}" ] && docker image rm -f "$LOCAL_IMAGE" > /dev/null 2>&1 || true
                [ -n "${ECR_IMAGE:-}" ] && docker image rm -f "$ECR_IMAGE:$IMAGE_TAG" ${TAG_NAME:+"$ECR_IMAGE:$TAG_NAME"} > /dev/null 2>&1 || true
                [ -n "${ECR_REGISTRY:-}" ] && docker logout "$ECR_REGISTRY" > /dev/null 2>&1 || true
                rm -rf "$TOOLS" .build
            '''
        }
    }
}
