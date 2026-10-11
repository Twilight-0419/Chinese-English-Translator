# Dataset: `zh-en.txt`

Chinese to English sentence pairs, one pair per line, the two sides separated by a
single tab character:

```
中文句子	English sentence
```

Encoding is UTF-8 without BOM, line endings are LF.

## Sources

Built from seven [OPUS](https://opus.nlpl.eu/) corpora (`moses` release, `en-zh`
direction). Download sizes and how many pairs each one contributed:

| corpus | version | downloaded | pairs in source | pairs kept |
|---|---|---:|---:|---:|
| ParaCrawl | v9 | 1246 MB | 14,170,869 | 945,656 |
| OpenSubtitles | v2016 | 285 MB | 9,304,777 | 823,126 |
| WikiMatrix | v1 | 99 MB | 786,512 | 55,094 |
| TED2013 | v1.1 | 11 MB | 154,579 | 22,556 |
| QED | v2.0a | 1 MB | 13,123 | 1,193 |
| wikimedia | v20260327 | 86 MB | 471,224 | 544 |
| News-Commentary | v16 | 28 MB | 125,996 | 108 |
| XLEnt | v1.1 | 165 MB | 6,292,330 | 0 |
| **total** | | | | **1,848,277** |

XLEnt contributes nothing: it is a Wiktionary-derived lexicon rather than a
sentence corpus, so none of it satisfies the sentence filters below. The news and
Wikipedia corpora contribute very little because their sentences are far longer
than the length window allows.

OPUS does not attach a single standard open licence to these corpora. Check the
OPUS and upstream terms before redistributing this data or using it commercially.

## How it was built

The two line-aligned source files were turned into this file by the steps below.
The code that performed them is not part of this repository; this section is the
specification of what was done, so the result is reproducible.

1. Converts traditional Chinese to simplified Chinese with OpenCC (`t2s`). The
   source is mixed script, so this is required for a consistent vocabulary.
2. Canonicalises punctuation on both sides. The source mixes full width and half
   width marks (`？` vs `?`, `！` vs `!`) and carries encoding artefacts (`´`,
   `` ` ``, `︰`, `¶`, `§`, `♪`). Every punctuation character is mapped onto the
   small canonical set documented below, and one that has no canonical form is
   deleted.
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
5. Drops rows whose Chinese contains runs of repeated punctuation (`。。`, `，，`).
   The original rule already rejected `...`, but web-crawled text writes ellipses
   with full width stops, and 23,915 rows slipped through.
6. Ranks the survivors by simplicity and keeps the shortest ones first.

The final file is capped at 103,000,000 bytes because GitHub rejects any single
file above 100 MiB (104,857,600 bytes). Because pairs are ordered by simplicity,
the cap removes the longest sentences at the tail. Together the punctuation rule
and the cap turn the 1,848,277 filtered pairs into the 1,381,995 shipped here.

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
| Pairs | 1,381,995 |
| Chinese length | 6-19 characters, median 10 |
| English length | 3-12 words, median 7 |
| Traditional characters left | 0 |
| Duplicate Chinese sentences | 0 |
| Lines with a proper noun | 0 |
| Chinese lines containing latin letters | 0 |
| Chinese punctuation variants | 18, of which one is the decimal point |
| English punctuation variants | 13 of the 13 canonical marks |
| File size | 98.2 MiB (103,000,073 bytes) |

## Known limitations

- Subtitle data is noisy. Filtering removed the names, the truncated lines and
  the badly encoded ones, but a loose or wrong alignment still survives in
  roughly one pair in six or eight. This is inherent to OpenSubtitles-derived
  corpora and cannot be removed by text filters alone.
- The corpus is now a mix of domains: film and TV dialogue (OpenSubtitles),
  web-crawled text (ParaCrawl), encyclopedic prose (WikiMatrix) and talks
  (TED2013). That widens the vocabulary but also the style, so expect the model
  to be mediocre everywhere rather than good on one domain.
- ParaCrawl is web text and its alignment quality is uneven. A few rows still
  carry paragraph numbers or navigation fragments from the source pages.
- Selecting the shortest sentences removes long, complex constructions, which is
  what makes this set easy to train on, but it also biases the data towards short
  conversational turns.
- The text is film and TV dialogue, so it contains informal language, slang and
  profanity.

## Vocabulary compatibility

`models/word2index_and_word_count.pt` was built from the earlier 493,085 pair
version of this file. The vocabulary in the published model release matches it,
so it is kept as is.

Before training on this larger file, delete that `.pt` file and let the notebook
rebuild it, otherwise every word that is new to the larger corpus is mapped to
`<unk>`.
