"""Build a simplified Chinese -> English sentence-pair file from OPUS OpenSubtitles.

Input:  the aligned `en-zh.en` / `en-zh.zh` files from
        https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2016/moses/en-zh.txt.zip
Output: a tab-separated file with one `Chinese<TAB>English` pair per line,
        fully converted to simplified Chinese.

Usage:
    # the 500k simplest sentence pairs
    python src/prepare_data.py --src-dir <raw dir> --out data/zh-en.txt \
        --order simplest --max-pairs 500000
"""

from __future__ import annotations

import argparse
import heapq
import random
import re
import sys
from pathlib import Path

try:
    import opencc
except ImportError:  # pragma: no cover - handled at runtime
    opencc = None

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LATIN = re.compile(r"[A-Za-z]")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TERMINAL = re.compile(r"[。！？!?]$")
ASTRAL = re.compile(r"[\U00010000-\U0010FFFF]")
ELLIPSIS = ("...", "\u2026")
# Subtitle files are sometimes mis-encoded and leak kana, box drawing or other
# symbols into the text. Keep only characters that belong in Chinese / English.
DISALLOWED_ZH = re.compile(
    r"[^\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\ufe30-\ufe4f"
    r"\uff00-\uffef\u2018\u2019\u201c\u201d\u2014\u2026\u00b7\x20-\x7e]"
)
DISALLOWED_EN = re.compile(
    r"[^\x20-\x7e\u00a0-\u00ff\u2018\u2019\u201c\u201d\u2013\u2014\u2026]"
)
ALLOWED_RATIO = 0.98
# Subtitle speaker markers that leak into the sentence text.
LEADING_NOISE = re.compile(r"^[\-\u2013\u2014!\uff01\u00b7\u2022]")
# Quotes left over from the source subtitle markup.
LEADING_QUOTE = "\"\u201c\u2018'"
EN_TERMINAL = re.compile(r"[.!?][\"'\u201d\u2019)]?$")
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")
# Capitalised words that are ordinary English rather than names or places.
COMMON_CAPS = frozenset({
    "I", "I'm", "I've", "I'll", "I'd", "A", "An", "The", "OK", "Ok", "Oh", "Ah",
    "Eh", "Um", "Uh", "Hey", "Hi", "Hello", "God", "Lord", "Mr", "Mrs", "Ms",
    "Dr", "Sir", "Madam", "Mister", "Miss",
})


def traditional_regex() -> re.Pattern[str] | None:
    """Character class matching every traditional character OpenCC knows about.

    Only ~7% of OpenSubtitles lines contain traditional characters, so testing a
    cheap regex first lets us skip the expensive conversion for the rest.
    """
    if opencc is None:
        return None
    table = Path(opencc.__file__).parent / "dictionary" / "TSCharacters.txt"
    if not table.is_file():
        return None
    chars: set[str] = set()
    with table.open(encoding="utf-8") as handle:
        for line in handle:
            key = line.split("\t", 1)[0].strip()
            if len(key) == 1:
                chars.add(key)
    if not chars:
        return None
    return re.compile("[" + re.escape("".join(sorted(chars))) + "]")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-dir", required=True, type=Path,
                   help="directory holding en-zh.en and en-zh.zh")
    p.add_argument("--out", required=True, type=Path,
                   help="output TSV path")
    p.add_argument("--max-pairs", type=int, default=500_000,
                   help="keep at most this many pairs (default: 500000)")
    p.add_argument("--order", choices=("simplest", "random"), default="simplest",
                   help="'simplest' keeps the shortest pairs, 'random' shuffles")
    p.add_argument("--dedupe", choices=("source", "pair"), default="source",
                   help="'source' keeps one translation per Chinese sentence")
    p.add_argument("--oversample", type=float, default=2.0,
                   help="candidate pool size as a multiple of --max-pairs")
    p.add_argument("--min-zh-chars", type=int, default=4)
    p.add_argument("--min-zh-cjk", type=int, default=6,
                   help="minimum number of Chinese characters (default: 6)")
    p.add_argument("--max-zh-chars", type=int, default=20)
    p.add_argument("--min-en-words", type=int, default=3,
                   help="minimum number of English words (default: 3)")
    p.add_argument("--max-en-chars", type=int, default=120)
    p.add_argument("--max-en-words", type=int, default=12)
    p.add_argument("--allow-unterminated", dest="require_terminal_punct",
                   action="store_false",
                   help="keep lines whose Chinese has no closing punctuation")
    p.add_argument("--keep-ellipsis", dest="drop_ellipsis", action="store_false",
                   help="keep truncated lines (leading dash, '...', '…')")
    p.add_argument("--keep-proper-nouns", dest="drop_proper_nouns",
                   action="store_false",
                   help="keep lines containing names and other proper nouns")
    p.add_argument("--allow-english-fragments", dest="require_en_terminal",
                   action="store_false",
                   help="keep lines whose English has no closing punctuation")
    p.add_argument("--allow-latin-in-chinese", dest="reject_latin_zh",
                   action="store_false",
                   help="keep Chinese lines that contain stray latin letters")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-simplify", action="store_true",
                   help="skip traditional -> simplified conversion")
    return p.parse_args()


