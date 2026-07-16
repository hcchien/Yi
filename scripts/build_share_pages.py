#!/usr/bin/env python3
"""Generate 64 hexagrams × 7 languages as static OG pages and cards."""

import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://hcchien.github.io/Yi"
LANGS = ("zh", "en", "ja", "ko", "es", "fr", "de")
FONT_PATHS = {
    "zh": "/System/Library/Fonts/STHeiti Medium.ttc",
    "ja": next(Path("/System/Library/Fonts").glob("ヒラギノ角ゴシック W6.ttc")),
    "ko": "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "latin": "/System/Library/Fonts/Supplemental/Arial.ttf",
}
COPY = {
    "zh": {
        "html": "zh-Hant", "eyebrow": "所得之卦 · 本卦", "number": "第 {n} 卦",
        "judgment": "卦辭", "site": "擲爻問卦",
        "description": "《易經》第 {n} 卦「{name}」。查看完整六爻、本卦、變爻與變卦解讀。",
    },
    "en": {
        "html": "en", "eyebrow": "YOUR READING · PRIMARY", "number": "HEXAGRAM {n}",
        "judgment": "JUDGMENT", "site": "I Ching Oracle",
        "description": "I Ching Hexagram {n}, “{name}”. View the six lines, changing lines, and transformed hexagram.",
    },
    "ja": {
        "html": "ja", "eyebrow": "得られた卦 · 本卦", "number": "第 {n} 卦",
        "judgment": "卦辞", "site": "擲爻問卦",
        "description": "易経第 {n} 卦「{name}」。六爻・変爻・之卦の解釈をご覧ください。",
    },
    "ko": {
        "html": "ko", "eyebrow": "얻은 괘 · 본괘", "number": "제 {n} 괘",
        "judgment": "괘사", "site": "척효문괘",
        "description": "주역 제 {n}괘 「{name}」. 육효, 변효와 지괘의 풀이를 확인하세요.",
    },
    "es": {
        "html": "es", "eyebrow": "TU LECTURA · PRINCIPAL", "number": "HEXAGRAMA {n}",
        "judgment": "DICTAMEN", "site": "Oráculo del I Ching",
        "description": "Hexagrama {n} del I Ching, «{name}». Consulta las seis líneas, las mutables y el hexagrama transformado.",
    },
    "fr": {
        "html": "fr", "eyebrow": "VOTRE TIRAGE · PRINCIPAL", "number": "HEXAGRAMME {n}",
        "judgment": "JUGEMENT", "site": "Oracle du Yi Jing",
        "description": "Hexagramme {n} du Yi Jing, « {name} ». Consultez les six traits, les traits mutables et l’hexagramme transformé.",
    },
    "de": {
        "html": "de", "eyebrow": "DEINE DEUTUNG · STAMMHEXAGRAMM", "number": "HEXAGRAMM {n}",
        "judgment": "URTEIL", "site": "I-Ging-Orakel",
        "description": "I-Ging-Hexagramm {n}, „{name}“. Sieh die sechs Linien, wandelnden Linien und das gewandelte Hexagramm.",
    },
}


def load_hexagrams():
    source = (ROOT / "js/data.js").read_text(encoding="utf-8")
    match = re.fullmatch(r"window\.YI = (.*);\s*", source, re.S)
    if not match:
        raise RuntimeError("Unable to parse js/data.js")
    return json.loads(match.group(1))


def font_for(lang, size):
    path = FONT_PATHS.get(lang, FONT_PATHS["latin"])
    return ImageFont.truetype(str(path), size)


def fit_font(draw, text, lang, max_width, start=68, minimum=32):
    for size in range(start, minimum - 1, -2):
        candidate = font_for(lang, size)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
    return font_for(lang, minimum)


def wrap_text(draw, text, font_obj, max_width, max_lines):
    words = text.split()
    if len(words) == 1:
        words = list(text)
    lines, current = [], ""
    for word in words:
        separator = "" if len(word) == 1 and unicodedata.east_asian_width(word) in "WFA" else " "
        trial = current + (separator if current else "") + word
        if current and draw.textbbox((0, 0), trial, font=font_obj)[2] > max_width:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
        else:
            current = trial
    if len(lines) < max_lines and current:
        lines.append(current)
    consumed = "".join(lines).replace(" ", "")
    if len(consumed) < len(text.replace(" ", "")) and lines:
        lines[-1] = lines[-1].rstrip(" ,.;，。") + "…"
    return lines


