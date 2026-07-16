#!/usr/bin/env python3
"""Build the browser data bundle from public-domain Zhouyi text."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/tmp/zhouyi.txt")
EN_SOURCE = Path("/tmp/yi-source/data/hexagrams.json")

NAMES_ZH = "乾 坤 屯 蒙 需 訟 師 比 小畜 履 泰 否 同人 大有 謙 豫 隨 蠱 臨 觀 噬嗑 賁 剝 復 無妄 大畜 頤 大過 坎 離 咸 恆 遯 大壯 晉 明夷 家人 睽 蹇 解 損 益 夬 姤 萃 升 困 井 革 鼎 震 艮 漸 歸妹 豐 旅 巽 兌 渙 節 中孚 小過 既濟 未濟".split()
NAMES = {
    "en": "The Creative|The Receptive|Difficulty at the Beginning|Youthful Folly|Waiting|Conflict|The Army|Holding Together|Small Taming|Treading|Peace|Standstill|Fellowship|Great Possession|Modesty|Enthusiasm|Following|Repairing Decay|Approach|Contemplation|Biting Through|Grace|Splitting Apart|Return|Innocence|Great Taming|Nourishment|Great Exceeding|The Abysmal|The Clinging|Influence|Duration|Retreat|Great Power|Progress|Darkening of the Light|The Family|Opposition|Obstruction|Deliverance|Decrease|Increase|Breakthrough|Coming to Meet|Gathering|Pushing Upward|Oppression|The Well|Revolution|The Cauldron|Shock|Keeping Still|Development|The Marrying Maiden|Abundance|The Wanderer|The Gentle|The Joyous|Dispersion|Limitation|Inner Truth|Small Exceeding|After Completion|Before Completion".split("|"),
    "ja": "乾為天|坤為地|水雷屯|山水蒙|水天需|天水訟|地水師|水地比|風天小畜|天澤履|地天泰|天地否|天火同人|火天大有|地山謙|雷地豫|澤雷随|山風蠱|地澤臨|風地観|火雷噬嗑|山火賁|山地剝|地雷復|天雷無妄|山天大畜|山雷頤|澤風大過|坎為水|離為火|澤山咸|雷風恒|天山遯|雷天大壮|火地晋|地火明夷|風火家人|火澤睽|水山蹇|雷水解|山澤損|風雷益|澤天夬|天風姤|澤地萃|地風升|澤水困|水風井|澤火革|火風鼎|震為雷|艮為山|風山漸|雷澤帰妹|雷火豊|火山旅|巽為風|兌為澤|風水渙|水澤節|風澤中孚|雷山小過|水火既済|火水未済".split("|"),
    "ko": "건|곤|둔|몽|수|송|사|비|소축|리|태|비|동인|대유|겸|예|수|고|림|관|서합|비|박|복|무망|대축|이|대과|감|리|함|항|둔|대장|진|명이|가인|규|건|해|손|익|쾌|구|췌|승|곤|정|혁|정|진|간|점|귀매|풍|려|손|태|환|절|중부|소과|기제|미제".split("|"),
    "es": "Lo Creativo|Lo Receptivo|Dificultad inicial|La Inexperiencia|La Espera|El Conflicto|El Ejército|La Unión|La fuerza de lo pequeño|El Porte|La Paz|El Estancamiento|La Comunidad|La Gran Posesión|La Modestia|El Entusiasmo|El Seguimiento|Reparar lo corrompido|El Acercamiento|La Contemplación|Atravesar mordiendo|La Gracia|La Desintegración|El Retorno|La Inocencia|La fuerza de lo grande|La Nutrición|El exceso de lo grande|Lo Abismal|Lo Adherente|La Influencia|La Duración|La Retirada|El Gran Poder|El Progreso|El oscurecimiento de la luz|La Familia|La Oposición|El Impedimento|La Liberación|La Disminución|El Aumento|La Resolución|El Encuentro|La Reunión|El Ascenso|La Opresión|El Pozo|La Revolución|El Caldero|La Conmoción|La Quietud|El Desarrollo|La Doncella|La Abundancia|El Viajero|Lo Suave|Lo Gozoso|La Dispersión|La Limitación|La Verdad Interior|El exceso de lo pequeño|Después de la consumación|Antes de la consumación".split("|"),
    "fr": "Le Créateur|Le Réceptif|La Difficulté initiale|La Folie juvénile|L’Attente|Le Conflit|L’Armée|L’Union|Le Petit apprivoise|La Marche|La Paix|La Stagnation|La Communauté|Le Grand Avoir|La Modestie|L’Enthousiasme|La Suite|Réparer le corrompu|L’Approche|La Contemplation|Mordre au travers|La Grâce|L’Éclatement|Le Retour|L’Innocence|Le Grand apprivoise|La Nourriture|Le Grand excès|L’Abîme|Ce qui s’attache|L’Influence|La Durée|La Retraite|La Grande Puissance|Le Progrès|L’Obscurcissement|La Famille|L’Opposition|L’Obstacle|La Libération|La Diminution|L’Augmentation|La Percée|La Rencontre|Le Rassemblement|La Poussée|L’Oppression|Le Puits|La Révolution|Le Chaudron|L’Ébranlement|L’Immobilisation|Le Développement|L’Épousée|L’Abondance|Le Voyageur|Le Doux|Le Joyeux|La Dispersion|La Limitation|La Vérité intérieure|Le Petit excès|Après l’accomplissement|Avant l’accomplissement".split("|"),
    "de": "Das Schöpferische|Das Empfangende|Die Anfangsschwierigkeit|Die Jugendtorheit|Das Warten|Der Streit|Das Heer|Das Zusammenhalten|Des Kleinen Zähmungskraft|Das Auftreten|Der Friede|Die Stockung|Gemeinschaft|Der Besitz von Großem|Die Bescheidenheit|Die Begeisterung|Die Nachfolge|Die Arbeit am Verdorbenen|Die Annäherung|Die Betrachtung|Das Durchbeißen|Die Anmut|Die Zersplitterung|Die Wiederkehr|Die Unschuld|Des Großen Zähmungskraft|Die Ernährung|Des Großen Übergewicht|Das Abgründige|Das Haftende|Die Einwirkung|Die Dauer|Der Rückzug|Des Großen Macht|Der Fortschritt|Die Verfinsterung des Lichts|Die Sippe|Der Gegensatz|Das Hemmnis|Die Befreiung|Die Minderung|Die Mehrung|Der Durchbruch|Das Entgegenkommen|Die Sammlung|Das Empordringen|Die Bedrängnis|Der Brunnen|Die Umwälzung|Der Tiegel|Das Erregende|Das Stillhalten|Die Entwicklung|Das heiratende Mädchen|Die Fülle|Der Wanderer|Das Sanfte|Das Heitere|Die Auflösung|Die Beschränkung|Innere Wahrheit|Des Kleinen Übergewicht|Nach der Vollendung|Vor der Vollendung".split("|"),
}

LINE_PREFIX = re.compile(r"^(初[六九]|[六九][二三四五]|上[六九])[,，]")
HEX_HEAD = re.compile(r"^(\d{1,2})[.、]?\s+([^，,]+)[，,](.+)$")

TEMPLATES = {
    "zh": ("此卦提醒你把握「{name}」的核心精神：先辨明時位，再以正道行動。", "第 {pos} 爻著重此刻所處的位置與分寸；結合原文，觀察何時宜進、宜守或宜變。"),
    "ja": ("「{name}」の中心は、時と立場を見極め、正しい道を選ぶことです。", "第{pos}爻は今の位置と節度を示します。原文を手掛かりに、進む・守る・改める時を見極めてください。"),
    "ko": ("「{name}」의 핵심은 때와 처지를 살피고 바른 길로 움직이는 데 있습니다.", "제 {pos}효는 현재의 위치와 정도를 강조합니다. 원문을 비추어 나아갈지, 지킬지, 바꿀지를 살피세요."),
    "es": ("El centro de «{name}» es reconocer el momento y actuar con rectitud.", "La línea {pos} subraya la posición y la medida: usa el texto clásico para decidir si conviene avanzar, esperar o cambiar."),
    "fr": ("Le cœur de « {name} » est de reconnaître le moment juste et d’agir avec droiture.", "Le trait {pos} insiste sur la place et la mesure : lisez le texte classique pour discerner s’il faut avancer, attendre ou changer."),
    "de": ("Der Kern von „{name}“ liegt darin, den richtigen Zeitpunkt zu erkennen und aufrichtig zu handeln.", "Linie {pos} betont Stellung und Maß. Der klassische Text hilft zu erkennen, ob Vorangehen, Abwarten oder Wandel angemessen ist."),
}

def parse_chinese():
    lines = [x.strip() for x in SOURCE.read_text(encoding="utf-8").splitlines() if x.strip()]
    starts = [(i, int(m.group(1)), m) for i, x in enumerate(lines) if (m := HEX_HEAD.match(x)) and 1 <= int(m.group(1)) <= 64]
    out = {}
    for idx, (start, number, m) in enumerate(starts):
        if number in out:
            continue
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        section = lines[start:end]
        yao = [x for x in section[1:] if LINE_PREFIX.match(x)][:6]
        if len(yao) != 6:
            raise RuntimeError(f"hexagram {number}: found {len(yao)} lines")
        out[number] = {"judgment": f"{m.group(2)}，{m.group(3)}", "lines": yao}
    return out

def main():
    cn = parse_chinese()
    en = json.loads(EN_SOURCE.read_text(encoding="utf-8"))
    data = []
    for n in range(1, 65):
        eh = en[str(n)]
        names = {"zh": NAMES_ZH[n-1], **{k: v[n-1] for k, v in NAMES.items()}}
        gx = {"en": eh["judgment"]["text"].replace("\n", " ")}
        for lang in ("zh", "ja", "ko", "es", "fr", "de"):
            gx[lang] = TEMPLATES[lang][0].format(name=names[lang])
        line_items = []
        for pos, raw in enumerate(cn[n]["lines"], 1):
            lx = {"en": eh["lines"][str(pos)]["text"].replace("\n", " ")}
            for lang in ("zh", "ja", "ko", "es", "fr", "de"):
                lx[lang] = TEMPLATES[lang][1].format(pos=pos)
            line_items.append([raw, lx])
        data.append({
            "n": n,
            "b": eh["binary"][::-1],
            "zi": eh["unicode"],
            "nm": names,
            "g": cn[n]["judgment"],
            "gx": gx,
            "ls": line_items,
        })
    target = ROOT / "js" / "data.js"
    target.write_text("window.YI = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

if __name__ == "__main__":
    main()
