# model-card-gen

[![PyPI version](https://img.shields.io/pypi/v/trysac-model-card-gen)](https://pypi.org/project/trysac-model-card-gen/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-model-card-gen)](LICENSE)
[![CI](https://github.com/Trysac/u290-model-card-gen/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u290-model-card-gen/actions/workflows/ci.yml)

Generate model cards in Markdown from structured JSON following the Mitchell et al. sections, with validation, Decimal metric tables and subgroup disparity notes

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-model-card-gen
# or
uv add trysac-model-card-gen
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import model_card_gen

# normalize() trims surrounding whitespace and lower-cases the text.
print(model_card_gen.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    model_card_gen.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
