# Security notes

## Threat model

`model_card_gen` is a pure library. `load_card`, `validate`, `disparities`, and `render_markdown` do not open files, make network calls, execute external commands, or print. The CLI in `src/model_card_gen/__main__.py` reads the card path and optionally writes the `--out` path.

Defended:

- Oversized input: `load_card` encodes the input as UTF-8 and rejects more than `max_bytes` (default `1_048_576`) with `CardError('input_too_large')`.
- Malformed JSON: `json.loads` failure raises `CardError('invalid_json')`.
- Invalid card structure: the top level must be an object; `name` must be non-blank and at most 100 characters; text fields and tag items at most 20,000 characters; `tags` must be a list of strings; metrics must be a dict or a list of metric entries; metric values must be non-boolean numbers in `[0, 1]`. Invalid input raises `CardError('invalid_card')`.
- Unknown fields and licenses: `validate` returns `unknown_field` warnings for top-level keys outside the card schema and `unknown_license` for a non-empty license outside the allowlist.
- Markdown escaping: `render_markdown` replaces `<` with `&lt;` in all text and replaces `|` with `\|` in table cells. It does not implement a general Markdown or HTML sanitizer.

Not defended:

- Card claims and metric values are not verified; the library does not compute metrics from predictions or check data provenance.
- Subgroup completeness is not checked; `disparities` only compares the groups present in the supplied metrics.
- There is no authentication, authorization, encryption, sandbox, rate limiting, or separate nesting-depth/CPU limit beyond the UTF-8 byte limit in `load_card`.
- The CLI writes directly to the `--out` path with `Path.write_text` and does not restrict filesystem paths.
- No secrets scanning, dependency scanning, or release signing is implemented in the provided source.

## Publishing

No release or publishing configuration is present in the provided source.
