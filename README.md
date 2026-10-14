# Chinese-English Translator

A Chinese-to-English neural machine translation project. A GRU encoder-decoder
with additive attention, trained from scratch on 1.38M sentence pairs.

```
我爱你。              i love you .
你叫什么名字？         what 's your name ?
我是一名警察。         i 'm a cop .
他在哪里？            where 's he ?
我不知道该怎么办。      i don 't know what to do .
```

## Project Layout

```
data/       the parallel corpus and its documentation
models/     vocabulary and checkpoints, not in git - see Model below
notebook/   the model, the training loop and the loss curve
src/        the command line translator
```

## Data

`data/zh-en.txt` holds 1,381,995 simplified Chinese to English sentence pairs, one
pair per line, separated by a tab. It was built from seven OPUS corpora covering
web text, film subtitles, Wikipedia, talks and news.

See [data/README.md](data/README.md) for the sources, the filtering rules, the
per-corpus yield, the vocabulary cut-offs and the known limitations.

## Model

Checkpoints live in GitHub releases rather than in git: they are around 100 MB of
binary that git cannot delta-compress and would keep in the history forever.

| release | notes |
|---|---|
| **[v0.2](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.2)** | current, 1.38M pairs, 25.4M parameters |
| [v0.1](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.1) | first run, 493k pairs, 44.4M parameters |

Each release carries three assets that only work together:

| asset | v0.2 |
|---|---:|
| `encoder.pt` | 37.9 MB |
| `decoder.pt` | 63.7 MB |
| `word2index_and_word_count.pt` | 1.3 MB |

The vocabulary ships with the checkpoint because the two are a pair: index 7 is
"is" in one vocabulary and something else in another.

```bash
mkdir -p models && cd models
base=https://github.com/Twilight-0419/Chinese-English-Translator/releases/download/v0.2
for f in encoder.pt decoder.pt word2index_and_word_count.pt; do curl -L -O "$base/$f"; done
```

## Usage

From the project root:

```bash
python -m src.main
```

```
请输入中文句子: 我爱你。
翻译结果: i love you .
是否继续翻译？(y/n):
```

`python -m src.main` rather than `python src/main.py`. Running the script directly
puts `src/` on the import path instead of the project root, and then `from
src.translator import translate` cannot find the package.

`src/translator.py` holds the model classes, loads the weights once and exposes
`translate(sentence)`.

## Training

`notebook/C2E_Translator.ipynb` contains the whole pipeline: corpus loading,
vocabulary construction, the model, the training loop and a loss curve. Run the
cells from the top.

Training settings for v0.2: batch size 256, Adam at 1e-4, gradient clipping at
max_norm 20, teacher forcing starting at 0.5 and decaying by 0.95 per epoch, 30
epochs.

## How It Works

**Encoder** — a GRU reads the Chinese sentence. Padding never reaches the decoder:
the final hidden state is taken at each sentence's real last token and the
attention scores are masked, so padded positions get exactly zero weight.

**Decoder** — at each step it combines the previous hidden state with the embedded
previous word, attends over the encoder outputs, and emits a distribution over the
English vocabulary.

**Decoding is greedy** — the highest scoring word is taken at every step, so the
same input always gives the same output.

**A repetition penalty of 2.0** divides the score of any word already emitted.
Without it the model happily produces `i love love . .`; with it, repetition
dropped from 72% of test sentences to zero.

## Known Limitations

- **Short sentences only.** The corpus was filtered to 6-19 Chinese characters, so
  long or complex sentences are out of distribution and translate poorly.
- **The corpus is noisy.** It mixes film subtitles and web crawls; roughly one
  pair in six to eight is a loose or wrong alignment. Text filters cannot remove
  that.
- **It is small.** 25M parameters with no beam search, no subword units and a
  34k/30k word vocabulary. Treat it as a working end-to-end pipeline rather than a
  usable translator.
- **Output spacing is literal.** Words are joined with spaces after tokenisation,
  so contractions and punctuation come out as `i 'm a cop .` rather than `I'm a
  cop.`
