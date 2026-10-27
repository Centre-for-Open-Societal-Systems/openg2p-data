# openg2p-data image: this repo baked in at /openg2p-data, with the MDS seed
# scripts' dependencies installed.
#
# /openg2p-data matches master-data's geoSeed.packRoot (/openg2p-data/packs), so
# the packs are where the geo-seed Job expects them. The default command runs
# scripts/mds/seed_all_mds.py; it takes its DB settings from the
# MASTER_DATA_API_DB_* variables (see scripts/mds/README.md).
#
#   docker build -t openg2p-data:latest .
#   docker run --rm -e MASTER_DATA_API_DB_HOSTNAME=... -e MASTER_DATA_API_DB_PASSWORD=... openg2p-data:latest
FROM python:3.14-slim

ENV DATA_DIR=/openg2p-data \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Generators (faker, Pillow) plus what the MDS seed scripts import.
COPY scripts/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt psycopg2-binary requests jsonschema \
    && rm /tmp/requirements.txt

COPY . ${DATA_DIR}
WORKDIR ${DATA_DIR}

USER 10001:10001
CMD ["python3", "scripts/mds/seed_all_mds.py"]
