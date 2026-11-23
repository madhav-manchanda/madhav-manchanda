#!/usr/bin/env python3
"""Generate a compact SVG card from public GitHub profile/repository metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

USERNAME = "madhav-manchanda"
API_ROOT = "https://api.github.com"


def github_get(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profile-readme-metrics",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def collect():
    user = github_get(f"/users/{USERNAME}")
    stars = 0
    forks = 0
    owned_repos = 0

    for page in range(1, 21):
        repos = github_get(
            f"/users/{USERNAME}/repos?type=owner&per_page=100&sort=updated&page={page}"
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("owner", {}).get("login", "").lower() != USERNAME.lower():
                continue
            owned_repos += 1
            stars += int(repo.get("stargazers_count") or 0)
            forks += int(repo.get("forks_count") or 0)
        if len(repos) < 100:
            break

    return {
        "followers": int(user.get("followers") or 0),
        "repositories": int(user.get("public_repos") or owned_repos),
        "stars": stars,
        "forks": forks,
    }


def compact(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def render(stats: dict[str, int]) -> str:
    items = [
        ("PUBLIC REPOSITORIES", stats["repositories"]),
        ("STARS EARNED", stats["stars"]),
        ("FOLLOWERS", stats["followers"]),
        ("FORKS", stats["forks"]),
    ]
    cells = []
    for index, (label, value) in enumerate(items):
        x = 38 + index * 232
        cells.append(
            f"""
            <g transform="translate({x},0)">
              <text class="label" x="0" y="89">{html.escape(label)}</text>
              <text class="value" x="0" y="137">{html.escape(compact(value))}</text>
              <rect class="underline" x="0" y="153" width="42" height="3" rx="1.5">
                <animate attributeName="width" values="18;42;18" dur="{3.2 + index * 0.4}s" repeatCount="indefinite"/>
              </rect>
            </g>
            """
        )

    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y").upper()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="220" viewBox="0 0 1000 220" role="img" aria-labelledby="title desc">
  <title id="title">Madhav Manchanda — GitHub overview</title>
  <desc id="desc">Public repository, star, follower and fork counts generated automatically from GitHub.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0D130F"/>
      <stop offset="100%" stop-color="#030503"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00FF41"/>
      <stop offset="100%" stop-color="#FF3355"/>
    </linearGradient>
    <style>
      .eyebrow {{ fill:#6F8A76; font:600 11px 'SFMono-Regular',Consolas,monospace; letter-spacing:2.2px; }}
      .heading {{ fill:#EAFFF0; font:600 19px 'Segoe UI',Arial,sans-serif; }}
      .label {{ fill:#6F8A76; font:600 10px 'SFMono-Regular',Consolas,monospace; letter-spacing:1.15px; }}
      .value {{ fill:#EAFFF0; font:600 31px 'Segoe UI',Arial,sans-serif; }}
      .underline {{ fill:url(#accent); }}
      .scan {{ stroke:#39FF7A; stroke-width:1; opacity:.10; }}
    </style>
  </defs>
  <rect x="1" y="1" width="998" height="218" rx="16" fill="url(#panel)" stroke="#1F3A28"/>
  <path d="M18 17 H982" stroke="url(#accent)" stroke-width="2" opacity=".85"/>
  <text class="eyebrow" x="38" y="43">GITHUB / PUBLIC PROFILE</text>
  <text class="heading" x="38" y="68">An overview of what I'm building in the open.</text>
  {''.join(cells)}
  <text class="eyebrow" x="962" y="194" text-anchor="end">UPDATED {updated} UTC</text>
  <circle cx="965" cy="42" r="4" fill="#39FF7A">
    <animate attributeName="opacity" values="1;.35;1" dur="2.4s" repeatCount="indefinite"/>
  </circle>
  <path class="scan" d="M24 177 H976">
    <animate attributeName="opacity" values=".03;.16;.03" dur="5s" repeatCount="indefinite"/>
  </path>
</svg>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/profile-metrics.svg")
    args = parser.parse_args()

    stats = collect()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(stats), encoding="utf-8")
    print(f"Wrote {output} with {stats}")


if __name__ == "__main__":
    main()
