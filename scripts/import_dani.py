#!/usr/bin/env python3
"""Import an existing, user-supplied ZIP of Dani's Sweet Lab assets into the portfolio."""
from __future__ import annotations
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import re
import sys
from PIL import Image

ASSETS = Path("assets/images/portfolio/danis-sweet-lab")
INDEX = Path("index.html")
ROOT = "Danis-Sweet-Lab/"
CATEGORIES = ("Menus/", "Social Posts/", "Logo/", "Highlight Covers/")
LABELS = {"Menus": "Menu design", "Social Posts": "Social media", "Logo": "Brand identity", "Highlight Covers": "Highlight cover"}

def main():
    zpath = Path(sys.argv[1])
    ASSETS.mkdir(parents=True, exist_ok=True)
    gallery = []
    with ZipFile(zpath) as bundle:
        names = [n for n in bundle.namelist() if n.startswith(ROOT) and n.lower().endswith(".png") and n[len(ROOT):].startswith(CATEGORIES)]
        if len(names) != 26:
            raise SystemExit(f"Expected 26 provided PNG files; got {len(names)}")
        for position, name in enumerate(names, 1):
            with Image.open(BytesIO(bundle.read(name))) as source:
                img = source.copy()
            # Keep original detail in portrait-format menus, preserve alpha for logos.
            max_size = (1800, 2700) if "/Menus/" in name else (1400, 1400)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            filename = f"{position:02d}.webp"
            img.save(ASSETS / filename, format="WEBP", quality=88, method=5)
            original_name = name.split("/")[-1].removesuffix(".png")
            category = name[len(ROOT):].split("/")[0]
            label = f"{original_name} - {LABELS.get(category, category)}"
            gallery.append((filename, label, img.width, img.height))

    html = INDEX.read_text(encoding="utf-8")
    if 'id="p-danis-sweet-lab"' in html:
        print("Project already in HTML; images refreshed.")
        return
    items = []
    for i, (filename, label, width, height) in enumerate(gallery, 1):
        url = f"assets/images/portfolio/danis-sweet-lab/{filename}"
        alt = escape(f"Dani's Sweet Lab - {label}", quote=True)
        cap = escape(f"Dani's Sweet Lab · {label}", quote=True)
        items.append(f'<li><button class="shot" type="button" data-full="{url}" data-cap="{cap}" aria-label="Open {alt}"><img src="{url}" alt="{alt}" width="{width}" height="{height}" loading="lazy" decoding="async"></button></li>')

    article = (
        '      <article class="proj" data-cat="food" id="p-danis-sweet-lab">\n'
        '        <div class="proj-meta">\n'
        '          <span class="proj-no">00</span>\n'
        "          <h3>Dani's Sweet Lab</h3>\n"
        '          <p class="proj-cat">Food &amp; Hospitality · 26 designs</p>\n'
        '          <p class="proj-desc">A playful pink dessert brand identity carried across menus, food promotions, social media graphics, logo treatments and Instagram highlight covers.</p>\n'
        '          <ul class="tags"><li>Brand identity</li><li>Social media</li><li>Menus</li><li>Highlights</li></ul>\n'
        '        </div>\n'
        f'        <ul class="strip" aria-label="Dani&#39;s Sweet Lab designs">{"".join(items)}</ul>\n'
        '      </article>\n'
    )
    target = '      <article class="proj" data-cat="food"'
    if target not in html:
        raise SystemExit("Could not find food project insertion point")
    html = html.replace(target, article + target, 1)

    heading = '<h2>49 designs for <span class="serif">13 brands</span></h2>'
    if heading not in html:
        raise SystemExit("Unexpected project count heading")
    html = html.replace(heading, '<h2>75 designs for <span class="serif">14 brands</span></h2>', 1)
    for a, b in (
        ('data-f="all" aria-pressed="true">All <small>13</small>', 'data-f="all" aria-pressed="true">All <small>14</small>'),
        ('data-f="food" aria-pressed="false">Food &amp; Hospitality <small>7</small>', 'data-f="food" aria-pressed="false">Food &amp; Hospitality <small>8</small>'),
    ):
        if a not in html:
            raise SystemExit(f"Missing filter markup: {a}")
        html = html.replace(a, b, 1)

    def resequence(match):
        resequence.n += 1
        return f'<span class="proj-no">{resequence.n:02d}</span>'
    resequence.n = 0
    html = re.sub(r'<span class="proj-no">\d+</span>', resequence, html)
    if resequence.n != 14:
        raise SystemExit(f"Expected 14 project cards, found {resequence.n}")
    if re.search("designify", html, re.IGNORECASE):
        raise SystemExit("Unexpected studio name appears in portfolio")
    INDEX.write_text(html, encoding="utf-8")
    print(f"Added {len(gallery)} designs and updated portfolio to {resequence.n} projects")

if __name__ == "__main__":
    main()