def draw_hexagram(draw, binary):
    x, y, width, height, gap = 58, 138, 172, 18, 14
    for index, bit in enumerate(reversed(binary)):
        line_y = y + index * (height + gap)
        if bit == "1":
            draw.rounded_rectangle((x, line_y, x + width, line_y + height), 2, fill="#20352d")
        else:
            segment = 72
            draw.rounded_rectangle((x, line_y, x + segment, line_y + height), 2, fill="#20352d")
            draw.rounded_rectangle((x + width - segment, line_y, x + width, line_y + height), 2, fill="#20352d")


def build_card(hexagram, lang, target):
    copy = COPY[lang]
    image = Image.new("RGB", (1200, 630), "#fbfbf8")
    draw = ImageDraw.Draw(image)
    draw.text((58, 62), copy["eyebrow"], font=font_for(lang, 27), fill="#e1644d")
    draw_hexagram(draw, hexagram["b"])

    name = hexagram["nm"][lang]
    draw.text((310, 130), copy["number"].format(n=hexagram["n"]), font=font_for(lang, 25), fill="#6a7872")
    draw.text((310, 180), name, font=fit_font(draw, name, lang, 780, 70, 34), fill="#20352d")
    secondary = hexagram["nm"]["zh"]
    draw.text((312, 285), secondary, font=font_for("zh", 27), fill="#e1644d")

    draw.rounded_rectangle((58, 382, 172, 432), 25, fill="#e4f2eb")
    label_font = font_for(lang, 22)
    label_box = draw.textbbox((0, 0), copy["judgment"], font=label_font)
    draw.text((115 - (label_box[2] - label_box[0]) / 2, 395), copy["judgment"], font=label_font, fill="#2f7059")

    draw.rectangle((58, 454, 63, 520), fill="#e1644d")
    classical_font = font_for("zh", 31)
    for i, line in enumerate(wrap_text(draw, hexagram["g"], classical_font, 1050, 2)):
        draw.text((88, 455 + i * 40), line, font=classical_font, fill="#20352d")

    plain_font = font_for(lang, 24)
    for i, line in enumerate(wrap_text(draw, hexagram["gx"][lang], plain_font, 1080, 2)):
        draw.text((58, 548 + i * 32), line, font=plain_font, fill="#68766f")
    image.save(target, optimize=True, quality=92)


def build_page(hexagram, lang, target):
    copy = COPY[lang]
    n = hexagram["n"]
    name = html.escape(hexagram["nm"][lang])
    title = f"{copy['number'].format(n=n)} · {name} — {copy['site']}"
    description = html.escape(copy["description"].format(n=n, name=name))
    canonical = f"{SITE_URL}/readings/{lang}/{n}/"
    image = f"{SITE_URL}/assets/og/{lang}/hex-{n}.png"
    root = "../../../"
    target.write_text(f"""<!DOCTYPE html>
<html lang="{copy['html']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{html.escape(copy['site'])}">
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
  var destination = "{root}?lang={lang}" + (/^[6789]{{6}}$/.test(cast || "") ? "#cast=" + cast : "");
  location.replace(destination);
}})();
</script>
</head>
<body><main><h1>{title}</h1><p>{description}</p><p><a href="{root}?lang={lang}">{html.escape(copy['site'])}</a></p></main></body>
</html>
""", encoding="utf-8")


def main():
    pages = ROOT / "readings"
    cards = ROOT / "assets/og"
    if pages.exists():
        shutil.rmtree(pages)
    if cards.exists():
        shutil.rmtree(cards)
    pages.mkdir()
    cards.mkdir(parents=True)
    for lang in LANGS:
        (pages / lang).mkdir()
        (cards / lang).mkdir()
        for hexagram in load_hexagrams():
            page_dir = pages / lang / str(hexagram["n"])
            page_dir.mkdir()
            build_page(hexagram, lang, page_dir / "index.html")
            build_card(hexagram, lang, cards / lang / f"hex-{hexagram['n']}.png")
    print("Generated 448 localized share pages and 448 Open Graph cards.")


if __name__ == "__main__":
    main()
