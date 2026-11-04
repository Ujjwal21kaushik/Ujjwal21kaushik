#!/usr/bin/env python3
"""Generate a self-hosted GitHub profile statistics SVG using the GitHub REST API."""
import json, os, sys, urllib.parse, urllib.request
from collections import Counter
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GITHUB_USERNAME", "Ujjwal21kaushik")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_PATH = "assets/github-stats.svg"
API = "https://api.github.com"

def api_get(path):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "profile-readme-stats-generator"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def get_stats():
    user = api_get(f"/users/{USERNAME}")
    repos = api_get(f"/users/{USERNAME}/repos?per_page=100&type=owner&sort=updated")
    repos = [r for r in repos if not r.get("fork") and not r.get("archived")]
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    languages = Counter(r.get("language") for r in repos if r.get("language"))
    prs = api_get("/search/issues?q=" + urllib.parse.quote(f"author:{USERNAME} is:pr"))
    issues = api_get("/search/issues?q=" + urllib.parse.quote(f"author:{USERNAME} is:issue"))
    return {"repos": user.get("public_repos", len(repos)), "stars": stars, "forks": forks,
            "followers": user.get("followers", 0), "prs": prs.get("total_count", 0),
            "issues": issues.get("total_count", 0), "languages": languages}


def render(stats):
    metrics = [
        ("PUBLIC REPOS", stats["repos"]),
        ("STARS", stats["stars"]),
        ("FORKS", stats["forks"]),
        ("FOLLOWERS", stats["followers"]),
        ("PULL REQUESTS", stats["prs"]),
        ("ISSUES", stats["issues"])
    ]

    positions = [
        (30, 94), (230, 94), (430, 94),
        (30, 170), (230, 170), (430, 170)
    ]

    cells = []

    for (label, value), (x, y) in zip(metrics, positions):
        cells.append(
            f'<g>'
            f'<rect x="{x}" y="{y}" width="170" height="58" '
            f'rx="10" fill="#101f50" stroke="#243b7b"/>'
            f'<text x="{x+14}" y="{y+21}" class="label">{escape(label)}</text>'
            f'<text x="{x+14}" y="{y+45}" class="value">{value:,}</text>'
            f'</g>'
        )

    # Top languages
    langs = stats["languages"].most_common(5)
    total = sum(v for _, v in langs) or 1

    bars = []

    for i, (lang, count) in enumerate(langs):
        y = 325 + i * 35
        width = 300 * count / total

        bars.append(
            f'<text x="32" y="{y}" class="lang">{escape(lang)}</text>'
            f'<rect x="150" y="{y-11}" width="300" height="8" '
            f'rx="4" fill="#1b2b61"/>'
            f'<rect x="150" y="{y-11}" width="{width:.1f}" height="8" '
            f'rx="4" fill="url(#bar)"/>'
            f'<text x="475" y="{y}" class="small">{count} repos</text>'
        )

    if not bars:
        bars.append(
            '<text x="32" y="325" class="small">'
            'Language data will appear after the first sync.'
            '</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 630 510" width="630" height="510"
role="img" aria-label="GitHub statistics for {escape(USERNAME)}">

<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#080f30"/>
        <stop offset="1" stop-color="#10265d"/>
    </linearGradient>

    <linearGradient id="edge">
        <stop offset="0" stop-color="#00d4ff"/>
        <stop offset="1" stop-color="#345bdb"/>
    </linearGradient>

    <linearGradient id="bar">
        <stop offset="0" stop-color="#00d4ff"/>
        <stop offset="1" stop-color="#4263eb"/>
    </linearGradient>
</defs>

<style>
    .title {{ font:700 21px Arial,sans-serif; fill:#fff }}
    .user {{ font:500 12px monospace; fill:#91a8dc }}
    .label {{ font:600 10px Arial,sans-serif; letter-spacing:1px; fill:#91a8dc }}
    .value {{ font:700 21px Arial,sans-serif; fill:#fff }}
    .section {{ font:700 13px Arial,sans-serif; fill:#dce8ff }}
    .lang {{ font:600 11px Arial,sans-serif; fill:#dce8ff }}
    .small {{ font:500 10px monospace; fill:#91a8dc }}
</style>

<rect x="1" y="1" width="628" height="508"
rx="18" fill="url(#bg)" stroke="url(#edge)" stroke-width="1.5"/>

<text x="30" y="39" class="title">GitHub Dashboard</text>
<text x="600" y="38" text-anchor="end" class="user">@{escape(USERNAME)}</text>

{''.join(cells)}



{''.join(bars)}

<text x="30" y="490" class="small">
    Live snapshot · GitHub API · updated by GitHub Actions
</text>

</svg>"""


def main():
    try:
        stats = get_stats()
        os.makedirs("assets", exist_ok=True)
        with open(OUT_PATH,"w",encoding="utf-8") as f: f.write(render(stats))
        print(f"Updated {OUT_PATH}")
    except Exception as exc:
        print(f"::error::Could not generate GitHub stats: {type(exc).__name__}: {exc}")
        sys.exit(1)

if __name__ == "__main__": main()
