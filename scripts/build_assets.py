#!/usr/bin/env python3
"""Build the static profile images (dark + light) into assets/.

    python scripts/build_assets.py

Edit the data blocks below (projects, toolbox, buttons) and re-run.
"""
import math
import os

from common import PROFILE as P, ROOT, THEMES, card, icon_d, svg, write
from xml.sax.saxutils import escape

A = os.path.join(ROOT, "assets")
SANS = ["sans400", "sans500", "sans600"]
W = 880

# ============================================================ HERO
def hero(t):
    H = 314
    b = [card(W, H, t)]
    # decorative "service graph" on the right (original artwork)
    nodes = [(700, 78), (782, 56), (846, 112), (742, 146), (812, 176), (684, 206),
             (764, 236), (842, 246), (650, 140), (722, 276), (806, 288), (858, 190)]
    edges = [(0, 1), (1, 2), (0, 3), (3, 4), (2, 4), (3, 5), (4, 6), (5, 6), (6, 7), (4, 7),
             (8, 0), (8, 3), (8, 5), (6, 9), (9, 10), (7, 10), (4, 11), (2, 11)]
    b.append('<g opacity=".95">')
    for r, op in ((34, .5), (68, .35), (104, .22)):
        b.append(f'<circle cx="780" cy="168" r="{r}" fill="none" stroke="{t["line"]}" stroke-width="1" opacity="{op+.3}"/>')
    for i, (a, c) in enumerate(edges):
        (x1, y1), (x2, y2) = nodes[a], nodes[c]
        b.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{t["line"]}" stroke-width="1.2"/>')
    for i, (x, y) in enumerate(nodes):
        big = i in (3, 4)
        b.append(f'<circle cx="{x}" cy="{y}" r="{5 if big else 3.2}" fill="{t["accent"] if big else t["card"]}" '
                 f'stroke="{t["accent"]}" stroke-width="1.4"/>')
    for k, (a, c) in enumerate(((0, 3), (3, 4), (4, 7), (8, 5), (2, 4), (6, 9))):
        (x1, y1), (x2, y2) = nodes[a], nodes[c]
        b.append(f'<circle r="2.6" fill="{t["accent"]}"><animateMotion dur="{2.6 + k * .45}s" begin="{k * .5}s" '
                 f'repeatCount="indefinite" path="M{x1} {y1}L{x2} {y2}"/></circle>')
    b.append("</g>")

    b.append(f'<text x="62" y="76" class="sans rise" font-size="11" font-weight="500" letter-spacing="3.2" fill="{t["accent"]}">HELLO, WORLD</text>')
    b.append(f'<text x="60" y="142" class="serif rise" font-size="72" fill="{t["ink"]}" style="animation-delay:.1s">'
             f'{P["name_first"]} <tspan font-style="italic" fill="{t["accent"]}">{P["name_last"]}</tspan></text>')
    # request "pipeline" line
    b.append(f'<rect x="62" y="162" width="300" height="10" rx="5" fill="none" stroke="{t["accent"]}" stroke-width="1.2" class="fade" style="animation-delay:.3s"/>')
    for x in (130, 190, 250, 310):
        b.append(f'<circle cx="{x}" cy="167" r="1.4" fill="{t["accent"]}" opacity=".6"/>')
    b.append(f'<circle cy="167" r="2.8" fill="{t["accent"]}"><animate attributeName="cx" values="72;352;72" dur="5s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="62" y="214" class="sans rise" font-size="20" fill="{t["ink"]}" style="animation-delay:.25s">Backend developer and DSA problem solver.</text>')
    b.append(f'<text x="62" y="240" class="sans rise" font-size="15" fill="{t["muted"]}" style="animation-delay:.35s">Computer Science engineering student · Python, Java, REST APIs.</text>')
    x = 62
    for i, chip in enumerate(("Backend", "DSA", "Automation")):
        w = int(len(chip) * 7.4 + 34)
        b.append(f'<g class="rise" style="animation-delay:{.45 + i * .1}s"><rect x="{x}" y="262" width="{w}" height="30" rx="15" fill="{t["chip"]}" stroke="{t["stroke"]}"/>'
                 f'<text x="{x + w / 2}" y="281.5" text-anchor="middle" class="sans" font-size="12.5" fill="{t["muted"]}">{chip}</text></g>')
        x += w + 10
    return svg(W, H, "".join(b), f'{P["name_first"]} {P["name_last"]}: backend developer and DSA problem solver',
               SANS + ["serif400", "serifi400"])