def is_clean(text: str) -> bool:
    return bool(text) and not CONTROL.search(text)


def too_dirty(text: str, disallowed: re.Pattern[str]) -> bool:
    """True when too much of `text` falls outside the allowed character set."""
    if disallowed.search(text) is None:
        return False
    return len(disallowed.findall(text)) / len(text) > 1 - ALLOWED_RATIO


def acceptable(zh: str, en: str, args: argparse.Namespace) -> bool:
    # Rare extension-plane characters are almost always subtitle noise.
    if ASTRAL.search(zh) or ASTRAL.search(en):
        return False
    if too_dirty(zh, DISALLOWED_ZH) or too_dirty(en, DISALLOWED_EN):
        return False
    if LEADING_NOISE.match(zh) or en.startswith("-"):
        return False
    if zh[0] in LEADING_QUOTE:
        return False
    # Subtitle files carry markup such as "#", "(德语)", "**" or a stray "," in
    # front of the text; a real sentence starts with a character or a digit.
    if not (CJK.match(zh) or zh[0].isdigit()):
        return False
    # Stray latin text inside the Chinese side is subtitle markup, not content.
    if args.reject_latin_zh and LATIN.search(zh):
        return False
    if not (args.min_zh_chars <= len(zh) <= args.max_zh_chars):
        return False
    if not (1 <= len(en) <= args.max_en_chars):
        return False
    en_words = len(en.split())
    if en_words > args.max_en_words or en_words < args.min_en_words:
        return False
    if not CJK.search(zh) or not LATIN.search(en):
        return False
    # Require enough Chinese so tiny fragments drop out.
    if len(CJK.findall(zh)) < args.min_zh_cjk:
        return False
    # Subtitles routinely cut sentences off or interleave two speakers; lines
    # ending in proper punctuation are far better aligned on average.
    if args.require_terminal_punct and not TERMINAL.search(zh):
        return False
    if args.drop_ellipsis and (any(mark in zh for mark in ELLIPSIS) or
                               any(mark in en for mark in ELLIPSIS)):
        return False
    # A finishing period/question mark means the subtitle line was not cut mid
    # sentence, which correlates with a correct alignment.
    if args.require_en_terminal and not EN_TERMINAL.search(en):
        return False
    # Film dialogue addresses people by name constantly; those pairs teach the
    # model little and flood the vocabulary with rare tokens.
    if args.drop_proper_nouns:
        tokens = TOKEN.findall(en)
        if any(token[0].isupper() and token not in COMMON_CAPS
               for token in tokens[1:]):
            return False
    return True


