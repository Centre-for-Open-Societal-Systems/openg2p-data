#!/usr/bin/env python3
"""Propose the new seed image to oan-helm as a pull request; never merge it.

Standard library only. Two subcommands, both used by propose_seed_pin.sh:

  rewrite <values.yaml> <image.json>
      Set master-data.geoSeed.image (repository and tag@digest) in the
      commons-services chart's values.yaml to the reference the build recorded
      in dist/image.json. Touches those two lines and nothing else. Prints
      'changed' or 'unchanged'.

  pr <body-file>
      Open the pull request from the bot branch to main, or update its title
      and body when one is already open. Reads GH_TOKEN from the environment.
      It calls the pull-request endpoints only: there is no merge call and no
      branch is written here.

The pipeline binds the oan-helm credential only in the stage that runs this.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = "Centre-for-Open-Societal-Systems/oan-helm"
BRANCH = "bot/seed-image"
BASE = "main"
GITHUB_API = os.environ.get("GITHUB_API", "https://api.github.com")  # tests point it at a fake
TITLE = "chore(commons): seed Master Data code lists from the latest openg2p-data develop build"
SEED_REPOSITORY = "379220350808.dkr.ecr.ap-south-1.amazonaws.com/eoan/openg2p-data/master-data-db-seed"

# The two lines under `image:` of `geoSeed:` that name the seed image.
_PIN = re.compile(
    r"(?P<head>^  geoSeed:\n(?:(?!^  \S).*\n)*?    image:\n)"
    r"(?P<repo>      repository: )(?P<repo_val>\S+)\n"
    r"(?P<tag>      tag: )(?P<tag_val>\S+)\n",
    re.M,
)


def set_pin(text: str, repository: str, tag: str) -> str:
    """Return values.yaml text with the seed image set; ValueError if it can't be found once."""
    if repository != SEED_REPOSITORY:
        raise ValueError(f"unexpected seed repository {repository!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+-develop\.\d+@sha256:[0-9a-f]{64}", tag):
        raise ValueError(f"unexpected seed tag {tag!r}")
    matches = list(_PIN.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"found {len(matches)} geoSeed image blocks, expected 1")
    m = matches[0]
    new = (m["head"] + m["repo"] + repository + "\n" + m["tag"] + tag + "\n")
    return text[: m.start()] + new + text[m.end():]


def _version(tag: str) -> int:
    m = re.match(r"\d+\.\d+\.\d+-develop\.(\d+)@", tag)
    return int(m.group(1)) if m else -1


def cmd_rewrite(values_path: str, image_json: str) -> int:
    with open(image_json, encoding="utf-8") as f:
        info = json.load(f)
    values = info["deploy_values"]
    repository = values["master-data.geoSeed.image.repository"]
    tag = values["master-data.geoSeed.image.tag"]
    with open(values_path, encoding="utf-8", newline="") as f:
        text = f.read()
    current = _PIN.search(text)
    # An older build's re-run must not move the pin back.
    if current and _version(current["tag_val"]) > _version(tag):
        print("unchanged (the pin is already a newer build)")
        return 0
    new = set_pin(text, repository, tag)
    if new == text:
        print("unchanged")
        return 0
    with open(values_path, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print("changed")
    return 0


def _api(method: str, path: str, token: str, body: dict | None = None):
    req = urllib.request.Request(
        f"{GITHUB_API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub {method} {path}: HTTP {e.code}: {e.read().decode()[:300]}")


def cmd_pr(body_file: str) -> int:
    token = os.environ["GH_TOKEN"]
    with open(body_file, encoding="utf-8") as f:
        body = f.read()
    owner = REPO.split("/")[0]
    open_prs = _api("GET", f"/repos/{REPO}/pulls?state=open&base={BASE}&head={owner}:{BRANCH}", token)
    if open_prs:
        n = open_prs[0]["number"]
        _api("PATCH", f"/repos/{REPO}/pulls/{n}", token, {"title": TITLE, "body": body})
        print(f"updated {REPO}#{n}")
    else:
        pr = _api("POST", f"/repos/{REPO}/pulls", token,
                  {"title": TITLE, "head": BRANCH, "base": BASE, "body": body})
        print(f"opened {REPO}#{pr['number']}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "rewrite":
        return cmd_rewrite(argv[2], argv[3])
    if len(argv) == 3 and argv[1] == "pr":
        return cmd_pr(argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
