# Use structured JSON input and explicit disparity rendering for model cards

Status: accepted (generated, pending human review)

## Context

Model cards are often written as free text, leading to missing sections and hidden subgroup gaps. The specification requires validation against Mitchell et al. sections, Decimal-precise metrics, and automatic disparity statements.

## Decision

Implement a Python package that loads a JSON card into a frozen dataclass, validates required/recommended sections, computes subgroup disparities relative to the best non-'all' group, and renders deterministic Markdown with a CLI. All parsing uses `decimal.Decimal` via `json.loads(parse_float=Decimal)` for exact arithmetic.

## Consequences

The library enforces structured cards and transparent reporting. It does not handle metric computation from predictions, the full Hugging Face model-index schema, or HTML/EU AI Act output, which are out of scope.
