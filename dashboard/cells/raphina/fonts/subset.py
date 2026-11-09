"""Rebuild the font subsets in this folder from ../index.html.

Run after you add winners to AWARDS:
    pip install fonttools brotli
    python subset.py <dir with the source .ttf files>

Source fonts (SIL OFL, from github.com/google/fonts/tree/main/ofl):
    JetBrainsMono[wght].ttf, NotoSansJP[wght].ttf, NotoSansSC[wght].ttf,
    NanumGothicCoding-Regular.ttf, NanumGothicCoding-Bold.ttf
"""
import re
import sys
from pathlib import Path

from fontTools import subset

HERE = Path(__file__).resolve().parent
CJK = 0x2E80  # first code point of the CJK blocks

# source file -> (output file, which characters it gets)
FONTS = {
    "JetBrainsMono[wght].ttf": ("latin.woff2", "latin"),
    "NotoSansJP[wght].ttf": ("ja.woff2", "ja"),
    "NotoSansSC[wght].ttf": ("zh.woff2", "zh"),
    "NanumGothicCoding-Regular.ttf": ("ko-400.woff2", "ko"),
    "NanumGothicCoding-Bold.ttf": ("ko-700.woff2", "ko"),
}


# A subset is a modified font, and the OFL forbids giving it a Reserved Font
# Name. Nanum Gothic Coding reserves "Nanum" and "NanumGothic", so its subsets
# get a new name (also used in index.html). See OFL.txt.
RENAME = {
    "NanumGothicCoding-Regular.ttf": ("Coding KR", "Regular"),
    "NanumGothicCoding-Bold.ttf": ("Coding KR", "Bold"),
}


def rename(font, names):
    family, style = names
    ps = f"{family.replace(' ', '')}-{style}"
    for nid, value in {1: family, 3: ps, 4: f"{family} {style}", 6: ps, 16: family}.items():
        font["name"].removeNames(nameID=nid)
        font["name"].setName(value, nid, 3, 1, 0x409)


def chars_by_lang(html):
    """Group the CJK characters of each AWARDS entry by its lang tag."""
    groups = {"latin": set(map(chr, range(0x20, 0x7F)))}
    lang = None
    for line in html.splitlines():
        m = re.search(r"lang: '(\w+)'", line)
        if m:
            lang = m.group(1)
        for c in line:
            if ord(c) < CJK:
                groups["latin"].add(c)
            elif lang:
                groups.setdefault(lang, set()).add(c)
    return groups


def main(src):
    groups = chars_by_lang((HERE.parent / "index.html").read_text("utf-8"))
    for name, (out, group) in FONTS.items():
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]  # keep the copyright and OFL license entries
        font = subset.load_font(str(Path(src) / name), opts)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(groups.get(group, ()))))
        sub.subset(font)
        if name in RENAME:
            rename(font, RENAME[name])
        subset.save_font(font, str(HERE / out), opts)
        print(f"{out}: {len(groups.get(group, ()))} chars, {(HERE / out).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1])
