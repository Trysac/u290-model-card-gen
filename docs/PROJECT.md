# Project record

## Objective

Generate model cards in Markdown from structured JSON following the Mitchell et al. sections, with validation, Decimal metric tables, and subgroup disparity notes.

## Scope

- In scope: `load_card`, `validate`, `disparities`, and `render_markdown` as documented in [README.md](../README.md); immutable `ModelCard`, `Issue`, and `Gap` dataclasses; the `python -m model_card_gen` CLI with `--out`, `--check`, and `--threshold`; standard-library-only implementation.
- Out of scope: computing metrics from predictions, the full Hugging Face model-index schema, HTML output, and EU AI Act documentation.

## Timeline

No dated project timeline is recorded in the provided source files.

## Effort metrics

Measured values only; a value that has not been measured stays pending measurement.

| Metric | Value |
|---|---|
| Tokens (input / output) | 1089507 / 92490 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1233 |

## Factory run u290 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1875 | 27450 | 0 | 3200 | 0.0557 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 24683 | 10372 | 0 | 325888 | 0.0109 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 9961 | 3099 | 0 | 45184 | 0.0035 |
| 2026-11-10 | audit | deepseek-flash | no | 30328 | 33021 | 0 | 380928 | 0.0255 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 15716 | 3890 | 0 | 159488 | 0.0052 |
| 2026-11-10 | docs | deepseek-flash | no | 92000 | 14658 | 0 | 256 | 0.0226 |

Total: $0.1233. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
