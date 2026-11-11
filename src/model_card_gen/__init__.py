"""Generate model cards in Markdown from structured JSON.

This module implements parsing, validation, disparity analysis and
Markdown rendering for model cards following the sections of
Mitchell et al., "Model Cards for Model Reporting" (2019).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

GroupValues = dict[str, Decimal]


@dataclass(frozen=True)
class MetricEntry:
    """One metric in the list form of a card's metrics section."""

    name: str
    higher_is_better: bool
    values: GroupValues


MetricForm = dict[str, GroupValues] | tuple[MetricEntry, ...]


@dataclass(frozen=True)
class ModelCard:
    """An immutable model card.

    Required fields are ``name`` (validated by :func:`load_card`) and the
    five content sections that :func:`validate` checks.  Optional fields
    have default empty values.
    """

    name: str
    model_details: str = ""
    intended_use: str = ""
    metrics: MetricForm = field(default_factory=dict)
    evaluation_data: str = ""
    training_data: str = ""
    version: str = ""
    license: str = ""
    tags: tuple[str, ...] = ()
    factors: str = ""
    ethical_considerations: str = ""
    caveats: str = ""
    extra_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Normalise list inputs to immutable tuples.
        if isinstance(self.tags, list):
            object.__setattr__(self, "tags", tuple(self.tags))
        if isinstance(self.extra_keys, list):
            object.__setattr__(self, "extra_keys", tuple(self.extra_keys))
        if isinstance(self.metrics, list):
            entries = []
            for item in self.metrics:
                if not isinstance(item, dict):
                    raise TypeError("metrics list items must be dicts")
                name = item.get("name")
                values = item.get("values")
                higher = item.get("higher_is_better", True)
                if (
                    not isinstance(name, str)
                    or not isinstance(values, dict)
                    or not isinstance(higher, bool)
                ):
                    raise TypeError("invalid metrics list item")
                new_values: GroupValues = {}
                for key, val in values.items():
                    if isinstance(val, bool) or not isinstance(val, (int, Decimal)):
                        raise TypeError("invalid metric value")
                    new_values[key] = Decimal(val) if isinstance(val, int) else val
                entries.append(MetricEntry(name, higher, new_values))
            object.__setattr__(self, "metrics", tuple(entries))


@dataclass(frozen=True)
class Issue:
    """A validation issue found in a card."""

    code: str
    field: str
    severity: Literal["error", "warning"]


@dataclass(frozen=True)
class Gap:
    """A subgroup disparity discovered by :func:`disparities`."""

    metric: str
    group: str
    value: Decimal
    reference_group: str
    reference: Decimal
    gap: Decimal


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CARD_KEYS = {
    "name",
    "version",
    "license",
    "tags",
    "model_details",
    "intended_use",
    "factors",
    "metrics",
    "evaluation_data",
    "training_data",
    "ethical_considerations",
    "caveats",
}

_LICENSES = {
    "apache-2.0",
    "mit",
    "bsd-3-clause",
    "cc-by-4.0",
    "cc-by-sa-4.0",
    "cc-by-nc-4.0",
    "openrail",
    "llama3",
    "gemma",
    "other",
}