# ============================================================ HEADERS
SECTIONS = [  # slug, number, title, right-hand note
    ("about", "01", "About me", "updated daily"),
    ("work", "02", "Featured work", "things I have built"),
    ("toolbox", "03", "Toolbox", "what I build with"),
    ("contributions", "04", "GitHub contributions", "last 12 months"),
    ("problem-solving", "05", "Problem solving", "updated daily"),
]


def header(t, num, title, note):
    H = 56
    tx = 30 + len(title) * 12.2 + 14
    b = (f'<text x="2" y="34" class="sans" font-size="13" font-weight="500" fill="{t["accent"]}">{num}</text>'
         f'<text x="30" y="35" class="sans" font-size="22" font-weight="600" fill="{t["ink"]}">{escape(title)}</text>'
         f'<path class="draw" style="animation-delay:.15s" pathLength="100" d="M{tx:.1f} 27.5H{W - 8 - len(note) * 6.6 - 14:.1f}" stroke="{t["line"]}"/>'
         f'<text x="{W - 2}" y="32" text-anchor="end" class="sans" font-size="12" fill="{t["dim"]}">{escape(note)}</text>')
    return svg(W, H, b, f"{num} {title}", SANS)


# ============================================================ BUTTONS
BUTTONS = [  # slug, label, handle, icon
    ("linkedin", "LinkedIn", P["linkedin_handle"], "linkedin"),
    ("leetcode", "LeetCode", P["leetcode"], "leetcode"),
    ("github", "GitHub", P["github"], "github"),
    ("email", "Email", "say hello", "gmail"),
]


