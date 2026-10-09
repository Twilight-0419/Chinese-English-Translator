"""Canonical punctuation and text normalisation for the zh-en dataset.

The source corpus mixes full width and half width punctuation and carries a long
tail of encoding artefacts (``´``, `` ` ``, ``︰``, ``¶``, ``§``, ``♪``, ...).
Left alone, every one of those becomes its own token in the vocabulary.

So every punctuation character is mapped onto one of the two small canonical
sets below. A character that has no canonical form is deleted.

    Chinese:  。 ， ！ ？ 、 ： ； （ ） 《 》 … “ ” ‘ ’ %
    English:  . , ! ? ; : ' " - ( ) % $

Full width and half width forms are unified, decimal points and thousand
separators inside numbers are handled as part of the numeral, and spaces that
sit next to a Chinese character are dropped, because Chinese does not separate
words with spaces.
"""

from __future__ import annotations

import re
import unicodedata

# The complete punctuation inventory used in the dataset.
CHINESE_PUNCT = "。，！？、：；（）《》…“”‘’%"
ENGLISH_PUNCT = ".,!?;:'\"-()%$"

CJK_RANGES = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK = re.compile(f"[{CJK_RANGES}]")
# Ideographs plus Chinese punctuation: anything that marks Chinese context.
ZH_CONTEXT = re.compile(f"[{CJK_RANGES}{re.escape(CHINESE_PUNCT)}]")
MULTI_SPACE = re.compile(r" {2,}")

# Chinese variants that map onto a canonical Chinese form.
ZH_MAP = {
    ",": "，", "?": "？", "!": "！", ":": "：", ";": "；",
    "(": "（", ")": "）", ".": "。", "％": "%",
    "「": "“", "」": "”", "『": "“", "』": "”", "〝": "“", "〞": "”",
    "【": "（", "】": "）", "〔": "（", "〕": "）",
    "[": "（", "]": "）", "［": "（", "］": "）",
}

# English variants that map onto a canonical English form.
EN_MAP = {
    "´": "'", "`": "'", "′": "'", "‘": "'", "’": "'", "＇": "'",
    "–": "-", "—": "-", "−": "-",
    "[": "(", "]": ")",
    "！": "!", "？": "?", "，": ",", "。": ".", "：": ":", "；": ";",
    "（": "(", "）": ")", "％": "%", "＄": "$",
}


def normalize_zh(text: str) -> str:
    """Return `text` with canonical Chinese punctuation and no stray symbols."""
    out: list[str] = []
    double_open = True
    single_open = True

    for index, ch in enumerate(text):
        prev_ch = text[index - 1] if index else ""
        next_ch = text[index + 1] if index + 1 < len(text) else ""

        if ch == " ":
            # Chinese does not separate words with spaces.
            if ZH_CONTEXT.match(prev_ch) or ZH_CONTEXT.match(next_ch):
                continue
            if out and out[-1] == " ":
                continue
            out.append(" ")
            continue

        if ch in ('"', "\uff02"):
            out.append("“" if double_open else "”")
            double_open = not double_open
            continue

        if ch in ("'", "\uff07"):
            out.append("‘" if single_open else "’")
            single_open = not single_open
            continue

        # Inside a numeral a "." is a decimal point and belongs to the number;
        # a "," is a thousands separator that Chinese text does not use.
        if ch == "." and prev_ch.isdigit() and next_ch.isdigit():
            out.append(ch)
            continue
        if ch == "," and prev_ch.isdigit() and next_ch.isdigit():
            continue

        if ch in CHINESE_PUNCT:
            if ch == "“":
                double_open = False
            elif ch == "”":
                double_open = True
            out.append(ch)
            continue

        mapped = ZH_MAP.get(ch)
        if mapped is not None:
            out.append(mapped)
            continue

        # Anything else that is a symbol, separator or unlisted punctuation has
        # no canonical form and is dropped.
        if unicodedata.category(ch)[0] in "PSZ":
            continue

        out.append(ch)

    return MULTI_SPACE.sub(" ", "".join(out)).strip()


def normalize_en(text: str) -> str:
    """Return `text` with canonical English punctuation and no stray symbols."""
    out: list[str] = []
    for ch in text:
        if ch in ENGLISH_PUNCT or ch == " ":
            out.append(ch)
            continue
        mapped = EN_MAP.get(ch)
        if mapped is not None:
            out.append(mapped)
            continue
        if unicodedata.category(ch)[0] in "PSZ":
            continue
        out.append(ch)
    return MULTI_SPACE.sub(" ", "".join(out)).strip()


def inventory(strings) -> set[str]:
    """Return every punctuation character present in `strings`."""
    found: set[str] = set()
    for text in strings:
        found.update(ch for ch in text if unicodedata.category(ch)[0] in "PS")
    return found
