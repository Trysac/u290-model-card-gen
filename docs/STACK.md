# Stack

## Used

| Tool | Why |
|---|---|
| Python | The package uses only the standard library: `json`, `decimal`, `dataclasses`, `logging`, `typing`, `argparse`, and `pathlib`. |
| Standard-library `json` with `parse_float=Decimal` | Keeps metric values as `Decimal` during parsing. |
| Standard-library `argparse` | Builds the `model-card-gen` CLI in `src/model_card_gen/__main__.py`. |
| pytest | The test module `tests/test_model_card_gen.py` is compiled with pytest 9.2.0 in the provided cache. |

## Discarded

| Tool | Why not |
|---|---|
| Third-party runtime dependencies | The package declares no runtime dependencies and imports only the Python standard library. |
