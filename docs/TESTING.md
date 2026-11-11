# Testing

## Running

```sh
pytest tests/test_model_card_gen.py
```

## Policy

The test module `tests/test_model_card_gen.py` imports the public API (`CardError`, `Gap`, `Issue`, `ModelCard`, `disparities`, `load_card`, `render_markdown`, `validate`) and pytest. Its `make_card` helper builds JSON cards. Tests assert returned cards, metric values, and `CardError.code` values. No network or external services are used by the tests.

## Tiers

No separate conformance tier, CI configuration, or coverage threshold is present in the provided files. The tests are a single pytest module.

## Layout

- `tests/test_model_card_gen.py` contains `make_card` and `TestLoadCard`.
- `TestLoadCard.test_load_valid_dict_metrics` covers valid dict-form metrics.
- `TestLoadCard.test_load_list_metrics` covers list-form metrics.
- `TestLoadCard.test_direct_construction_normalises_lists` covers list normalisation in `ModelCard`.
- `TestLoadCard.test_invalid_cards_raise_invalid_card` covers invalid card structures and `CardError.code == 'invalid_card'`.
- `TestLoadCard.test_load_too_large` covers `CardError.code == 'input_too_large'` with `max_bytes`.
- `TestLoadCard.test_load_invalid_json` covers `CardError.code == 'invalid_json'`.
- `TestLoadCard.test_load_invalid_metric_value_string` and `test_load_invalid_metric_value_out_of_range` cover invalid metric values.
