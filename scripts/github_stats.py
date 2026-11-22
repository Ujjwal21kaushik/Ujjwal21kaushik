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
        (24, 52), (204, 52), (384, 52),
        (24, 106), (204, 106), (384, 106)
    ]

    cells = []
    for (label, value), (x, y) in zip(metrics, positions):
        cells.append(
            f'<g><rect x="{x}" y="{y}" width="152" height="44" rx="8" '
            f'fill="#191a1d" stroke="#34353a"/>'
            f'<text x="{x+11}" y="{y+16}" class="label">{escape(label)}</text>'
            f'<text x="{x+11}" y="{y+37}" class="value">{value:,}</text></g>'
        )

    langs = stats["languages"].most_common(5)
    total = sum(v for _, v in langs) or 1
    bars = []
    for i, (lang, count) in enumerate(langs):
        y = 202 + i * 19
        width = 250 * count / total
        bars.append(
            f'<text x="26" y="{y}" class="lang">{escape(lang)}</text>'
            f'<rect x="140" y="{y-7}" width="250" height="5" rx="2.5" fill="#303136"/>'
            f'<rect x="140" y="{y-7}" width="{width:.1f}" height="5" rx="2.5" fill="url(#bar)"/>'
            f'<text x="410" y="{y}" class="small">{count} repos</text>'
        )
    if not bars:
        bars.append('<text x="26" y="202" class="small">Language data will appear after the first sync.</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 560 310" width="560" height="310"
role="img" aria-label="GitHub statistics for {escape(USERNAME)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#111214"/><stop offset="1" stop-color="#17181b"/>
  </linearGradient>
  <linearGradient id="bar">
    <stop offset="0" stop-color="#b9955b"/><stop offset="1" stop-color="#e3d1aa"/>
  </linearGradient>
</defs>
<style>
  .title {{ font:700 17px Arial,sans-serif; fill:#f4f1e9 }}
  .user {{ font:500 9px monospace; fill:#a9a49a }}
  .label {{ font:600 8px Arial,sans-serif; letter-spacing:.65px; fill:#aaa69d }}
  .value {{ font:700 17px Arial,sans-serif; fill:#f5f2eb }}
  .section {{ font:700 9px Arial,sans-serif; letter-spacing:.6px; fill:#e5dfd2 }}
  .lang {{ font:600 9px Arial,sans-serif; fill:#e8e4dc }}
  .small {{ font:500 8px monospace; fill:#aaa69d }}
</style>
<rect x="1" y="1" width="558" height="308" rx="13" fill="url(#bg)" stroke="#38352f" stroke-width="1.1"/>
<text x="24" y="31" class="title">GitHub Overview</text>
<text x="536" y="30" text-anchor="end" class="user">@{escape(USERNAME)}</text>
{''.join(cells)}
<line x1="24" y1="169" x2="536" y2="169" stroke="#302e29"/>
<text x="24" y="187" class="section">LANGUAGES</text>
{''.join(bars)}
<text x="24" y="295" class="small">Live snapshot · GitHub API · updated by GitHub Actions</text>
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
