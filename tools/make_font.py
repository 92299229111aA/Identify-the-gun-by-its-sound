"""Subset Noto Serif SC to the characters actually used, as woff2 + base64."""
import base64
import json
import os
import re
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
SRC = os.path.join(PROJECT, "fonts", "NotoSerifSC-SemiBold.otf")
OUT_WOFF2 = os.path.join(PROJECT, "fonts", "subset.woff2")
OUT_B64 = os.path.join(PROJECT, "fonts", "subset.b64")


def chars_from_html(path):
    html = open(path, encoding="utf-8").read()
    html = re.sub(r"(?s)<script.*?</script>", " ", html)
    html = re.sub(r"(?s)<style.*?</style>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text


def main():
    html_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT, "game.html")
    text = chars_from_html(html_path)
    # ASCII printable + all CJK / punctuation actually present
    chars = set(text)
    chars.update(chr(c) for c in range(0x20, 0x7F))
    chars.update("·—…“”‘’《》〈〉、。，！？：；（）【】「」")
    chars = {c for c in chars if c.strip() or c == " "}
    text_arg = "".join(sorted(chars))

    font = TTFont(SRC)
    options = subset.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text_arg)
    subsetter.subset(font)
    font.flavor = "woff2"
    font.save(OUT_WOFF2)

    raw = open(OUT_WOFF2, "rb").read()
    b64 = base64.b64encode(raw).decode("ascii")
    with open(OUT_B64, "w", encoding="utf-8") as handle:
        handle.write(b64)
    print(f"chars={len(chars)} woff2={len(raw)/1024:.1f} KB base64={len(b64)/1024:.1f} KB")
    print("wrote", OUT_WOFF2, "and", OUT_B64)


if __name__ == "__main__":
    main()
