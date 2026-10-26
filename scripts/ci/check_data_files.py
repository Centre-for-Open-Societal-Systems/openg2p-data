#!/usr/bin/env python3
"""Cheap, repo-wide checks on the committed data files.

    python scripts/ci/check_data_files.py

validate_pack.py checks what a pack *means*; this checks that every file can be
read at all, which is what a db-seed image hits first when it clones the repo:

  - every .json / .geojson parses, as UTF-8
  - every .csv is UTF-8, has a header with no duplicate or empty column names,
    and every row has as many fields as the header
  - every image_file a CSV names exists beside it

Exits non-zero if anything fails, so it works as a CI gate.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def tracked(*patterns):
    """Files git tracks, so a stray local output never fails the build."""
    out = subprocess.run(["git", "ls-files", "--", *patterns], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    return sorted(p for p in out.splitlines() if p)


def check_json(rel, errors):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            json.load(fh)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        errors.append(f"{rel}: {e}")


def check_csv(rel, errors):
    path = os.path.join(ROOT, rel)
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
    except (UnicodeDecodeError, csv.Error) as e:
        errors.append(f"{rel}: {e}")
        return
    if not rows:
        errors.append(f"{rel}: empty file")
        return
    header = rows[0]
    if any(not h.strip() for h in header):
        errors.append(f"{rel}: header has an empty column name")
    dupes = sorted({h for h in header if header.count(h) > 1})
    if dupes:
        errors.append(f"{rel}: duplicate columns {dupes}")
    for n, row in enumerate(rows[1:], start=2):
        if row and len(row) != len(header):
            errors.append(f"{rel}:{n}: {len(row)} fields, header has {len(header)}")
    if "image_file" in header:
        # Relative to the CSV, or to demography/ — household-info/ is the same
        # population and shares its portraits rather than copying them.
        col = header.index("image_file")
        bases = [os.path.dirname(path), os.path.join(ROOT, "demography")]
        missing = [r[col] for r in rows[1:] if len(r) > col and r[col]
                   and not any(os.path.exists(os.path.join(b, r[col])) for b in bases)]
        if missing:
            errors.append(f"{rel}: {len(missing)} image_file(s) missing, e.g. {missing[:3]}")


def main():
    errors = []
    json_files = tracked("*.json", "*.geojson")
    csv_files = tracked("*.csv")
    for rel in json_files:
        check_json(rel, errors)
    for rel in csv_files:
        check_csv(rel, errors)
    for e in errors:
        print(f"ERROR {e}")
    print(f"checked {len(json_files)} JSON and {len(csv_files)} CSV files: "
          f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
