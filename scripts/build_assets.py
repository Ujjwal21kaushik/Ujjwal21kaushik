#!/usr/bin/env python3
"""Build the static profile images (dark + light) into assets/.

    python scripts/build_assets.py

Edit the data blocks below (projects, toolbox, buttons) and re-run. Featured Work cards are generated here.
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
    b.append(f'<image x="4" y="8" width="100" height="45" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{MORPANK_DATA}"/>')
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
    b.append(f'<text x="62" y="214" class="sans rise" font-size="17" fill="{t["ink"]}" style="animation-delay:.25s">Full-stack web developer and AI &amp; data analytics enthusiast.</text>')
    b.append(f'<text x="62" y="240" class="sans rise" font-size="13.5" fill="{t["muted"]}" style="animation-delay:.35s">B.Tech CSE (AI &amp; Data Science) · GLA University.</text>')
    x = 62
    for i, chip in enumerate(("Full-stack Web", "Automation", "DSA")):
        w = int(len(chip) * 7.4 + 34)
        b.append(f'<g class="rise" style="animation-delay:{.45 + i * .1}s"><rect x="{x}" y="262" width="{w}" height="30" rx="15" fill="{t["chip"]}" stroke="{t["stroke"]}"/>'
                 f'<text x="{x + w / 2}" y="281.5" text-anchor="middle" class="sans" font-size="12.5" fill="{t["muted"]}">{chip}</text></g>')
        x += w + 10
    return svg(W, H, "".join(b), f'{P["name_first"]} {P["name_last"]}: full-stack web developer and AI & data analytics enthusiast',
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
# Descriptions and stack labels verified against each public repository README.
PROJECTS = [
    {
        "title": "Vyapar Setu", "lead": "Vyapar", "accent": "Setu",
        "desc": "Full-stack local business discovery platform with listings, reviews, bookmarks and admin verification.",
        "tags": ["React", "FastAPI", "MongoDB", "Cloudflare R2"],
        "updated": "Nov 2026", "live": True,
    },
    {
        "title": "StockDrishti", "lead": "Stock", "accent": "Drishti",
        "desc": "Retail inventory and billing system with barcode workflows, QR bills and demand forecasting.",
        "tags": ["Python", "Flask", "PostgreSQL", "JavaScript"],
        "updated": "Nov 2026",
    },
    {
        "title": "WhatsApp FAQ Chatbot", "lead": "WhatsApp FAQ", "accent": "Chatbot",
        "desc": "WhatsApp FAQ automation using cached company data, fuzzy matching and lead capture.",
        "tags": ["Python", "Flask", "Twilio", "RapidFuzz"],
        "updated": "Jun 2026",
    },
    {
        "title": "CampusPramaan", "lead": "Campus", "accent": "Pramaan",
        "desc": "Django attendance prototype combining face verification, GPS geofencing and live sessions.",
        "tags": ["Python", "Django", "OpenCV", "SQLite"],
        "updated": "Nov 2026",
    },
]

STACK_COLORS = ["#E76F51", "#3B82B7", "#8B6BB1", "#E3C84B"]


def wrap(text, n):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > n:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return lines[:2]


MORPANK_DATA = "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"


def feather(t):
    # Mor Pank sits in the upper-left corner; Rangoli geometry stays on the right.
    return (f'<image x="22" y="8" width="92" height="54" '
            f'preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{MORPANK_DATA}"/>')


def mandala(t):
    # Rangoli-inspired kolam geometry: interlaced diamonds, petals and stepped lattice.
    gold = "#C9A35B" if t["card"] == "#10151C" else "#A5772A"
    parts = [f'<g transform="translate(447 82)" fill="none" stroke="{gold}" stroke-width=".85" opacity=".23">']
    for i in range(8):
        parts.append(
            f'<g transform="rotate({i * 45})">'
            '<path d="M0 -5 L13 -20 L0 -39 L-13 -20 Z"/>'
            '<path d="M0 -12 Q-20 -22 0 -34 Q20 -22 0 -12Z"/>'
            '<path d="M0 -39 L-7 -52 L0 -65 L7 -52 Z"/>'
            '<path d="M-13 -20 L-28 -20 L-36 -31 L-22 -34 Z"/>'
            '<path d="M13 -20 L28 -20 L36 -31 L22 -34 Z"/>'
            '<path d="M0 -5 L-8 5 L0 14 L8 5 Z"/>'
            '</g>')
    for i in range(4):
        parts.append(f'<g transform="rotate({i * 45})"><path d="M0 -18 L18 -36 L0 -54 L-18 -36 Z"/>'
                     f'<path d="M0 -28 L8 -36 L0 -44 L-8 -36 Z"/></g>')
    parts.append('<path d="M0 -69 L8 -61 L0 -53 L-8 -61 Z M0 0 L8 8 L0 16 L-8 8 Z"/>')
    parts.append('</g>')
    return ''.join(parts)


def project(t, idx, item):
    w, h = 520, 270
    title, desc, tags = item["title"], item["desc"], item["tags"]
    lead, accent = item["lead"], item["accent"]
    gold = "#C9A35B" if t["card"] == "#10151C" else "#A5772A"
    soft_gold = "#A9874F" if t["card"] == "#10151C" else "#B18A48"
    b = [
        f'<rect x="1" y="1" width="518" height="268" rx="18" fill="{t["card"]}" stroke="{soft_gold}" stroke-opacity=".62" stroke-width="1"/>',
        mandala(t),
        feather(t),
        f'<text x="128" y="39" class="sans" font-size="10.5" font-weight="600" letter-spacing="2.5" fill="{gold}">{idx:02d} · PROJECT</text>',
        f'<path d="M266 34H323" stroke="{gold}" stroke-width="1.2" opacity=".75"/>',
        f'<text x="30" y="82" class="serif" font-size="34" font-weight="400" fill="{t["ink"]}">{escape(lead)} <tspan font-style="italic" fill="{gold}">{escape(accent)}</tspan></text>',
    ]
    if item.get("live"):
        b.append(f'<g><rect x="431" y="26" width="58" height="22" rx="11" fill="{t["chip"]}" stroke="{gold}" stroke-width="1"/>'
                 f'<circle cx="443" cy="37" r="3.2" fill="#38C98B"/><text x="452" y="41" class="sans" font-size="9.5" font-weight="600" letter-spacing=".8" fill="{gold}">LIVE</text></g>')
    for i, line in enumerate(wrap(desc, 64)):
        b.append(f'<text x="30" y="{116 + i * 22}" class="serif" font-size="17" fill="{t["ink"]}">{escape(line)}</text>')

    bar_x, bar_y, bar_w, bar_h = 30, 165, 460, 7
    b.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3.5" fill="{t["line"]}"/>')
    seg_w = bar_w / len(tags)
    for i, _ in enumerate(tags):
        x = bar_x + i * seg_w
        b.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w + .5:.1f}" height="{bar_h}" rx="2" fill="{STACK_COLORS[i % len(STACK_COLORS)]}"/>')

    x, y = 30, 205
    for tag in tags:
        tw = int(len(tag) * 7.0 + 34)
        if x + tw > 490:
            x, y = 30, 229
        b.append(f'<rect x="{x}" y="{y-17}" width="{tw}" height="27" rx="13.5" fill="{t["chip"]}" stroke="{soft_gold}" stroke-opacity=".55"/>')
        b.append(f'<text x="{x + tw / 2}" y="{y + 1}" text-anchor="middle" class="serif" font-size="14" fill="{t["ink"]}">{escape(tag)}</text>')
        x += tw + 8

    b.append(f'<path d="M30 235H490" stroke="{soft_gold}" stroke-opacity=".42" stroke-width=".8"/>')
    b.append(f'<path d="M35 248l5 -8 5 8 -5 5Z" fill="{gold}"/>')
    b.append(f'<text x="55" y="252" class="serif" font-size="14" fill="{t["ink"]}">0</text>')
    b.append(f'<path d="M108 242v10m0 -8l-5 -4m5 4l5 -4m-5 8l-5 4m5 -4l5 4" stroke="{t["ink"]}" stroke-width="1.2" fill="none" stroke-linecap="round"/>')
    b.append(f'<text x="125" y="252" class="serif" font-size="14" fill="{t["ink"]}">0</text>')
    b.append(f'<text x="490" y="252" text-anchor="end" class="serif" font-size="14" fill="{t["ink"]}">Updated {item["updated"]} ↗</text>')
    return svg(w, h, "".join(b), f'{title}: {desc}', SANS + ["serif400", "serifi400"])


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
        for i, item in enumerate(PROJECTS, 1):
            write(f"{A}/projects/project-{i}-{mode}.svg", project(t, i, item))


if __name__ == "__main__":
    main()