def simplicity(zh: str, en: str) -> int:
    """Lower is simpler: Chinese characters plus English words."""
    return len(CJK.findall(zh)) + len(en.split())


def describe(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return "no pairs"
    zh_lens = sorted(len(CJK.findall(zh)) for zh, _ in pairs)
    en_lens = sorted(len(en.split()) for _, en in pairs)
    pick = lambda values, q: values[min(len(values) - 1, int(len(values) * q))]
    return (f"chinese chars  min={zh_lens[0]} median={pick(zh_lens, 0.5)} "
            f"p90={pick(zh_lens, 0.9)} max={zh_lens[-1]} | "
            f"english words  min={en_lens[0]} median={pick(en_lens, 0.5)} "
            f"p90={pick(en_lens, 0.9)} max={en_lens[-1]}")


def main() -> int:
    args = parse_args()

    zh_path = args.src_dir / "en-zh.zh"
    en_path = args.src_dir / "en-zh.en"
    for path in (zh_path, en_path):
        if not path.is_file():
            print(f"error: missing input file {path}", file=sys.stderr)
            return 1

    converter = None
    trad = None
    if not args.no_simplify:
        if opencc is None:
            print("error: opencc is required for t2s conversion; "
                  "install it with `pip install opencc-python-reimplemented` "
                  "or pass --no-simplify", file=sys.stderr)
            return 1
        converter = opencc.OpenCC("t2s")
        trad = traditional_regex()

    # Bounded heap keeps memory flat on multi-million line input.
    keep = max(args.max_pairs, int(args.max_pairs * args.oversample))
    heap: list[tuple[int, int, str, str]] = []
    shuffled: list[tuple[str, str]] = []
    total = 0
    converted = 0
    serial = 0

    with zh_path.open(encoding="utf-8") as fzh, en_path.open(encoding="utf-8") as fen:
        for zh_line, en_line in zip(fzh, fen):
            total += 1
            zh = zh_line.strip()
            en = " ".join(en_line.split())
            if not is_clean(zh) or not is_clean(en):
                continue

            # Convert first: OpenCC can map a traditional character onto a rare
            # extension-plane simplified character, which the filters must see.
            if converter is not None and (trad is None or trad.search(zh)):
                simplified = converter.convert(zh)
                if simplified != zh:
                    converted += 1
                zh = simplified

            if not acceptable(zh, en, args):
                continue

            if args.order == "simplest":
                serial += 1
                item = (-simplicity(zh, en), serial, zh, en)
                if len(heap) < keep:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)
            else:
                shuffled.append((zh, en))

    if args.order == "simplest":
        candidates = sorted(((zh, en) for _, _, zh, en in heap),
                            key=lambda pair: (simplicity(*pair), pair[0]))
    else:
        random.Random(args.seed).shuffle(shuffled)
        candidates = shuffled

    seen_source: set[str] = set()
    seen_pair: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str]] = []
    for zh, en in candidates:
        if args.dedupe == "pair":
            if (zh, en) in seen_pair:
                continue
            seen_pair.add((zh, en))
        elif zh in seen_source:
            continue
        seen_source.add(zh)
        pairs.append((zh, en))
        if len(pairs) >= args.max_pairs:
            break

    # Final pass over the selected pairs only: the fast pre-filter above can miss
    # the occasional phrase-level conversion, so make the output exactly simplified.
    if converter is not None:
        for index, (zh, en) in enumerate(pairs):
            simplified = converter.convert(zh)
            if simplified != zh:
                pairs[index] = (simplified, en)

    if len(pairs) < args.max_pairs:
        print(f"warning: only {len(pairs):,} pairs survived; "
              f"raise --oversample or widen the length limits", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        for zh, en in pairs:
            handle.write(f"{zh}\t{en}\n")

    print(f"read          : {total:,} aligned lines")
    print(f"t2s converted : {converted:,} lines")
    print(f"written       : {len(pairs):,} pairs -> {args.out}")
    print(f"shape         : {describe(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
