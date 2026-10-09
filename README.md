# Chinese-English Translator

A Chinese-to-English neural machine translation project built on a GRU
encoder-decoder sequence-to-sequence model with an attention mechanism.

The encoder reads a Chinese sentence into a sequence of hidden states, attention
lets the decoder focus on the relevant source positions while generating each
English word, and the decoder produces the translation one token at a time.

## Project Layout

```
data/       datasets and preprocessing output
models/     trained model checkpoints
notebook/   experiments and exploration
src/        source code (data pipeline, model, training, inference)
```

## Data

`data/zh-en.txt` holds 500,000 simple Chinese to English sentence pairs, one pair
per line, separated by a tab. It is built from the OPUS `OpenSubtitles` corpus,
filtered down to short complete sentences and fully converted to simplified
Chinese. See [data/README.md](data/README.md) for the source, the filtering rules
and the known limitations.

## Status

Data preparation is done (`src/prepare_data.py`). Model, training and inference
code coming next.
