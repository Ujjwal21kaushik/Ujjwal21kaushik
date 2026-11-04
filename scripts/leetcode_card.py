#!/usr/bin/env python3
"""Generate an animated LeetCode stats card (SVG) straight from LeetCode's GraphQL API.

No third-party card service is involved, so the card can't break when someone else's
server goes down. If LeetCode can't be reached the job fails with a clear error, and the previous card stays in place.

Usage:
    LEETCODE_USERNAME=your_name python scripts/leetcode_card.py
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

USERNAME = os.environ.get("LEETCODE_USERNAME", "ueMXf7R1D6")
OUT_PATH = os.environ.get("CARD_PATH", "assets/leetcode-card.svg")

QUERY = """
query userProfile($username: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $username) {
    username
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    userCalendar { streak totalActiveDays }
  }
}
"""


def fetch(username):
    payload = json.dumps({"query": QUERY, "variables": {"username": username}}).encode()
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Referer": f"https://leetcode.com/u/{username}/",
            "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot)",
        },
    )
    last_err = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            snippet = exc.read()[:200].decode("utf-8", "replace")
            last_err = f"HTTP {exc.code} from LeetCode: {snippet}"
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
        print(f"Attempt {attempt}/3 failed -> {last_err}")
        time.sleep(3 * attempt)
    else:
        raise RuntimeError(last_err)

    if body.get("errors"):
        raise RuntimeError(f"LeetCode returned errors: {body['errors']}")
    data = body["data"]

    user = data.get("matchedUser")
    if not user:
        raise ValueError(f"LeetCode user '{username}' not found")

    solved = {r["difficulty"]: r["count"] for r in user["submitStatsGlobal"]["acSubmissionNum"]}
    total = {r["difficulty"]: r["count"] for r in data["allQuestionsCount"]}
    cal = user.get("userCalendar") or {}
    return {
        "username": user["username"],
        "solved": solved,
        "total": total,
        "ranking": (user.get("profile") or {}).get("ranking"),
        "streak": cal.get("streak", 0),
        "active_days": cal.get("totalActiveDays", 0),
    }


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else "—"


def render(data, username=USERNAME):
    pending = data is None
    solved = {} if pending else data["solved"]
    total = {} if pending else data["total"]
    name = escape(username if pending else data["username"])

    s_all, t_all = solved.get("All", 0), total.get("All", 0)
    no_totals = (not pending) and not t_all
    frac = (s_all / t_all) if t_all else 0
    r = 56
    circ = 2 * math.pi * r
    off_end = circ * (1 - frac)
    max_solved = max([solved.get(k, 0) for k in ("Easy", "Medium", "Hard")] + [1])

    rows = [("Easy", "#00B8A3", 92), ("Medium", "#FFC01E", 128), ("Hard", "#EF4743", 164)]
    bars = []
    bar_w = 372
    for label, color, y in rows:
        s, t = solved.get(label, 0), total.get(label, 0)
        if no_totals:
            w, count = s / max_solved * bar_w, str(s)
        else:
            w = (s / t * bar_w) if t else 0
            count = "—" if pending else f"{s} / {t}"
        bars.append(f"""
  <text x="214" y="{y}" class="lbl" fill="{color}">{label}</text>
  <text x="586" y="{y}" class="cnt" text-anchor="end">{count}</text>
  <rect x="214" y="{y + 9}" width="{bar_w}" height="8" rx="4" fill="#16245a"/>
  <rect x="214" y="{y + 9}" width="0" height="8" rx="4" fill="{color}">
    <animate attributeName="width" from="0" to="{w:.1f}" dur="1.3s" begin="0.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/>
  </rect>""")

    big = "—" if pending else str(s_all)
    sub = "waiting for sync" if pending else ("problems solved" if no_totals else f"of {t_all} solved")
    rank = fmt(None) if pending else ("#" + fmt(data["ranking"]) if data["ranking"] else "—")
    manual = (not pending) and data.get("manual")
    streak = "—" if (pending or manual) else f"{data['streak']} days"
    active = "—" if (pending or manual) else str(data["active_days"])

    footer_note = (
        '<text x="592" y="244" class="note" text-anchor="end">run the “Update LeetCode card” workflow once</text>'
        if pending
        else '<text x="592" y="244" class="note" text-anchor="end">numbers entered manually</text>'
        if manual
        else '<text x="592" y="244" class="note" text-anchor="end">synced from LeetCode by GitHub Actions</text>'
    )

    if no_totals:
        colors = {"Easy": "#00B8A3", "Medium": "#FFC01E", "Hard": "#EF4743"}
        parts, start = [], 0.0
        sum_ = sum(solved.get(k, 0) for k in colors) or 1
        for k, c in colors.items():
            seg = circ * solved.get(k, 0) / sum_
            if seg <= 0:
                continue
            length = max(seg - 4, 1)
            parts.append(
                f'<circle cx="110" cy="128" r="{r}" fill="none" stroke="{c}" stroke-width="10" stroke-linecap="butt" '
                f'stroke-dasharray="{length:.2f} {circ:.2f}" stroke-dashoffset="{-start:.2f}" transform="rotate(-90 110 128)" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" dur="1s" begin="0.2s" fill="freeze"/></circle>'
            )
            start += seg
        ring_svg = "".join(parts)
    else:
        ring_svg = (
            f'<circle cx="110" cy="128" r="{r}" fill="none" stroke="url(#ring)" stroke-width="10" stroke-linecap="round" '
            f'stroke-dasharray="{circ:.2f}" stroke-dashoffset="{circ:.2f}" transform="rotate(-90 110 128)">'
            f'<animate attributeName="stroke-dashoffset" from="{circ:.2f}" to="{off_end:.2f}" dur="1.6s" begin="0.1s" fill="freeze" '
            f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/></circle>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 250" width="620" height="250" role="img" aria-label="LeetCode statistics for {name}">
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#070d2e"/><stop offset="1" stop-color="#0b1b52"/>
    </linearGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#00D4FF"/><stop offset="1" stop-color="#2457C5"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#00D4FF"/><stop offset="0.5" stop-color="#2457C5"/><stop offset="1" stop-color="#090979"/>
    </linearGradient>
  </defs>
  <style>
    .t {{ font: 700 20px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: #FFA116; }}
    .u {{ font: 500 13px 'Fira Code', Consolas, monospace; fill: #8fa6d6; }}
    .big {{ font: 800 36px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: #fff; }}
    .sub {{ font: 500 12px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: #8fa6d6; }}
    .lbl {{ font: 600 14px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; }}
    .cnt {{ font: 500 13px 'Fira Code', Consolas, monospace; fill: #dbe6ff; }}
    .k {{ font: 500 11px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: #8fa6d6; text-transform: uppercase; letter-spacing: 1px; }}
    .v {{ font: 700 17px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: #fff; }}
    .note {{ font: 400 10px 'Fira Code', Consolas, monospace; fill: #5f77b0; }}
    .glow {{ animation: pulse 3s ease-in-out infinite; transform-origin: 110px 128px; }}
    @keyframes pulse {{ 0%,100% {{ opacity: .35; }} 50% {{ opacity: .8; }} }}
  </style>

  <rect x="1" y="1" width="618" height="248" rx="18" fill="url(#card)" stroke="url(#edge)" stroke-width="1.5"/>

  <text x="28" y="42" class="t">LeetCode</text>
  <text x="592" y="41" class="u" text-anchor="end">@{name}</text>

  <!-- ring -->
  <circle class="glow" cx="110" cy="128" r="70" fill="none" stroke="#00D4FF" stroke-width="1" stroke-dasharray="2 8"/>
  <circle cx="110" cy="128" r="{r}" fill="none" stroke="#16245a" stroke-width="10"/>
{ring_svg}
  <text x="110" y="133" class="big" text-anchor="middle">{big}</text>
  <text x="110" y="152" class="sub" text-anchor="middle">{sub}</text>
{''.join(bars)}

  <line x1="28" y1="190" x2="592" y2="190" stroke="#1d2f6e"/>
  <text x="28" y="208" class="k">Global rank</text>
  <text x="28" y="230" class="v">{rank}</text>
  <text x="214" y="208" class="k">Current streak</text>
  <text x="214" y="230" class="v">{streak}</text>
  <text x="380" y="208" class="k">Active days</text>
  <text x="380" y="230" class="v">{active}</text>
  {footer_note}
</svg>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate the LeetCode stats card")
    parser.add_argument("--manual", nargs=3, type=int, metavar=("EASY", "MEDIUM", "HARD"),
                        help="skip the API and draw the card from numbers you type in")
    args = parser.parse_args()

    if args.manual:
        e, m, h = args.manual
        data = {"username": USERNAME, "solved": {"All": e + m + h, "Easy": e, "Medium": m, "Hard": h},
                "total": {}, "ranking": None, "streak": 0, "active_days": 0, "manual": True}
    else:
        try:
            data = fetch(USERNAME)
        except Exception as exc:
            # Fail loudly so the red cross in the Actions tab tells you what went wrong.
            print(f"::error::Could not read LeetCode stats for '{USERNAME}': {exc}")
            print("Try:  python scripts/leetcode_card.py --manual EASY MEDIUM HARD")
            return 1

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(render(data))
    print(f"Wrote {OUT_PATH}: {data['solved'].get('All', 0)} solved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
