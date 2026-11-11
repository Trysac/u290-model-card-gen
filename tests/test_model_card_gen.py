"""Tests for model_card_gen."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from model_card_gen import (
    CardError,
    Gap,
    Issue,
    ModelCard,
    disparities,
    load_card,
    render_markdown,
    validate,
)


def make_card(**overrides) -> ModelCard:
    data = {
        "name": "sentiment-small",
        "license": "mit",
        "tags": ["text-classification"],
        "model_details": "A small sentiment model.",
        "intended_use": "Classify text sentiment.",
        "factors": "Language, domain.",
        "metrics": {"accuracy": {"all": Decimal("0.9"), "lang=en": Decimal("0.95")}},
        "evaluation_data": "Test set.",
        "training_data": "Train set.",
        "ethical_considerations": "Bias considerations.",
        "caveats": "Not for critical decisions.",
    }
    data.update(overrides)
    return load_card(json.dumps(data, default=float))


class TestLoadCard:
    def test_load_valid_dict_metrics(self):
        card = make_card()
        assert card.name == "sentiment-small"
        assert card.metrics == {"accuracy": {"all": Decimal("0.9"), "lang=en": Decimal("0.95")}}
        assert isinstance(card.metrics["accuracy"]["all"], Decimal)

    def test_load_list_metrics(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": [
                {
                    "name": "error_rate",
                    "higher_is_better": False,
                    "values": {"all": 0.05, "a": 0.04, "b": 0.12},
                }
            ],
            "evaluation_data": "e",
            "training_data": "t",
        }
        card = load_card(json.dumps(data))
        assert isinstance(card.metrics, tuple)
        entry = card.metrics[0]
        assert entry.name == "error_rate"
        assert entry.higher_is_better is False
        assert entry.values == {
            "all": Decimal("0.05"),
            "a": Decimal("0.04"),
            "b": Decimal("0.12"),
        }

    def test_direct_construction_normalises_lists(self):
        card = ModelCard(
            name="m",
            tags=["a"],
            extra_keys=["foo"],
            metrics=[{"name": "accuracy", "values": {"all": 1}}],
        )
        assert card.tags == ("a",)
        assert card.extra_keys == ("foo",)
        assert card.metrics[0].name == "accuracy"
        assert card.metrics[0].higher_is_better is True
        assert card.metrics[0].values == {"all": Decimal("1")}

    @pytest.mark.parametrize(
        "data",
        [
            [],
            {"name": ""},
            {"name": "m", "model_details": 1},
            {"name": "m", "model_details": "x" * 20_001},
            {"name": "m", "tags": "x"},
            {"name": "m", "tags": [1]},
            {"name": "m", "tags": ["x" * 20_001]},
            {"name": "m", "metrics": 5},
            {"name": "m", "metrics": {"accuracy": 0.5}},
            {"name": "m", "metrics": [1]},
            {"name": "m", "metrics": [{"name": 1, "values": {}}]},
            {"name": "m", "metrics": [{"name": "a", "values": {"all": "high"}}]},
            {"name": "m", "metrics": [{"name": "a", "values": {"all": 1.5}}]},
        ],
    )
    def test_invalid_cards_raise_invalid_card(self, data):
        with pytest.raises(CardError) as exc:
            load_card(json.dumps(data))
        assert exc.value.code == "invalid_card"

    def test_load_too_large(self):
        text = '{"name": "a"}' * 100000
        with pytest.raises(CardError) as exc:
            load_card(text, max_bytes=100)
        assert exc.value.code == "input_too_large"

    def test_load_invalid_json(self):
        with pytest.raises(CardError) as exc:
            load_card("not json")
        assert exc.value.code == "invalid_json"

    def test_load_invalid_metric_value_string(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": "high"}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        with pytest.raises(CardError) as exc:
            load_card(json.dumps(data))
        assert exc.value.code == "invalid_card"

    def test_load_invalid_metric_value_out_of_range(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 1.5}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        with pytest.raises(CardError) as exc:
            load_card(json.dumps(data))
        assert exc.value.code == "invalid_card"

    def test_load_rejects_boolean_metric_value(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": True}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        with pytest.raises(CardError) as exc:
            load_card(json.dumps(data))
        assert exc.value.code == "invalid_card"

    def test_load_unknown_keys_collected(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
            "foo": "bar",
        }
        card = load_card(json.dumps(data))
        assert card.extra_keys == ("foo",)

    def test_load_missing_required_sections_allowed(self):
        data = {"name": "m"}
        card = load_card(json.dumps(data))
        assert card.model_details == ""
        assert card.metrics == {}
        # validation will flag them


class TestValidate:
    def test_required_missing_intended_use(self):
        card = make_card(intended_use="")
        issues = validate(card)
        assert Issue("missing_section", "intended_use", "error") in issues

    def test_recommended_warning_for_ethics(self):
        card = make_card(ethical_considerations="")
        issues = validate(card)
        assert Issue("missing_section", "ethical_considerations", "warning") in issues

    def test_required_missing_metrics(self):
        card = make_card(metrics={})
        issues = validate(card)
        assert Issue("missing_section", "metrics", "error") in issues

    def test_unknown_license_warning(self):
        card = make_card(license="my-license")
        issues = validate(card)
        assert Issue("unknown_license", "license", "warning") in issues

    def test_unknown_field_warning(self):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
            "foo": "bar",
        }
        card = load_card(json.dumps(data))
        issues = validate(card)
        assert Issue("unknown_field", "foo", "warning") in issues


class TestDisparities:
    def test_basic_higher_is_better(self):
        card = make_card(
            metrics={
                "accuracy": {
                    "all": Decimal("0.91"),
                    "lang=en": Decimal("0.93"),
                    "lang=es": Decimal("0.84"),
                }
            }
        )
        gaps = disparities(card, threshold=Decimal("0.05"))
        assert gaps == [
            Gap(
                metric="accuracy",
                group="lang=es",
                value=Decimal("0.84"),
                reference_group="lang=en",
                reference=Decimal("0.93"),
                gap=Decimal("0.09"),
            )
        ]

    def test_lower_is_better_list_form(self):
        card = make_card(
            metrics=[
                {
                    "name": "error_rate",
                    "higher_is_better": False,
                    "values": {
                        "all": Decimal("0.05"),
                        "a": Decimal("0.04"),
                        "b": Decimal("0.12"),
                    },
                }
            ]
        )
        gaps = disparities(card, threshold=Decimal("0.05"))
        assert gaps == [
            Gap(
                metric="error_rate",
                group="b",
                value=Decimal("0.12"),
                reference_group="a",
                reference=Decimal("0.04"),
                gap=Decimal("0.08"),
            )
        ]

    def test_no_groups_only_all(self):
        card = make_card(metrics={"accuracy": {"all": Decimal("0.9")}})
        assert disparities(card) == []

    def test_gap_exactly_threshold(self):
        card = make_card(
            metrics={
                "accuracy": {
                    "a": Decimal("0.55"),
                    "b": Decimal("0.50"),
                }
            }
        )
        gaps = disparities(card, threshold=Decimal("0.05"))
        assert len(gaps) == 1
        assert gaps[0].gap == Decimal("0.05")

    def test_tie_breaks_by_group_name(self):
        card = make_card(
            metrics={
                "accuracy": {
                    "a": Decimal("0.90"),
                    "b": Decimal("0.90"),
                    "c": Decimal("0.80"),
                }
            }
        )
        gaps = disparities(card, threshold=Decimal("0.05"))
        assert gaps[0].reference_group == "a"


class TestRenderMarkdown:
    def test_front_matter_exact(self):
        card = make_card()
        rendered = render_markdown(card)
        assert rendered.startswith(
            "---\nlicense: mit\ntags:\n- text-classification\n---\n\n# sentiment-small\n\n## Model Details\n\n"
        )

    def test_table_exact_for_acceptance(self):
        card = make_card(
            metrics={
                "accuracy": {
                    "all": Decimal("0.91"),
                    "lang=en": Decimal("0.93"),
                    "lang=es": Decimal("0.84"),
                }
            }
        )
        rendered = render_markdown(card)
        expected_table = (
            "| Metric | Group | Value |\n"
            "| --- | --- | --- |\n"
            "| accuracy | all | 0.910 |\n"
            "| accuracy | lang=en | 0.930 |\n"
            "| accuracy | lang=es | 0.840 |\n"
        )
        assert expected_table in rendered

    def test_disparity_line_rendered(self):
        card = make_card(
            metrics={
                "accuracy": {
                    "all": Decimal("0.91"),
                    "lang=en": Decimal("0.93"),
                    "lang=es": Decimal("0.84"),
                }
            }
        )
        rendered = render_markdown(card)
        assert "> Disparity: accuracy for lang=es is 0.09 below lang=en." in rendered

    def test_escaping_angle_brackets(self):
        card = make_card(model_details="<script>x</script>")
        rendered = render_markdown(card)
        assert "&lt;script>x&lt;/script>" in rendered

    def test_escaping_pipe_in_table(self):
        card = make_card(metrics={"accuracy": {"a|b": Decimal("0.5"), "c": Decimal("0.6")}})
        rendered = render_markdown(card)
        assert "| accuracy | a\\|b |" in rendered

    def test_output_ends_with_one_newline(self):
        card = make_card()
        rendered = render_markdown(card)
        assert rendered.endswith("\n")
        assert not rendered.endswith("\n\n")

    def test_empty_tags_omit_front_matter_tags(self):
        card = make_card(tags=[])
        rendered = render_markdown(card)
        assert "tags:" not in rendered.split("---")[1]

    def test_no_license_omits_license_line(self):
        card = make_card(license="")
        rendered = render_markdown(card)
        assert "license:" not in rendered.split("---")[1]

    def test_disparity_line_above_for_lower_is_better(self):
        card = make_card(
            metrics=[
                {
                    "name": "error_rate",
                    "higher_is_better": False,
                    "values": {
                        "all": Decimal("0.05"),
                        "a": Decimal("0.04"),
                        "b": Decimal("0.12"),
                    },
                }
            ]
        )
        rendered = render_markdown(card)
        assert "> Disparity: error_rate for b is 0.08 above a." in rendered


class TestCLI:
    def _run_main(self, args, capsys, tmp_path):
        from model_card_gen.__main__ import main

        return main(args)

    def test_check_missing_section(self, capsys, tmp_path):
        data = {
            "name": "m",
            "model_details": "d",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        card_file = tmp_path / "card.json"
        card_file.write_text(json.dumps(data), encoding="utf-8")
        code = self._run_main([str(card_file), "--check"], capsys, tmp_path)
        captured = capsys.readouterr()
        assert code == 1
        assert "error missing_section intended_use" in captured.out

    def test_out_writes_file(self, tmp_path):
        card_data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        src = tmp_path / "card.json"
        src.write_text(json.dumps(card_data), encoding="utf-8")
        out = tmp_path / "out.md"
        from model_card_gen.__main__ import main

        code = main([str(src), "--out", str(out)])
        assert code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert content.startswith("---\n")

    def test_out_readme_md(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        card_data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        card_file = tmp_path / "card.json"
        card_file.write_text(json.dumps(card_data), encoding="utf-8")
        from model_card_gen.__main__ import main

        code = main(["card.json", "--out", "README.md"])
        assert code == 0
        written = tmp_path / "README.md"
        assert written.exists()
        assert written.read_text(encoding="utf-8").startswith("---\n")

    def test_threshold_option_filters_disparities(self, tmp_path):
        card_data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {
                "accuracy": {"all": 0.91, "lang=en": 0.93, "lang=es": 0.84},
            },
            "evaluation_data": "e",
            "training_data": "t",
        }
        src = tmp_path / "card.json"
        src.write_text(json.dumps(card_data), encoding="utf-8")
        from model_card_gen.__main__ import main

        default_out = tmp_path / "default.md"
        assert main([str(src), "--out", str(default_out)]) == 0
        assert "> Disparity: accuracy for lang=es is 0.09 below lang=en." in default_out.read_text(
            encoding="utf-8"
        )

        filtered_out = tmp_path / "filtered.md"
        assert main([str(src), "--out", str(filtered_out), "--threshold", "0.2"]) == 0
        assert "> Disparity:" not in filtered_out.read_text(encoding="utf-8")

    def test_check_ok_returns_0(self, tmp_path, capsys):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
            "factors": "f",
            "ethical_considerations": "e",
            "caveats": "c",
        }
        card_file = tmp_path / "card.json"
        card_file.write_text(json.dumps(data), encoding="utf-8")
        from model_card_gen.__main__ import main

        code = main([str(card_file), "--check"])
        assert code == 0

    def test_out_io_error_returns_2(self, tmp_path, capsys):
        data = {
            "name": "m",
            "model_details": "d",
            "intended_use": "u",
            "metrics": {"accuracy": {"all": 0.5}},
            "evaluation_data": "e",
            "training_data": "t",
        }
        src = tmp_path / "card.json"
        src.write_text(json.dumps(data), encoding="utf-8")
        from model_card_gen.__main__ import main

        code = main([str(src), "--out", str(tmp_path)])
        assert code == 2
        captured = capsys.readouterr()
        assert "cannot write" in captured.err

    def test_missing_file_returns_2(self, tmp_path, capsys):
        from model_card_gen.__main__ import main

        code = main(["nonexistent.json", "--check"])
        assert code == 2
        captured = capsys.readouterr()
        assert "cannot read" in captured.err

    def test_usage_error_when_no_mode(self, capsys):
        from model_card_gen.__main__ import main

        code = main(["card.json"])
        assert code == 2

    def test_load_card_error_returns_1(self, tmp_path, capsys):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json", encoding="utf-8")
        from model_card_gen.__main__ import main

        code = main([str(bad_file), "--check"])
        assert code == 1
