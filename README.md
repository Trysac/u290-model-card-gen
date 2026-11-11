# trysac-model-card-gen

`model_card_gen` is a standard-library-only Python package that turns a structured JSON model card into deterministic Markdown. It validates the sections used by Mitchell et al., Model Cards for Model Reporting (2019), keeps metric values as `Decimal`, reports subgroup metric disparities explicitly, and writes YAML front matter plus the section order: Model Details, Intended Use, Factors, Metrics, Evaluation Data, Training Data, Quantitative Analyses, Ethical Considerations, Caveats and Recommendations.

## Installation

```bash
pip install trysac-model-card-gen
```

The import name is `model_card_gen`. The package has no runtime dependencies.

## Usage

```python
import json
from model_card_gen import load_card, validate, render_markdown

text = json.dumps(
    {
        "name": "m",
        "model_details": "d",
        "intended_use": "u",
        "metrics": {"acc": {"all": 0.9}},
        "evaluation_data": "e",
        "training_data": "t",
    }
)
card = load_card(text)
issues = validate(card)
print(render_markdown(card))
```

The CLI reads a card file and can write Markdown or print validation issues:

```bash
python -m model_card_gen card.json --out README.md
python -m model_card_gen card.json --check
python -m model_card_gen card.json --out README.md --threshold 0.1
```

## Public API

- `load_card(text: str, *, max_bytes: int = 1_048_576) -> ModelCard` parses JSON with `parse_float=Decimal`. It raises `CardError` with `.code` set to `input_too_large`, `invalid_json`, or `invalid_card`.
- `ModelCard` is a frozen dataclass. Required content checked by `validate` is `model_details`, `intended_use`, `metrics`, `evaluation_data`, and `training_data`; optional fields default to empty values. `metrics` accepts either `{metric: {group: number}}` or a list of `{'name': ..., 'higher_is_better': ..., 'values': {group: number}}`.
- `validate(card: ModelCard) -> list[Issue]` returns `Issue(code, field, severity)`. Missing or blank required sections are `error`; missing or blank `factors`, `ethical_considerations`, and `caveats` are `warning`; unknown top-level keys are `unknown_field` warnings; a non-empty license outside the allowlist is an `unknown_license` warning. The allowlist is `apache-2.0`, `mit`, `bsd-3-clause`, `cc-by-4.0`, `cc-by-sa-4.0`, `cc-by-nc-4.0`, `openrail`, `llama3`, `gemma`, `other`.
- `disparities(card: ModelCard, threshold: Decimal = Decimal('0.05')) -> list[Gap]` compares each non-`all` group with the best group (highest value, or lowest when `higher_is_better` is `False`; ties by group name). A `Gap` is reported when `gap >= threshold`; `gap` is the exact `Decimal` absolute difference.
- `render_markdown(card: ModelCard, *, threshold: Decimal = Decimal('0.05')) -> str` emits YAML front matter with `license` and `tags` only when present, `# <name>`, present sections as `## <Title>`, a metric-name list, a `| Metric | Group | Value |` table with values quantized to three decimals, and one `> Disparity: <metric> for <group> is <gap> below <reference_group>.` line per gap (`above` for lower-is-better metrics). Output ends with exactly one newline.
- CLI `main(argv: list[str] | None = None) -> int` in `src/model_card_gen/__main__.py` accepts the card path, `--out`, `--check`, and `--threshold`. Exit codes: `0` success, `1` validation errors or `CardError`, `2` usage or I/O errors. `--check` prints `<severity> <code> <field>` per issue.

Limits: `max_bytes` defaults to `1_048_576` UTF-8 bytes; `name` must be non-blank and at most 100 characters; text fields and tag items are at most 20,000 characters; metric values must be non-boolean numbers in `[0, 1]`. Rendering escapes `<` as `&lt;` in text and `|` as `\|` in table cells.

## Why not a Markdown template

A Markdown template cannot reject a card that omits required sections, and it cannot state subgroup gaps from structured metrics. This library validates the required sections, keeps metric values exact as `Decimal`, and renders explicit disparity lines when a gap is at or above the threshold.

## Features

- Standard-library-only parsing, validation, disparity analysis, and Markdown rendering.
- Frozen `ModelCard`, `Issue`, and `Gap` dataclasses; `MetricEntry` for list-form metrics.
- Deterministic Markdown with YAML front matter, the Mitchell et al. section order, and one trailing newline.
- Validation errors and warnings for required, recommended, unknown, and license fields.
- Subgroup disparity notes using a configurable `Decimal` threshold.
- Markdown table escaping for `<` and `|`.

## Documentation

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and input limits. See [docs/PROJECT.md](docs/PROJECT.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/TESTING.md](docs/TESTING.md) for scope, implementation shape, and tests.
