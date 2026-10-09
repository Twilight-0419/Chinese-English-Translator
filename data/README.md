# Dataset: `zh-en.txt`

Chinese to English sentence pairs, one pair per line, the two sides separated by a
single tab character:

```
中文句子	English sentence
```

Encoding is UTF-8 without BOM, line endings are LF.

## Source

| | |
|---|---|
| Corpus | [OPUS](https://opus.nlpl.eu/) `OpenSubtitles` v2016, `moses` release |
| Download | `https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2016/moses/en-zh.txt.zip` |
| Archive size | 285.3 MB |
| Aligned pairs in source | 9,304,777 |
| Underlying data | subtitles collected from opensubtitles.org |

OPUS does not attach a single standard open licence to the OpenSubtitles corpus.
Check the OPUS and opensubtitles.org terms before redistributing this data or
using it commercially.

## How it was built

`src/prepare_data.py` reads the two line-aligned source files, then:

1. Converts traditional Chinese to simplified Chinese with OpenCC (`t2s`). The
   source is mixed script, so this is required for a consistent vocabulary.
2. Canonicalises punctuation on both sides through `src/text_norm.py`. The source
   mixes full width and half width marks (`？` vs `?`, `！` vs `!`) and carries
   encoding artefacts (`´`, `` ` ``, `︰`, `¶`, `§`, `♪`). Every punctuation
   character is mapped onto the small canonical set documented below, and one
   that has no canonical form is deleted.
3. Keeps only pairs that look like complete, simple sentences:
   - 6 or more Chinese characters, English 3 to 12 words
   - both sides end in terminal punctuation, so neither was cut mid sentence
   - the Chinese starts with a character or digit, not with subtitle markup
     (`#`, `(德语)`, `**`, a stray `,` or `.`)
   - no leading speaker markers, no ellipsis, no `...`, no leftover quote marks
   - no stray latin letters inside the Chinese side
   - only characters that belong in Chinese or English text (this drops the
     mis-encoded subtitle lines that leak kana or symbol junk)
   - no names or other proper nouns, detected as a capitalised word inside the
     English sentence. Film dialogue is full of character names, and they teach
     a small model little while bloating the vocabulary.
4. Deduplicates on the Chinese sentence, so each source sentence has one English
   translation rather than a dozen competing variants.
5. Ranks the survivors by simplicity and keeps the shortest ones.

Reproduce with:

```bash
python src/prepare_data.py --src-dir <raw en-zh dir> --out data/zh-en.txt \
    --order simplest --max-pairs 500000
```

An already built file can be re-normalised in place without touching the raw
corpus:

```bash
python src/normalize_dataset.py --path data/zh-en.txt
```

## Punctuation

The whole dataset uses just these marks, plus the ASCII space:

| | Characters |
|---|---|
| Chinese | `。` `，` `！` `？` `、` `：` `；` `（` `）` `《` `》` `…` `“` `”` `‘` `’` `%` |
| English | `.` `,` `!` `?` `;` `:` `'` `"` `-` `(` `)` `%` `$` |

The canonical set holds 17 Chinese marks and 13 English ones, down from 65 and 40
in the raw source. Everything else was mapped onto one of these or deleted. In the
data as shipped the Chinese side uses 16 of the 17 (`…` never survives the
ellipsis filter) and the English side uses all 13. Two details worth knowing:

- A `.` between digits survives, because it is a decimal point inside a numeral,
  not sentence punctuation.
- A `,` between digits is dropped, because Chinese does not write thousand
  separators.

## Statistics

| | |
|---|---|
| Pairs | 493,085 |
| Chinese length | 6-16 characters, median 8 |
| English length | 2-12 words, median 5 |
| Traditional characters left | 0 |
| Duplicate Chinese sentences | 0 |
| Lines with a proper noun | 0 |
| Chinese lines containing latin letters | 0 |
| Chinese punctuation variants | 16 of the 17 canonical marks |
| English punctuation variants | 13 of the 13 canonical marks |
| File size | 27.2 MB |

## Known limitations

- Subtitle data is noisy. Filtering removed the names, the truncated lines and
  the badly encoded ones, but a loose or wrong alignment still survives in
  roughly one pair in six or eight. This is inherent to OpenSubtitles-derived
  corpora and cannot be removed by text filters alone.
- Selecting the shortest sentences removes long, complex constructions, which is
  what makes this set easy to train on, but it also biases the data towards short
  conversational turns.
- The text is film and TV dialogue, so it contains informal language, slang and
  profanity.
