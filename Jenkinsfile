// Jenkins pipeline for openg2p-data.
//
// Master Data's db-seed image bakes this repo in at build time
// (geoSeed.packRoot: /openg2p-data/packs), so this pipeline gates what a seeded
// install contains, builds that image and publishes it to ECR:
//
//   1. Lint scripts; check every JSON / GeoJSON / CSV is well-formed
//   2. validate_pack.py over every pack; GATED_PACKS (the deployed ones) must
//      pass, the others are reported
//   3. Pull the latest openg2p-commons-services chart from oan-helm and verify
//      its SHA-256 against the repository's published SHA256SUMS
//   4. Check the pack that chart selects (master-data.geoSeed.countryPack)
//      exists here, and that its geo-seed job renders for every pack
//      (`helm template` only: nothing reaches a cluster)
//   5. Package and archive the build artifacts (see 'Package artifacts')
//   6. Build master-data-db-seed from OpenG2P/master-data-service with THIS
//      commit of openg2p-data baked in, and prove the image's packs are
//      byte-identical to the ones validated above
//   7. Push it to ECR as eoan/openg2p-data/master-data-db-seed:<version>-<branch>.<build>
//      (the OAN naming standard, as the registry pipelines; <version> is init.yaml,
//      the tag comes from scripts/ci/image_names.py), and also as the git tag on a
//      tag build. A tag already in ECR is never overwritten. The openg2p-data and
//      master-data-service commits are OCI labels on the image; the pushed
//      reference, repo:tag@digest, is in dist/image.json.     (develop, tags)
//
// That is where this pipeline ends. It does not deploy or reseed anything, and
// no parameter makes it: it binds no cluster credentials and runs no
// `helm upgrade`. Seeding Master Data, a registry or the services from an image
// is a separate, approved deployment that names the image by the tag or digest
// in dist/image.json (master-data.geoSeed.image.repository / .tag in the
// commons-services chart). scripts/ci/check_jenkinsfile.py, run on every pull
// request, keeps it that way.
//
// Agent: oan-ci-deploy (as the registry pipelines), which has docker and aws,
// plus python3 with venv. Helm is downloaded at a pinned version and checksum
// into the workspace, to render the chart.
//
// Jenkins credentials:
//   AWS_ACCOUNT_ID            secret text   (shared with the registry pipelines)
//   aws-ecr-creds             AWS creds     (shared with the registry pipelines);
//                                           needs ecr:DescribeImages besides push

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
]

pipeline {
    agent { label 'oan-ci-deploy' }

    options {
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
        // One run at a time: two builds must not race to publish the same tag.
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
                     description: 'Also build and push the image from a branch other than develop or a tag')
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

        // Image: eoan/<repository>/<image>, the OAN standard (oan-helm
        // docs/release/naming-standard.md, section 6): repository openg2p-data,
        // image master-data-db-seed. The ECR repository is created outside CI
        // (immutable tags, scan on push, AES256); this pipeline fails if it is
        // missing rather than creating it.
        AWS_REGION     = 'ap-south-1'
        ECR_REPOSITORY = 'eoan/openg2p-data/master-data-db-seed'
        MDS_REPO       = 'https://github.com/OpenG2P/master-data-service.git'
        // What the image's Dockerfile clones. Must be where Jenkins builds from,
        // so the commit being built can be fetched by SHA.
        DATA_REPO_URL  = 'https://github.com/Centre-for-Open-Societal-Systems/openg2p-data.git'
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
                    // <version>-<branch>.<build>, as the registry pipelines. The commits
                    // are labels and in dist/image.json, not part of the tag.
                    env.IMAGE_TAG = sh(returnStdout: true,
                        script: 'python3 scripts/ci/image_names.py tag "$BRANCH_NAME" "$BUILD_NUMBER"').trim()
                    env.LOCAL_IMAGE = "openg2p-data-ci/master-data-db-seed:${env.IMAGE_TAG}"
                    echo "master-data-service ${env.MDS_REF} @ ${env.MDS_SHA}; openg2p-data ${env.DATA_SHA}; image tag ${env.IMAGE_TAG}"
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
                        --label org.openg2p.master-data-service.revision="$MDS_SHA"                         --label org.openg2p.master-data-service.ref="$MDS_REF" \
                        --label org.openg2p.build-url="${BUILD_URL:-}" \
                        --label org.opencontainers.image.title=master-data-db-seed \
                        --label org.opencontainers.image.version="$IMAGE_TAG" \
                        --label org.openg2p.pin.OPENG2P_DATA_BRANCH="$DATA_SHA" \
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

                        # Never overwrites a published tag; writes dist/image.json
                        # with the tag@digest a deployment pins.
                        tags=("$IMAGE_TAG")
                        [ -n "${TAG_NAME:-}" ] && tags+=("$TAG_NAME")
                        PYTHON="$TOOLS/venv/bin/python" \
                            bash scripts/ci/publish_image.sh "$LOCAL_IMAGE" "$ECR_IMAGE" "${tags[@]}"
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
