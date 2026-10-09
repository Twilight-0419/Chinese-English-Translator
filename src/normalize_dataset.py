"""Re-normalise an existing `Chinese<TAB>English` file in place.

Applies `text_norm.normalize_zh` / `normalize_en` to every pair, drops the pairs
that no longer end in terminal punctuation, and de-duplicates again because
unifying punctuation can collapse two rows into one.

Usage:
    python src/normalize_dataset.py --path data/zh-en.txt
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import text_norm

TERMINAL = ("。", "！", "？", ".", "!", "?")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--path", type=Path, default=Path("data/zh-en.txt"))
    p.add_argument("--dry-run", action="store_true",
                   help="report the changes without writing the file")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.path.is_file():
        print(f"error: {args.path} not found", file=sys.stderr)
        return 1

    before_zh: set[str] = set()
    before_en: set[str] = set()
    after_zh: set[str] = set()
    after_en: set[str] = set()
    changed = 0
    dropped_terminal = 0
    dropped_duplicate = 0
    total = 0

    seen: set[str] = set()
    rows: list[tuple[str, str]] = []

    with args.path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.count("\t") != 1:
                continue
            total += 1
            zh, en = line.split("\t")
            before_zh.update(ch for ch in zh if ch.isprintable() and not ch.isalnum())
            before_en.update(ch for ch in en if ch.isprintable() and not ch.isalnum())

            new_zh = text_norm.normalize_zh(zh)
            new_en = text_norm.normalize_en(en)
            if new_zh != zh or new_en != en:
                changed += 1
            after_zh.update(ch for ch in new_zh if ch.isprintable() and not ch.isalnum())
            after_en.update(ch for ch in new_en if ch.isprintable() and not ch.isalnum())

            if not new_zh.endswith(TERMINAL):
                dropped_terminal += 1
                continue
            if new_zh in seen:
                dropped_duplicate += 1
                continue
            seen.add(new_zh)
            rows.append((new_zh, new_en))

    print(f"read              : {total:,}")
    print(f"rows changed      : {changed:,}")
    print(f"dropped (no end)  : {dropped_terminal:,}")
    print(f"dropped (dup)     : {dropped_duplicate:,}")
    print(f"kept              : {len(rows):,}")
    print(f"chinese punct     : {len(before_zh)} -> {len(after_zh)} distinct")
    print(f"english punct     : {len(before_en)} -> {len(after_en)} distinct")
    print(f"chinese inventory : {''.join(sorted(after_zh))}")
    print(f"english inventory : {''.join(sorted(after_en))}")

    if args.dry_run:
        print("dry run, nothing written")
        return 0

    with args.path.open("w", encoding="utf-8", newline="\n") as handle:
        for zh, en in rows:
            handle.write(f"{zh}\t{en}\n")
    print(f"written           : {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
