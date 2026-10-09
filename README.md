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

## Status

Project scaffolding. Data pipeline, model, training, and inference code coming next.
