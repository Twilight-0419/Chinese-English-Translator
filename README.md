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

`data/zh-en.txt` holds 493,085 simple Chinese to English sentence pairs, one pair
per line, separated by a tab. It is built from the OPUS `OpenSubtitles` corpus,
filtered down to short complete sentences and fully converted to simplified
Chinese. See [data/README.md](data/README.md) for the source, the filtering rules
and the known limitations.

## Model

The trained checkpoints are published as a GitHub release instead of being
committed, because they add roughly 73 MB of binary that git cannot
delta-compress and would keep in the history forever.

**[Release v0.1 - trained GRU seq2seq model](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.1)**

| asset | size | contents |
|---|---:|---|
| `encoder.pt` | 27 MB | `state_dict()` for the encoder |
| `decoder.pt` | 46 MB | `state_dict()` for the attention decoder |

Download both into `models/`. The vocabulary is small and slow to rebuild, so
unlike the checkpoints it is versioned in this repository at
`models/word2index_and_word_count.pt` and arrives with a normal `git clone`.

The model is a GRU encoder-decoder with additive attention, hidden size 256, a
single layer and 19.1M parameters in total. It was trained on the full
`data/zh-en.txt` with batch size 256, Adam at 1e-4, gradient clipping at
max_norm 20 and a teacher forcing ratio of 0.5.

`notebook/C2E_Translator.ipynb` defines the model classes. Load the weights after
running the cells that build them:

```python
encoder.load_state_dict(torch.load('../models/encoder.pt'))
decoder.load_state_dict(torch.load('../models/decoder.pt'))
encoder.eval()
decoder.eval()
```

## Status

Data preparation is done and a first training run has finished. Inference code
coming next.
