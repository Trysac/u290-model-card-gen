# Architecture

## Purpose

`model-card-gen` is a small, standard-library-only Python package. It parses a JSON model card into an immutable `ModelCard`, validates the Mitchell et al. sections, computes subgroup disparities from metric values held as `Decimal`, and renders deterministic Markdown. The CLI entry point is `python -m model_card_gen`.

## Shape

```text
caller code --> model_card_gen (public API in __init__.py)
                    |
                    +-- load_card
                    +-- validate
                    +-- disparities
                    +-- render_markdown

python -m model_card_gen --> __main__.py --> the same functions
```

- Public API: `CardError`, `Gap`, `Issue`, `ModelCard`, `__version__`, `disparities`, `load_card`, `render_markdown`, `validate`, as listed in `__all__` of `src/model_card_gen/__init__.py`.
- Types: `ModelCard` is frozen; `Issue` and `Gap` are frozen dataclasses; `MetricEntry` models list-form metrics.
- Errors: `load_card` raises `model_card_gen.CardError` whose `.code` is `input_too_large`, `invalid_json`, or `invalid_card`. `validate` returns issues instead of raising for missing sections, unknown fields, and unknown licenses.
- Side effects: library functions do not read files, write files, print, or make network calls. The CLI in `src/model_card_gen/__main__.py` reads the card path, writes `--out`, prints issues for `--check`, and returns exit codes.
- Limits: `max_bytes` defaults to `1_048_576`; name at most 100 characters; text and tag items at most 20,000 characters; metric values in `[0, 1]` and JSON booleans rejected.

## Quality contract

The repository contains `tests/test_model_card_gen.py`, which uses pytest and imports the public API. The source includes `src/model_card_gen/py.typed`. No `scripts/check.py`, CI workflow, or coverage configuration is present in the provided files.

## Decisions

The implementation keeps the library in one module, uses `decimal.Decimal` throughout metric parsing and disparity calculation, uses frozen dataclasses for value objects, and has no runtime dependencies. No separate ADR directory is present in the provided source.
