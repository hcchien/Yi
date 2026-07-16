#!/usr/bin/env python3
"""Generate 64 static social-preview pages and their Open Graph cards."""

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://hcchien.github.io/Yi"
FONT_CJK = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/Arial.ttf"


def load_hexagrams():
    source = (ROOT / "js/data.js").read_text(encoding="utf-8")
    match = re.fullmatch(r"window\.YI = (.*);\s*", source, re.S)
    if not match:
        raise RuntimeError("Unable to parse js/data.js")
    return json.loads(match.group(1))


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_centered(draw, xy, text, font_obj, fill):
    box = draw.textbbox((0, 0), text, font=font_obj)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1]), text, font=font_obj, fill=fill)


def draw_hexagram(draw, binary):
    x, y, width, height, gap = 120, 145, 245, 20, 20
    for index, bit in enumerate(reversed(binary)):
        line_y = y + index * (height + gap)
        if bit == "1":
            draw.rounded_rectangle((x, line_y, x + width, line_y + height), 5, fill="#43836c")
        else:
            segment = 103
            draw.rounded_rectangle((x, line_y, x + segment, line_y + height), 5, fill="#43836c")
            draw.rounded_rectangle((x + width - segment, line_y, x + width, line_y + height), 5, fill="#43836c")


def build_card(hexagram, target):
    image = Image.new("RGB", (1200, 630), "#f5f4ee")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((38, 38, 1162, 592), 24, fill="#ffffff", outline="#dce5df", width=2)
    draw.ellipse((75, 73, 410, 408), fill="#edf5f0", outline="#b8d2c6", width=2)
    draw_hexagram(draw, hexagram["b"])

    draw.text((470, 110), f"第 {hexagram['n']} 卦", font=font(FONT_CJK, 34), fill="#df684f")
    draw.text((470, 165), hexagram["nm"]["zh"], font=font(FONT_CJK, 112), fill="#20302a")
    draw.text((475, 305), hexagram["nm"]["en"], font=font(FONT_LATIN, 42), fill="#43836c")
    draw.line((470, 378, 1080, 378), fill="#dce5df", width=2)
    draw.text((470, 414), "擲爻問卦 · I Ching Oracle", font=font(FONT_CJK, 29), fill="#53665e")
    draw.text((470, 465), "六爻成卦 · 觀時知變", font=font(FONT_CJK, 24), fill="#89968f")

    draw.rounded_rectangle((1042, 465, 1115, 538), 12, fill="#df684f")
    draw_centered(draw, (1078, 474), "易", font(FONT_CJK, 43), "#f3ecdc")
    image.save(target, optimize=True, quality=92)


def build_page(hexagram, target):
    n = hexagram["n"]
    zh_name = html.escape(hexagram["nm"]["zh"])
    en_name = html.escape(hexagram["nm"]["en"])
    title = f"第 {n} 卦・{zh_name} — 擲爻問卦"
    description = f"《易經》第 {n} 卦「{zh_name}」（{en_name}）。查看完整六爻、本卦、變爻與變卦解讀。"
    canonical = f"{SITE_URL}/readings/{n}/"
    image = f"{SITE_URL}/assets/og/hex-{n}.png"
    target.write_text(f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="易 · 擲爻問卦">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
<style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#f7f6f1;color:#20302a;font-family:Arial,sans-serif;text-align:center}}
main{{max-width:34rem;padding:2rem}}h1{{color:#43836c}}a{{color:#bb4c39}}
</style>
<script>
(function(){{
  var cast = new URLSearchParams(location.search).get("cast");
  var destination = "../../" + (/^[6789]{{6}}$/.test(cast || "") ? "#cast=" + cast : "");
  location.replace(destination);
}})();
</script>
</head>
<body><main><h1>第 {n} 卦・{zh_name}</h1><p>{description}</p><p><a href="../../">進入擲爻問卦</a></p></main></body>
</html>
""", encoding="utf-8")


def main():
    pages = ROOT / "readings"
    cards = ROOT / "assets/og"
    pages.mkdir(exist_ok=True)
    cards.mkdir(parents=True, exist_ok=True)
    for hexagram in load_hexagrams():
        page_dir = pages / str(hexagram["n"])
        page_dir.mkdir(exist_ok=True)
        build_page(hexagram, page_dir / "index.html")
        build_card(hexagram, cards / f"hex-{hexagram['n']}.png")
    print("Generated 64 share pages and 64 Open Graph cards.")


if __name__ == "__main__":
    main()