def button(t, label, handle, icon):
    w, h = 206, 54
    b = (f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{t["chip"]}" stroke="{t["stroke"]}"/>'
         f'<g transform="translate(18 15) scale(1)"><path d="{icon_d(icon)}" fill="{t["accent"]}"/></g>'
         f'<text x="58" y="24" class="sans" font-size="14" font-weight="600" fill="{t["ink"]}">{label}</text>'
         f'<text x="58" y="40" class="sans" font-size="12" fill="{t["dim"]}">{escape(handle)}</text>'
         f'<path d="M182 22l5 5-5 5" fill="none" stroke="{t["dim"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg(w, h, b, f"{label}: {handle}", SANS)


# ============================================================ TOOLBOX
# (label, simple-icons slug, dark colour, light colour)  - None colour = text colour
ROWS = [
    (["LANGUAGES"], [("Python", "python", "#4B8BBE", "#3776AB"), ("Java", "openjdk", "#F0932B", "#ED8B00"),
                   ("JavaScript", "javascript", "#F7DF1E", "#C9A800"), ("HTML5", "html5", "#E34F26", "#E34F26"),
                   ("CSS", "css", "#8A5CC9", "#663399")]),
    (["BACKEND", "& WEB"], [("FastAPI", "fastapi", "#05A38F", "#009688"), ("Flask", "flask", None, None),
                       ("Django", "django", "#44B78B", "#0C6B4B"), ("Node.js", "nodedotjs", "#5FA04E", "#3F8A2E"),
                       ("Express", "express", None, None), ("React", "react", "#61DAFB", "#1AA3C9"),
                       ("Tailwind CSS", "tailwindcss", "#38BDF8", "#06A0C4")]),
    (["DATA", "& TOOLS"], [("PostgreSQL", "postgresql", "#5B86E5", "#336791"), ("MongoDB", "mongodb", "#47A248", "#3C8A3E"),
                      ("MySQL", "mysql", "#5B9BC4", "#00758F"), ("Redis", "redis", "#FF4438", "#D82C20"),
                      ("Git", "git", "#F05032", "#F05032"), ("GitHub", "github", None, None),
                      ("Docker", "docker", "#2496ED", "#1D7FCB"), ("Postman", "postman", "#FF6C37", "#E4501C"),
                      ("Cloudflare", "cloudflare", "#F38020", "#E06A0A")]),
]


def toolbox(t, mode):
    H = 318
    PITCH, TW, TH = 86, 72, 76
    VX, VW = 146, 724
    b = [card(W, H, t), f'<path d="M130 24V{H-24}" stroke="{t["line"]}"/>']
    for r, (title, tools) in enumerate(ROWS):
        top = 22 + r * 96
        for li, line in enumerate(title):
            b.append(f'<text x="36" y="{top + 30 + li * 16}" class="sans" font-size="12" font-weight="600" letter-spacing="1.6" fill="{t["accent"]}">{escape(line)}</text>')
        b.append(f'<text x="36" y="{top + 30 + len(title) * 16 + 2}" class="sans" font-size="12" fill="{t["dim"]}">{len(tools)} tools</text>')
        n = len(tools)
        period = n * PITCH
        reps = math.ceil((VW + period) / period) + 1
        tiles = []
        for k in range(reps * n):
            label, slug, cd, cl = tools[k % n]
            col = (cd if mode == "dark" else cl) or t["ink"]
            x = k * PITCH
            tiles.append(
                f'<g transform="translate({x} 0)"><rect x="0" y="0" width="{TW}" height="{TH}" rx="14" fill="{t["chip"]}" stroke="{t["stroke"]}"/>'
                f'<g transform="translate(22 14) scale(1.1667)"><path d="{icon_d(slug)}" fill="{col}"/></g>'
                f'<text x="{TW / 2}" y="62" text-anchor="middle" class="sans" font-size="10" fill="{t["muted"]}">{escape(label)}</text></g>')
        dur = period / 26
        frm, to = (0, -period) if r % 2 == 0 else (-period, 0)
        b.append(f'<svg x="{VX}" y="{top}" width="{VW}" height="{TH + 2}" viewBox="0 0 {VW} {TH + 2}" overflow="hidden">'
                 f'<g><animateTransform attributeName="transform" type="translate" from="{frm} 1" to="{to} 1" dur="{dur:.1f}s" repeatCount="indefinite"/>'
                 f'{"".join(tiles)}</g></svg>')
    gid = "fade"
    b.append(f'<defs><linearGradient id="{gid}L" x1="0" x2="1"><stop offset="0" stop-color="{t["card"]}"/><stop offset="1" stop-color="{t["card"]}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="{gid}R" x1="0" x2="1"><stop offset="0" stop-color="{t["card"]}" stop-opacity="0"/><stop offset="1" stop-color="{t["card"]}"/></linearGradient></defs>'
             f'<rect x="{VX}" y="14" width="56" height="{H-28}" fill="url(#{gid}L)"/>'
             f'<rect x="{VX + VW - 56}" y="14" width="56" height="{H-28}" fill="url(#{gid}R)"/>')
    names = ", ".join(x[0] for _, tl in ROWS for x in tl)
    return svg(W, H, "".join(b), f"Toolbox: {names}", SANS)


# ============================================================ FOOTER
def footer(t):
    H = 240
    b = (f'<path d="M120 122H388M492 122H760" stroke="{t["line"]}"/>'
         f'<text x="414" y="132" text-anchor="middle" class="serif" font-size="64" fill="{t["accent"]}">{{</text>'
         f'<text x="466" y="132" text-anchor="middle" class="serif" font-size="64" fill="{t["accent"]}">}}</text>'
         f'<rect class="blink" x="437" y="104" width="6" height="26" rx="1" fill="{t["accent"]}"/>'
         f'<text x="440" y="192" text-anchor="middle" class="serif" font-style="italic" font-size="30" fill="{t["ink"]}">“Small progress every day adds up to big results.”</text>'
         f'<text x="440" y="224" text-anchor="middle" class="sans" font-size="12" fill="{t["dim"]}">© {P["name_first"]} {P["name_last"]} · generated with Python &amp; GitHub Actions</text>')
    return svg(W, H, b, "Small progress every day adds up to big results.", SANS + ["serifi400", "serif400"])


# ============================================================ PROJECT CARDS
PROJECTS = [
    ("WhatsApp FAQ Automation",
     "Webhook-based bot that answers customer questions automatically, with fuzzy matching and an AI fallback.",
     ["Python", "Twilio", "Webhooks"]),
    ("Business Listing Platform",
     "Searchable business directory with listings and membership flows, backed by a REST API and database.",
     ["REST API", "Database", "Search"]),
    ("Data Dashboard",
     "Upload spreadsheets and see call or lead statuses at a glance through simple, clear charts.",
     ["Python", "Data viz", "File upload"]),
    ("Mini CDN Concepts",
     "Experiments with a gateway and location-aware edge servers to explore routing and caching.",
     ["Routing", "Edge", "Caching"]),
]


def wrap(text, n):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines[:3]


def project(t, idx, title, desc, tags):
    w, h = 432, 238
    b = [card(w, h, t)]
    for i in range(4):
        for j in range(4):
            b.append(f'<circle cx="{358 + i * 11}" cy="{24 + j * 11}" r="1.5" fill="{t["accent"]}" opacity="{0.12 + 0.18 * ((i + j) / 6):.2f}"/>')
    b.append(f'<text x="28" y="48" class="sans" font-size="11" font-weight="500" letter-spacing="2.4" fill="{t["accent"]}">{idx:02d} · PROJECT</text>')
    b.append(f'<text x="28" y="84" class="sans" font-size="25" font-weight="600" fill="{t["ink"]}">{escape(title)}</text>')
    for i, line in enumerate(wrap(desc, 52)):
        b.append(f'<text x="28" y="{114 + i * 22}" class="sans" font-size="14.5" fill="{t["muted"]}">{escape(line)}</text>')
    b.append(f'<path d="M28 174H{w - 28}" stroke="{t["line"]}"/>')
    x = 28
    for tag in tags:
        tw = int(len(tag) * 6.9 + 26)
        b.append(f'<rect x="{x}" y="190" width="{tw}" height="28" rx="14" fill="{t["chip"]}" stroke="{t["stroke"]}"/>'
                 f'<text x="{x + tw / 2}" y="208.5" text-anchor="middle" class="sans" font-size="12" fill="{t["muted"]}">{escape(tag)}</text>')
        x += tw + 8
    return svg(w, h, "".join(b), f"{title}: {desc}", SANS)


# ============================================================ MAIN
def main():
    for mode, t in THEMES.items():
        write(f"{A}/hero-{mode}.svg", hero(t))
        write(f"{A}/toolbox-{mode}.svg", toolbox(t, mode))
        write(f"{A}/footer-{mode}.svg", footer(t))
        for slug, num, title, note in SECTIONS:
            write(f"{A}/headers/{slug}-{mode}.svg", header(t, num, title, note))
        for slug, label, handle, icon in BUTTONS:
            write(f"{A}/buttons/{slug}-{mode}.svg", button(t, label, handle, icon))
        for i, (title, desc, tags) in enumerate(PROJECTS, 1):
            write(f"{A}/projects/project-{i}-{mode}.svg", project(t, i, title, desc, tags))


if __name__ == "__main__":
    main()
