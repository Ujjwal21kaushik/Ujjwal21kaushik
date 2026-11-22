#!/usr/bin/env python3
"""Build the live profile cards (run by GitHub Actions every 6 hours).

    GITHUB_TOKEN=... python scripts/build_live.py          # real data
    python scripts/build_live.py --pending                  # offline preview with placeholders

Writes into assets/live/:  about-*.svg  leetcode-*.svg  github-3d-head-*.svg
If one source fails the others are still written, and the job exits with an error so you notice.
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

from common import PROFILE as P, ROOT, THEMES, card, icon_d, svg, write

LIVE = os.path.join(ROOT, "assets", "live")
SANS = ["sans400", "sans500", "sans600"]
MONO = ["mono400", "mono700"]
W = 880
TODAY = datetime.now(timezone.utc).date()


def days(v):
    return f"{v} day" + ("" if v == 1 else "s")


def n(v):
    return "—" if v is None else f"{v:,}"


# ====================================================================== data
def _post(url, payload, headers, label):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    last = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.load(resp)
            if body.get("errors"):
                raise RuntimeError(f"{label} returned errors: {body['errors']}")
            return body["data"]
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}: {exc.read()[:200].decode('utf-8', 'replace')}"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        print(f"{label}: attempt {attempt}/3 failed -> {last}")
        time.sleep(3 * attempt)
    raise RuntimeError(last)


def streaks(days):
    """days: [(date_str, count)] ascending -> (current, best)."""
    best = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    cur, i = 0, len(days) - 1
    if i >= 0 and days[i][1] == 0:
        i -= 1
    while i >= 0 and days[i][1] > 0:
        cur += 1
        i -= 1
    return cur, best


GH_QUERY = """
query($login: String!) {
  user(login: $login) {
    login createdAt
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def fetch_github():
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set")
    data = _post("https://api.github.com/graphql",
                 {"query": GH_QUERY, "variables": {"login": P["github"]}},
                 {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-readme-bot"},
                 "GitHub")
    u = data["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = sorted((d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"])
    cur, best = streaks(days)
    return {
        "login": u["login"], "created": u["createdAt"][:10], "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"], "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "total": cal["totalContributions"], "streak": cur, "best": best,
    }


LC_QUERY = """
query($u: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $u) {
    username
    profile { ranking }
    badges { id }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    languageProblemCount { languageName problemsSolved }
    userCalendar { streak totalActiveDays submissionCalendar }
  }
  userContestRanking(username: $u) { rating topPercentage attendedContestsCount }
}
"""


def fetch_leetcode():
    u = P["leetcode"]
    data = _post("https://leetcode.com/graphql", {"query": LC_QUERY, "variables": {"u": u}},
                 {"Content-Type": "application/json", "Referer": f"https://leetcode.com/u/{u}/",
                  "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot)"}, "LeetCode")
    m = data.get("matchedUser")
    if not m:
        raise RuntimeError(f"LeetCode user '{u}' not found")
    solved = {r["difficulty"]: r["count"] for r in m["submitStatsGlobal"]["acSubmissionNum"]}
    total = {r["difficulty"]: r["count"] for r in data["allQuestionsCount"]}
    cal = m.get("userCalendar") or {}
    raw = json.loads(cal.get("submissionCalendar") or "{}")
    counts = {}
    for ts, c in raw.items():
        d = datetime.fromtimestamp(int(ts), timezone.utc).date()
        counts[d] = counts.get(d, 0) + int(c)
    days = sorted((d.isoformat(), c) for d, c in counts.items())
    # best streak over the calendar window
    best = run = 0
    prev = None
    for d, c in sorted(counts.items()):
        run = run + 1 if (prev and (d - prev).days == 1) else 1
        best = max(best, run)
        prev = d
    langs = sorted(m.get("languageProblemCount") or [], key=lambda x: -x["problemsSolved"])[:2]
    cr = data.get("userContestRanking")
    return {
        "username": m["username"], "rank": (m["profile"] or {}).get("ranking"), "solved": solved, "total": total,
        "badges": len(m.get("badges") or []), "streak": cal.get("streak", 0), "best": best,
        "active": cal.get("totalActiveDays", 0), "counts": counts,
        "langs": [(x["languageName"], x["problemsSolved"]) for x in langs],
        "contest": cr and {"rating": round(cr["rating"]), "top": cr["topPercentage"], "n": cr["attendedContestsCount"]},
    }


# ====================================================================== portrait
COLS, ROWS = 60, 34
RAMP = " .:-=+*#%@"


def portrait_grid():
    """Returns (grid of 0..1 brightness, is_placeholder)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageOps

    photo = next((os.path.join(ROOT, "assets", f"photo{e}") for e in (".jpg", ".jpeg", ".png", ".webp")
                  if os.path.exists(os.path.join(ROOT, "assets", f"photo{e}"))), None)
    placeholder = photo is None
    if placeholder:
        im = Image.new("L", (300, 300), 18)
        d = ImageDraw.Draw(im)
        d.ellipse([98, 46, 202, 172], fill=230)
        d.rectangle([134, 160, 166, 208], fill=185)
        d.ellipse([34, 190, 266, 430], fill=165)
        im = im.filter(ImageFilter.GaussianBlur(3))
    else:
        im = ImageOps.exif_transpose(Image.open(photo)).convert("L")
        aspect = (COLS * 4.82) / (ROWS * 8.8)
        w, h = im.size
        cw, ch = (w, int(w / aspect)) if w / h < aspect else (int(h * aspect), h)
        left, top = (w - cw) // 2, max(0, int((h - ch) * 0.25)) if ch < h else 0
        im = im.crop((left, top, left + cw, top + ch))
        im = ImageOps.autocontrast(im, cutoff=2)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = list(im.tobytes())
    return [[px[r * COLS + c] / 255 for c in range(COLS)] for r in range(ROWS)], placeholder


def portrait_svg(grid, mode, t):
    """One <text> per row; colour changes become <tspan class=cN>."""
    out, bucket_cls = [], lambda lv: 0 if lv <= 0 else 1 if lv <= 2 else 2 if lv <= 5 else 3 if lv <= 7 else 4
    for r, row in enumerate(grid):
        runs, cur, buf = [], None, ""
        for v in row:
            v = (1 - v) if mode == "light" else v
            lv = min(9, int(v * 9.99))
            ch, cls = RAMP[lv], bucket_cls(lv)
            if cls != cur and buf:
                runs.append((cur, buf))
                buf = ""
            cur = cls
            buf += ch
        runs.append((cur, buf))
        spans = "".join(f'<tspan class="a{c}">{b}</tspan>' if c else b for c, b in runs)
        out.append(f'<text x="0" y="{r * 8.8 + 8:.1f}" class="mono" font-size="8" xml:space="preserve" style="white-space:pre">{spans}</text>')
    return "".join(out)


def portrait_css(t):
    return (f".a1{{fill:{t['dim']}}}.a2{{fill:{t['muted']}}}.a3{{fill:{t['accent']}}}.a4{{fill:{t['ink']}}}")


# ====================================================================== about card
def years_since(d0):
    y0 = date.fromisoformat(d0)
    months = (TODAY.year - y0.year) * 12 + TODAY.month - y0.month - (1 if TODAY.day < y0.day else 0)
    anchor_year, anchor_month = y0.year + (y0.month - 1 + months) // 12, (y0.month - 1 + months) % 12 + 1
    days = (TODAY - date(anchor_year, anchor_month, min(y0.day, 28))).days
    return f"{months // 12}y {months % 12}m {max(days, 0)}d on GitHub"


def about(t, mode, gh, lc, grid, placeholder):
    H = 460
    pending = gh is None and lc is None
    rows_static = [
        ("OS", "CS Engineering student"),
        ("Kernel", "Backend Development × DSA"),
        ("Shell", "Python · Java · JavaScript"),
        ("Building", "REST APIs · bots · data tools"),
        ("Learning", "React · Tailwind CSS"),
        ("Mantra", "Small progress every day adds up."),
    ]
    live = [
        ("Uptime", years_since(gh["created"]) if gh else "—"),
        ("GitHub", f'{n(gh["repos"])} repos · {n(gh["stars"])} stars · {n(gh["followers"])} followers' if gh else "—"),
        ("Contrib", f'{n(gh["total"])} in the last year' if gh else "—"),
        ("Streak", f'{days(gh["streak"])} now · {gh["best"]} best' if gh else "—"),
        ("LeetCode", (f'{lc["solved"].get("All", 0)} solved' + (f' · {n(lc["contest"]["rating"])} rating' if lc["contest"] else "")) if lc else "—"),
    ]
    b = [card(W, H, t),
         f'<path d="M1 44H{W-1}" stroke="{t["line"]}"/>'
         f'<circle cx="30" cy="22" r="5.5" fill="{t["line"]}"/><circle cx="50" cy="22" r="5.5" fill="{t["line"]}"/><circle cx="70" cy="22" r="5.5" fill="{t["line"]}"/>'
         f'<text x="{W/2}" y="26.5" text-anchor="middle" class="mono" font-size="12" fill="{t["muted"]}">{P["user"]}@{P["host"]}: ~</text>',
         f'<g transform="translate(46 92)" class="fade">{portrait_svg(grid, mode, t)}</g>',
         f'<text x="372" y="84" class="mono" font-size="13.5"><tspan fill="{t["dim"]}">$ </tspan><tspan fill="{t["ink"]}">neofetch --profile</tspan></text>',
         f'<text x="372" y="118" class="mono" font-size="18" font-weight="700"><tspan fill="{t["accent"]}">{P["user"]}</tspan><tspan fill="{t["dim"]}" font-weight="400">@</tspan><tspan fill="{t["ink"]}">{P["host"]}</tspan></text>']
    y = 150
    for i, (k, v) in enumerate(rows_static):
        b.append(f'<g class="rise" style="animation-delay:{.1 + i * .06:.2f}s"><text x="372" y="{y}" class="mono" font-size="13" fill="{t["accent"]}">{k}</text>'
                 f'<text x="462" y="{y}" class="mono" font-size="13" fill="{t["ink"]}">{escape(v)}</text></g>')
        y += 21
    y += 16
    for i, (k, v) in enumerate(live):
        b.append(f'<g class="rise" style="animation-delay:{.5 + i * .06:.2f}s"><text x="372" y="{y}" class="mono" font-size="13" fill="{t["accent"]}">{k}</text>'
                 f'<text x="462" y="{y}" class="mono" font-size="13" fill="{t["ink"]}">{escape(v)}</text></g>')
        y += 21
    b.append(f'<text x="372" y="{y + 16}" class="mono" font-size="13.5" fill="{t["dim"]}">$</text>'
             f'<rect class="blink" x="388" y="{y + 4}" width="8" height="15" fill="{t["accent"]}"/>')
    stamp = TODAY.strftime("%d %b %Y").lstrip("0")
    left = "waiting for first sync · run the workflow once" if pending else f"live · refreshed {stamp} by GitHub Actions"
    right = "placeholder portrait · add assets/photo.jpg" if placeholder else "60x34 ascii portrait"
    b.append(f'<path d="M1 424H{W-1}" stroke="{t["line"]}"/>'
             f'<circle cx="34" cy="442" r="3.2" fill="{t["ok"] if not pending else t["dim"]}"/>'
             f'<text x="46" y="446" class="mono" font-size="11" fill="{t["dim"]}">{left}</text>'
             f'<text x="{W-30}" y="446" text-anchor="end" class="mono" font-size="11" fill="{t["dim"]}">{right}</text>')
    return svg(W, H, "".join(b), f'{P["user"]}@{P["host"]}: neofetch-style profile card with ASCII portrait and live GitHub and LeetCode stats',
               SANS + MONO, portrait_css(t))


# ====================================================================== LeetCode card
def heatmap(t, counts, x0=36, y0=354, pitch=15.2, cell=12.4):
    last_sunday = TODAY - timedelta(days=(TODAY.weekday() + 1) % 7)
    start = last_sunday - timedelta(weeks=52)
    lvl = lambda c: 0 if c <= 0 else 1 if c == 1 else 2 if c <= 3 else 3 if c <= 6 else 4
    route, cells, months = [], [], []
    for c in range(53):
        order = range(7) if c % 2 == 0 else range(6, -1, -1)
        for r in order:
            route.append((c, r))
        d0 = start + timedelta(days=c * 7)
        if d0.day <= 7 and (c == 0 or (d0 - timedelta(days=7)).month != d0.month):
            months.append((c, d0.strftime("%b")))
    N = len(route)
    T = N * 0.075
    idx = {pos: k for k, pos in enumerate(route)}
    out = []
    for c, m in months:
        out.append(f'<text x="{x0 + c * pitch:.1f}" y="{y0 - 6}" class="sans" font-size="9" fill="{t["dim"]}">{m}</text>')
    for c in range(53):
        for r in range(7):
            d = start + timedelta(days=c * 7 + r)
            if d > TODAY:
                continue
            cnt = counts.get(d, 0)
            lv = lvl(cnt)
            x, y = x0 + c * pitch, y0 + r * pitch
            if lv:
                tt = (idx[(c, r)] + .5) / N
                anim = (f'<animate attributeName="opacity" calcMode="discrete" values="1;0;1;1" '
                        f'keyTimes="0;{tt:.4f};0.97;1" dur="{T:.1f}s" repeatCount="indefinite"/>')
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3" fill="{t["heat"][lv]}">{anim}</rect>')
            else:
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3" fill="{t["heat"][0]}"/>')
    pts = [(x0 + c * pitch + cell / 2, y0 + r * pitch + cell / 2) for c, r in route]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    pac_open = "M0 0L5.4 -3.1A6.2 6.2 0 1 0 5.4 3.1Z"
    pac_shut = "M0 0L6.2 -.1A6.2 6.2 0 1 0 6.2 .1Z"
    out.append(f'<g><path d="{pac_open}" fill="{t["accent"]}"><animate attributeName="d" values="{pac_open};{pac_shut};{pac_open}" dur=".35s" repeatCount="indefinite"/></path>'
               f'<animateMotion dur="{T:.1f}s" repeatCount="indefinite" rotate="auto" path="{path}"/></g>')
    ghost = "M-5.6 6V-.5A5.6 5.6 0 0 1 5.6 -.5V6L3.7 4.3L1.85 6L0 4.3L-1.85 6L-3.7 4.3Z"
    for color, off in (("#6F8BFF", 1.1), ("#F28CB1", 2.4)):
        out.append(f'<g><path d="{ghost}" fill="{color}"/><circle cx="-2" cy="-1" r="1.5" fill="#fff"/><circle cx="2" cy="-1" r="1.5" fill="#fff"/>'
                   f'<animateMotion dur="{T:.1f}s" begin="-{off}s" repeatCount="indefinite" path="{path}"/></g>')
    return "".join(out)


def leetcode(t, lc):
    H = 474
    pending = lc is None
    solved = {} if pending else lc["solved"]
    total = {} if pending else lc["total"]
    b = [card(W, H, t)]
    b.append(f'<g transform="translate(34 24) scale(.75)"><path d="{icon_d("leetcode")}" fill="{t["accent"]}"/></g>'
             f'<text x="62" y="40" class="sans" font-size="14" fill="{t["muted"]}">leetcode.com/u/<tspan font-weight="600" fill="{t["ink"]}">{P["leetcode"]}</tspan></text>'
             f'<text x="{W-36}" y="40" text-anchor="end" class="sans" font-size="13" fill="{t["dim"]}">global rank <tspan font-weight="600" fill="{t["ink"]}">'
             f'{"#" + n(lc["rank"]) if (lc and lc["rank"]) else "—"}</tspan></text>'
             f'<path d="M36 62H{W-36}" stroke="{t["line"]}"/>')
    # ring
    cx, cy, r = 140, 172, 68
    circ = 2 * math.pi * r
    s_all, t_all = solved.get("All", 0), total.get("All", 0)
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["line"]}" stroke-width="12"/>')
    parts = [("Easy", t["ok"]), ("Medium", t["accent"]), ("Hard", t["bad"])]
    start = 0.0
    for i, (k, col) in enumerate(parts):
        cnt = solved.get(k, 0)
        if not s_all or not cnt:
            continue
        seg = circ * cnt / s_all
        ln = max(seg - 7, 1)
        b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round" '
                 f'stroke-dasharray="0 {circ:.1f}" stroke-dashoffset="{-(start + 3.5):.1f}" transform="rotate(-90 {cx} {cy})">'
                 f'<animate attributeName="stroke-dasharray" from="0 {circ:.1f}" to="{ln:.1f} {circ:.1f}" dur="1.1s" begin="{i * .25}s" fill="freeze"/></circle>')
        start += seg
    b.append(f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" class="sans" font-size="44" font-weight="500" fill="{t["ink"]}">{n(s_all) if not pending else "—"}</text>'
             f'<text x="{cx}" y="{cy + 36}" text-anchor="middle" class="sans" font-size="12.5" fill="{t["muted"]}">'
             f'{"solved of " + n(t_all) if not pending else "waiting for sync"}</text>')
    # bars
    for i, (k, col) in enumerate(parts):
        y = 104 + i * 40
        s, tt = solved.get(k, 0), total.get(k, 0)
        wfill = 290 * s / tt if tt else 0
        b.append(f'<text x="272" y="{y}" class="sans" font-size="14" font-weight="500" fill="{t["ink"]}">{k}</text>'
                 f'<text x="562" y="{y}" text-anchor="end" class="sans" font-size="13" fill="{t["dim"]}"><tspan fill="{t["ink"]}">{n(s) if not pending else "—"}</tspan> / {n(tt) if not pending else "—"}</text>'
                 f'<rect x="272" y="{y + 9}" width="290" height="6" rx="3" fill="{t["line"]}"/>'
                 f'<rect x="272" y="{y + 9}" width="0" height="6" rx="3" fill="{col}"><animate attributeName="width" from="0" to="{wfill:.1f}" dur="1.1s" begin=".2s" fill="freeze"/></rect>')
    c = None if pending else lc["contest"]
    b.append(f'<text x="272" y="236" class="sans" font-size="24" font-weight="500" fill="{t["ink"]}">{n(c["rating"]) if c else "—"}</text>'
             f'<text x="272" y="255" class="sans" font-size="12" fill="{t["muted"]}">contest rating</text>'
             f'<text x="430" y="236" class="sans" font-size="24" font-weight="500" fill="{t["ink"]}">{("Top " + str(round(c["top"], 2)) + "%") if c else "—"}</text>'
             f'<text x="430" y="255" class="sans" font-size="12" fill="{t["muted"]}">{str(c["n"]) + " contests" if c else "no contests yet"}</text>')
    # consistency
    b.append(f'<path d="M596 84V262" stroke="{t["line"]}"/>'
             f'<text x="622" y="96" class="sans" font-size="11" font-weight="500" letter-spacing="2.2" fill="{t["accent"]}">CONSISTENCY</text>')
    stats = [("current streak", f'{lc["streak"]}d' if lc else "—"), ("best streak", f'{lc["best"]}d' if lc else "—"),
             ("active days, 1 year", n(lc["active"]) if lc else "—"), ("badges", n(lc["badges"]) if lc else "—")]
    for i, (lab, val) in enumerate(stats):
        x, y = 622 + (i % 2) * 126, 140 + (i // 2) * 58
        b.append(f'<text x="{x}" y="{y}" class="sans" font-size="24" font-weight="500" fill="{t["ink"]}">{val}</text>'
                 f'<text x="{x}" y="{y + 18}" class="sans" font-size="12" fill="{t["muted"]}">{lab}</text>')
    if lc and lc["langs"]:
        b.append(f'<text x="622" y="262" class="sans" font-size="12" fill="{t["muted"]}">Mostly ' + " · ".join(f"{a} {x}" for a, x in lc["langs"]) + "</text>")
    # pac-man year
    b.append(f'<path d="M36 292H{W-36}" stroke="{t["line"]}"/>'
             f'<text x="36" y="322" class="sans" font-size="11" font-weight="500" letter-spacing="2.2" fill="{t["accent"]}">PAC-MAN × MY LEETCODE YEAR</text>'
             f'<text x="{W-36}" y="322" text-anchor="end" class="sans" font-size="12" fill="{t["dim"]}">every dot is a day of solved problems</text>')
    b.append(heatmap(t, {} if pending else lc["counts"]))
    return svg(W, H, "".join(b), f'LeetCode {P["leetcode"]}: ' + ("waiting for first sync" if pending else
               f'{solved.get("All", 0)} solved ({solved.get("Easy", 0)} easy, {solved.get("Medium", 0)} medium, {solved.get("Hard", 0)} hard). Pac-Man eats the last year of submissions.'), SANS)


# ====================================================================== GitHub 3D header strip
def gh3d_head(t, gh):
    H = 56
    right = (f'<tspan font-weight="600" fill="{t["ink"]}">{n(gh["total"]) if gh else "—"}</tspan> contributions · '
             f'<tspan font-weight="600" fill="{t["ink"]}">{gh["streak"] if gh else "—"}d</tspan> streak · '
             f'<tspan font-weight="600" fill="{t["ink"]}">{gh["best"] if gh else "—"}d</tspan> best')
    b = (card(W, H, t, 16) +
         f'<g transform="translate(26 17) scale(.92)"><path d="{icon_d("github")}" fill="{t["accent"]}"/></g>'
         f'<text x="58" y="33" class="sans" font-size="14" fill="{t["muted"]}">github.com/<tspan font-weight="600" fill="{t["ink"]}">{P["github"]}</tspan> · last 12 months in 3D</text>'
         f'<text x="{W-28}" y="33" text-anchor="end" class="sans" font-size="13" fill="{t["muted"]}">{right}</text>')
    return svg(W, H, b, f'github.com/{P["github"]}: contributions in the last 12 months', SANS)


# ====================================================================== main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pending", action="store_true", help="skip the APIs and draw empty placeholder cards")
    args = ap.parse_args()

    gh = lc = None
    failed = False
    if not args.pending:
        for name, fn in (("GitHub", fetch_github), ("LeetCode", fetch_leetcode)):
            try:
                res = fn()
                gh, lc = (res, lc) if name == "GitHub" else (gh, res)
            except Exception as exc:
                failed = True
                print(f"::error::Could not read {name} data: {exc}")

    grid, placeholder = portrait_grid()
    for mode, t in THEMES.items():
        # a failed source keeps its previous file instead of being overwritten with empty values
        if args.pending or gh or lc:
            write(f"{LIVE}/about-{mode}.svg", about(t, mode, gh, lc, grid, placeholder))
        if args.pending or lc:
            write(f"{LIVE}/leetcode-{mode}.svg", leetcode(t, lc))
        if args.pending or gh:
            write(f"{LIVE}/github-3d-head-{mode}.svg", gh3d_head(t, gh))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
