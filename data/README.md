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
2. Keeps only pairs that look like complete, simple sentences:
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
3. Deduplicates on the Chinese sentence, so each source sentence has one English
   translation rather than a dozen competing variants.
4. Ranks the survivors by simplicity and keeps the 500,000 shortest.

Reproduce with:

```bash
python src/prepare_data.py --src-dir <raw en-zh dir> --out data/zh-en.txt \
    --order simplest --max-pairs 500000
```

## Statistics

| | |
|---|---|
| Pairs | 500,000 |
| Chinese length | 6-16 characters, median 8 |
| English length | 3-10 words, median 5 |
| Traditional characters left | 0 |
| Duplicate Chinese sentences | 0 |
| Lines with a proper noun | 0 |
| Chinese lines containing latin letters | 0 |
| File size | 27.3 MB |

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