_MAX_TEXT_LENGTH = 20_000
_MAX_NAME_LENGTH = 100
_DEFAULT_MAX_BYTES = 1_048_576


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CardError(Exception):
    """Raised when a card is invalid at load time."""

    def __init__(self, code: Literal["input_too_large", "invalid_json", "invalid_card"]):
        self.code = code
        super().__init__(code)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def load_card(text: str, *, max_bytes: int = _DEFAULT_MAX_BYTES) -> ModelCard:
    """Parse a JSON string into a :class:`ModelCard`.

    Numbers are converted to :class:`decimal.Decimal` via ``parse_float``.
    Invalid card structure or metric values raise :class:`CardError`.
    Missing optional fields receive empty defaults; required section
    presence is checked by :func:`validate`.

    Args:
        text: The JSON string.
        max_bytes: Maximum allowed UTF-8 encoded byte length.

    Raises:
        CardError: if the input is too large, is not valid JSON, or is not a
            valid card (wrong types, metric values out of range, etc.).
    """
    encoded = text.encode("utf-8")
    if len(encoded) > max_bytes:
        raise CardError("input_too_large")

    try:
        data = json.loads(text, parse_float=Decimal)
    except json.JSONDecodeError:
        raise CardError("invalid_json") from None

    if not isinstance(data, dict):
        raise CardError("invalid_card")

    # name is required and bounded
    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > _MAX_NAME_LENGTH:
        raise CardError("invalid_card")

    # string fields
    str_fields = {}
    for field_name in (
        "model_details",
        "intended_use",
        "evaluation_data",
        "training_data",
        "version",
        "license",
        "factors",
        "ethical_considerations",
        "caveats",
    ):
        val = data.get(field_name)
        if val is None:
            str_fields[field_name] = ""
        elif isinstance(val, str):
            if len(val) > _MAX_TEXT_LENGTH:
                raise CardError("invalid_card")
            str_fields[field_name] = val
        else:
            raise CardError("invalid_card")

    # tags
    tags_raw = data.get("tags")
    tags: tuple[str, ...]
    if tags_raw is None:
        tags = ()
    elif isinstance(tags_raw, list):
        normalized = []
        for item in tags_raw:
            if not isinstance(item, str):
                raise CardError("invalid_card")
            if len(item) > _MAX_TEXT_LENGTH:
                raise CardError("invalid_card")
            normalized.append(item)
        tags = tuple(normalized)
    else:
        raise CardError("invalid_card")

    # metrics
    metrics_raw = data.get("metrics")
    if metrics_raw is None:
        metrics: MetricForm = {}
    elif isinstance(metrics_raw, dict):
        metric_dict: dict[str, GroupValues] = {}
        for metric_name, groups in metrics_raw.items():
            if not isinstance(metric_name, str) or not isinstance(groups, dict):
                raise CardError("invalid_card")
            group_vals: GroupValues = {}
            for group, value in groups.items():
                if not isinstance(group, str):
                    raise CardError("invalid_card")
                if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
                    raise CardError("invalid_card")
                dec_val = Decimal(value) if isinstance(value, int) else value
                if not (Decimal("0") <= dec_val <= Decimal("1")):
                    raise CardError("invalid_card")
                group_vals[group] = dec_val
            metric_dict[metric_name] = group_vals
        metrics = metric_dict
    elif isinstance(metrics_raw, list):
        entries = []
        for item in metrics_raw:
            if not isinstance(item, dict):
                raise CardError("invalid_card")
            name_metric = item.get("name")
            values_raw = item.get("values")
            higher = item.get("higher_is_better", True)
            if (
                not isinstance(name_metric, str)
                or not isinstance(values_raw, dict)
                or not isinstance(higher, bool)
            ):
                raise CardError("invalid_card")
            group_vals = {}
            for group, value in values_raw.items():
                if not isinstance(group, str):
                    raise CardError("invalid_card")
                if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
                    raise CardError("invalid_card")
                dec_val = Decimal(value) if isinstance(value, int) else value
                if not (Decimal("0") <= dec_val <= Decimal("1")):
                    raise CardError("invalid_card")
                group_vals[group] = dec_val
            entries.append(MetricEntry(name_metric, higher, group_vals))
        metrics = tuple(entries)
    else:
        raise CardError("invalid_card")

    # extra keys
    known = set(_CARD_KEYS)
    extra_keys = tuple(k for k in data if k not in known)

    return ModelCard(
        name=name,
        model_details=str_fields["model_details"],
        intended_use=str_fields["intended_use"],
        metrics=metrics,
        evaluation_data=str_fields["evaluation_data"],
        training_data=str_fields["training_data"],
        version=str_fields["version"],
        license=str_fields["license"],
        tags=tags,
        factors=str_fields["factors"],
        ethical_considerations=str_fields["ethical_considerations"],
        caveats=str_fields["caveats"],
        extra_keys=extra_keys,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = ["model_details", "intended_use", "metrics", "evaluation_data", "training_data"]
_RECOMMENDED_FIELDS = ["factors", "ethical_considerations", "caveats"]


def validate(card: ModelCard) -> list[Issue]:
    """Validate a card and return a list of issues.

    Missing or blank required sections produce errors; missing or blank
    recommended sections produce warnings.  Unknown top-level keys and
    unknown licenses also produce warnings.
    """
    issues: list[Issue] = []

    for field_name in _REQUIRED_FIELDS:
        if field_name == "metrics":
            if not _has_metrics(card.metrics):
                issues.append(Issue("missing_section", field_name, "error"))
        else:
            value = getattr(card, field_name)
            if not value or not value.strip():
                issues.append(Issue("missing_section", field_name, "error"))

    for field_name in _RECOMMENDED_FIELDS:
        value = getattr(card, field_name)
        if not value or not value.strip():
            issues.append(Issue("missing_section", field_name, "warning"))

    for key in card.extra_keys:
        issues.append(Issue("unknown_field", key, "warning"))

    if card.license and card.license not in _LICENSES:
        issues.append(Issue("unknown_license", "license", "warning"))

    return issues


def _has_metrics(metrics: MetricForm) -> bool:
    return bool(metrics)


# ---------------------------------------------------------------------------
# Disparity analysis
# ---------------------------------------------------------------------------


def _iter_metrics(metrics: MetricForm) -> list[tuple[str, bool, GroupValues]]:
    """Flatten both metric forms into a list of (name, higher_is_better, values)."""
    result: list[tuple[str, bool, GroupValues]] = []
    if isinstance(metrics, dict):
        for name, values in metrics.items():
            result.append((name, True, values))
    else:
        for entry in metrics:
            result.append((entry.name, entry.higher_is_better, entry.values))
    return result


def disparities(card: ModelCard, threshold: Decimal = Decimal("0.05")) -> list[Gap]:
    """Compute subgroup disparities versus the best non-'all' group.

    For each metric, the best group is the one with the highest value when
    ``higher_is_better`` is true, otherwise the lowest. Ties are broken by
    lexicographic group name. A gap is reported when its absolute value is
    greater than or equal to ``threshold``.
    """
    gaps: list[Gap] = []
    for metric_name, higher_better, values in _iter_metrics(card.metrics):
        groups = [g for g in values if g != "all"]
        if not groups:
            continue

        if higher_better:
            best_group = sorted(groups, key=lambda g: (-values[g], g))[0]
        else:
            best_group = sorted(groups, key=lambda g: (values[g], g))[0]
        reference_value = values[best_group]

        for group in groups:
            if group == best_group:
                continue
            value = values[group]
            gap = abs(value - reference_value)
            if gap >= threshold:
                gaps.append(
                    Gap(
                        metric=metric_name,
                        group=group,
                        value=value,
                        reference_group=best_group,
                        reference=reference_value,
                        gap=gap,
                    )
                )
    return gaps


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_SECTION_TITLES = [
    "Model Details",
    "Intended Use",
    "Factors",
    "Metrics",
    "Evaluation Data",
    "Training Data",
    "Quantitative Analyses",
    "Ethical Considerations",
    "Caveats and Recommendations",
]


def _escape_text(text: str) -> str:
    """Escape '<' as '&lt;' in all text."""
    return text.replace("<", "&lt;")


def _escape_table_cell(text: str) -> str:
    """Escape both '<' and '|' for table cells."""
    return _escape_text(text).replace("|", "\\|")


def _format_metrics_list(metrics: MetricForm) -> str:
    names = [name for name, _, _ in _iter_metrics(metrics)]
    return ", ".join(names)


def _build_table_rows(metrics: MetricForm) -> list[tuple[str, str, Decimal]]:
    rows: list[tuple[str, str, Decimal]] = []
    for name, _, values in _iter_metrics(metrics):
        for group, value in values.items():
            rows.append((name, group, value))
    return rows


def _format_quantitative(card: ModelCard, threshold: Decimal = Decimal("0.05")) -> str:
    rows = _build_table_rows(card.metrics)
    lines = ["| Metric | Group | Value |", "| --- | --- | --- |"]
    for metric, group, value in rows:
        metric_cell = _escape_table_cell(metric)
        group_cell = _escape_table_cell(group)
        value_str = format(value.quantize(Decimal("0.001")), "f")
        lines.append(f"| {metric_cell} | {group_cell} | {value_str} |")

    gaps = disparities(card, threshold=threshold)
    directions = {name: higher for name, higher, _ in _iter_metrics(card.metrics)}
    for gap in gaps:
        higher = directions.get(gap.metric, True)
        direction = "below" if higher else "above"
        metric_esc = _escape_text(gap.metric)
        group_esc = _escape_text(gap.group)
        ref_esc = _escape_text(gap.reference_group)
        lines.append(
            f"> Disparity: {metric_esc} for {group_esc} is {gap.gap!s} {direction} {ref_esc}."
        )
    return "\n".join(lines)


def render_markdown(card: ModelCard, *, threshold: Decimal = Decimal("0.05")) -> str:
    """Render a card to deterministic Markdown.

    Output starts with YAML front matter (license and tags when present),
    followed by the card name and the sections in the Mitchell et al. order.
    The final string ends with exactly one newline.

    Args:
        card: The card to render.
        threshold: Minimum gap (as a :class:`~decimal.Decimal`) for a disparity
            note to be emitted; defaults to ``Decimal('0.05')``.
    """
    lines: list[str] = []

    # front matter
    lines.append("---")
    if card.license:
        lines.append(f"license: {_escape_text(card.license)}")
    if card.tags:
        lines.append("tags:")
        for tag in card.tags:
            lines.append(f"- {_escape_text(tag)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {_escape_text(card.name)}")
    lines.append("")

    section_contents = [
        ("Model Details", card.model_details),
        ("Intended Use", card.intended_use),
        ("Factors", card.factors),
        ("Metrics", _format_metrics_list(card.metrics)),
        ("Evaluation Data", card.evaluation_data),
        ("Training Data", card.training_data),
        ("Quantitative Analyses", _format_quantitative(card, threshold)),
        ("Ethical Considerations", card.ethical_considerations),
        ("Caveats and Recommendations", card.caveats),
    ]

    for title, content in section_contents:
        if content:
            lines.append(f"## {title}")
            lines.append("")
            if isinstance(content, str):
                lines.extend(_escape_text(content).split("\n"))
            else:  # list of strings (should not happen)
                lines.extend(content)
            lines.append("")

    # Remove any trailing blank lines so the final output ends with exactly
    # one newline after the last non-empty line.
    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines) + "\n"


__all__ = [
    "CardError",
    "Gap",
    "Issue",
    "ModelCard",
    "__version__",
    "disparities",
    "load_card",
    "render_markdown",
    "validate",
]
