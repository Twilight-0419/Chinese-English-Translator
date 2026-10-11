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
src/        source code (model, training, inference)
```

## Data

`data/zh-en.txt` holds 1,381,995 simple Chinese to English sentence pairs, one
pair per line, separated by a tab. It is built from seven OPUS corpora, filtered
down to short complete sentences and fully converted to simplified Chinese. See
[data/README.md](data/README.md) for the sources, the filtering rules, the
per-corpus yield and the known limitations.

## Model

The trained checkpoints are published as a GitHub release instead of being
committed, because they add roughly 73 MB of binary that git cannot
delta-compress and would keep in the history forever.

**[Release v0.1 - trained GRU seq2seq model](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.1)**

| asset | size | contents |
|---|---:|---|
| `encoder.pt` | 27 MB | `state_dict()` for the encoder |
| `decoder.pt` | 46 MB | `state_dict()` for the attention decoder |
| `word2index_and_word_count.pt` | 0.9 MB | the matching vocabulary |

Download all three into `models/`. The vocabulary ships with the release because
it has to match the checkpoint: index 7 means "is" in this vocabulary and would
mean something else in a vocabulary rebuilt from a different corpus. Rebuilding
it from the current 1.38M pair dataset produces a different, larger vocabulary,
which is the right thing for a new training run but will not load into this
checkpoint.

The model is a GRU encoder-decoder with additive attention, hidden size 256, a
single layer and 19.1M parameters in total. It was trained on the earlier
493,085 pair version of `data/zh-en.txt` with batch size 256, Adam at 1e-4,
gradient clipping at max_norm 20 and a teacher forcing ratio of 0.5. It matches
the vocabulary shipped in this repository, so it keeps working, but it has not
seen the newer ParaCrawl, WikiMatrix or TED2013 rows.

`notebook/C2E_Translator.ipynb` defines the model classes. Load the weights after
running the cells that build them:

```python
encoder.load_state_dict(torch.load('../models/encoder.pt'))
decoder.load_state_dict(torch.load('../models/decoder.pt'))
encoder.eval()
decoder.eval()
```

## Status

Data preparation is done, a first training run has finished, and inference works
through `src/translator.py`. The dataset was expanded to roughly three times its
earlier size, which means the next training run needs the vocabulary rebuilt
first - see the note at the end of [data/README.md](data/README.md).
