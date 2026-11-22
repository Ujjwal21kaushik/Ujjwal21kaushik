"""Shared design system for the profile images (colors, fonts, icons, SVG wrapper).

Everything is generated: change PROFILE / ACCENT here and re-run the build scripts.
Fonts (Inter, Crimson Text, DejaVu Sans Mono) are open-licensed and embedded per image,
so the SVGs look identical on every device without loading anything from the internet.
"""
import base64
import io
import os
import re
from html import unescape
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT_DIR = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- profile data
PROFILE = {
    "name_first": "Ujjwal",
    "name_last": "Kaushik",
    "github": "Ujjwal21kaushik",
    "leetcode": "ueMXf7R1D6",
    "linkedin_url": "https://www.linkedin.com/in/ujjwal-kaushik-447763280",
    "linkedin_handle": "ujjwal-kaushik",
    "email": "ujjwalkaus21@gmail.com",
    "host": "backend",   # shows as  ujjwal@backend  in the terminal card
    "user": "ujjwal",
}

# ---------------------------------------------------------------- themes
THEMES = {
    "dark": dict(
        card="#10151C", stroke="#232B38", ink="#E6E8EE", muted="#9AA3B5", dim="#6B7385",
        accent="#C9A35B", line="#232B38", chip="#151B24", ok="#3AA89B", bad="#D96A7A",
        heat=["#161C25", "#0E4F4A", "#13766D", "#1FA096", "#4BD2C3"], term_bar="#0D1218",
    ),
    "light": dict(
        card="#FBFAF8", stroke="#E3E0D8", ink="#1F2328", muted="#57606A", dim="#8A9099",
        accent="#A5772A", line="#E3E0D8", chip="#F3F1EC", ok="#1F8F80", bad="#C4475A",
        heat=["#EBEDF0", "#B7E4DC", "#6FCBBE", "#2FA597", "#0F766E"], term_bar="#F3F1EC",
    ),
}

# ---------------------------------------------------------------- fonts
FACES = {
    # key: (file, family, weight, style)
    "sans400": ("Inter-Regular.woff", "Inter", 400, "normal"),
    "sans500": ("Inter-Medium.woff", "Inter", 500, "normal"),
    "sans600": ("Inter-SemiBold.woff", "Inter", 600, "normal"),
    "serif400": ("Serif-Regular.woff", "Crimson Text", 400, "normal"),
    "serifi400": ("Serif-Italic.woff", "Crimson Text", 400, "italic"),
    "mono400": ("Mono-Regular.woff", "DejaVu Sans Mono", 400, "normal"),
    "mono700": ("Mono-Bold.woff", "DejaVu Sans Mono", 700, "normal"),
}

_cache = {}


def _subset_b64(filename, chars):
    key = (filename, chars)
    if key in _cache:
        return _cache[key]
    opts = subset.Options()
    opts.layout_features = ["kern"]
    opts.notdef_outline = False
    opts.name_IDs = []
    font = TTFont(os.path.join(FONT_DIR, filename))
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    font.flavor = "woff"
    buf = io.BytesIO()
    font.save(buf)
    _cache[key] = base64.b64encode(buf.getvalue()).decode()
    return _cache[key]


def visible_chars(body):
    """All characters shown as text in an SVG body (so each image embeds only what it needs)."""
    text = "".join(re.findall(r">([^<>]+)<", body))
    return "".join(sorted(set(unescape(text) + " ")))


def font_css(faces, chars):
    out = []
    for key in faces:
        fn, fam, wt, st = FACES[key]
        out.append(
            f"@font-face{{font-family:'{fam}';font-weight:{wt};font-style:{st};"
            f"src:url(data:font/woff;base64,{_subset_b64(fn, chars)}) format('woff')}}"
        )
    return "".join(out)


BASE_CSS = (
    ".sans{font-family:'Inter','Segoe UI',system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif}"
    ".serif{font-family:'Crimson Text',Georgia,'Times New Roman',serif}"
    ".mono{font-family:'DejaVu Sans Mono',ui-monospace,SFMono-Regular,Consolas,Menlo,monospace}"
    ".rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}@keyframes rise{from{opacity:0;transform:translateY(6px)}}"
    ".fade{animation:fadein 1.1s ease both}@keyframes fadein{from{opacity:0}}"
    ".draw{stroke-dasharray:100;animation:drawin 1.3s cubic-bezier(.6,0,.2,1) both}@keyframes drawin{from{stroke-dashoffset:100}}"
    ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


def svg(w, h, body, title, faces, extra_css=""):
    css = font_css(faces, visible_chars(body + f">{title}<"))
    t = escape(title)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{t}">'
        f"<title>{t}</title><defs><style>{css}{BASE_CSS}{extra_css}</style></defs>{body}</svg>\n"
    )


def card(w, h, t, rx=18):
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{rx}" fill="{t["card"]}" stroke="{t["stroke"]}"/>'


# ---------------------------------------------------------------- icons
import json

with open(os.path.join(HERE, "icons.json"), encoding="utf-8") as _fh:
    ICONS = json.load(_fh)  # Simple Icons marks (CC0), trademarks remain with their owners
# LinkedIn's mark is not shipped in Simple Icons any more; this is a simple glyph path.
LINKEDIN_D = ("M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9.75h4V21H3V9.75Zm6.5 0h3.8v1.6h.06c.53-1 1.83-2.05 "
              "3.77-2.05 4.03 0 4.77 2.65 4.77 6.1V21h-4v-4.93c0-1.18-.02-2.7-1.64-2.7-1.65 0-1.9 1.29-1.9 2.61V21h-4V9.75Z")


def icon_d(slug):
    if slug == "linkedin":
        return LINKEDIN_D
    return ICONS[slug]


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", os.path.relpath(path, ROOT), f"({len(content)//1024} KB)")
