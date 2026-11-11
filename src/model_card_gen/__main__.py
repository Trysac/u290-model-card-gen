"""Command-line interface for model_card_gen."""

from __future__ import annotations

import argparse
import pathlib
import sys
from decimal import Decimal

from . import CardError, load_card, render_markdown, validate


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command-line arguments (``None`` means ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 when validation errors exist, 2 for
        usage or I/O errors.
    """
    parser = argparse.ArgumentParser(prog="model-card-gen")
    parser.add_argument("card", help="path to the card JSON file")
    parser.add_argument("--out", help="write rendered Markdown to this file")
    parser.add_argument("--check", action="store_true", help="validate and print issues")
    parser.add_argument(
        "--threshold",
        type=Decimal,
        default=Decimal("0.05"),
        help="minimum gap for a disparity note (default: 0.05)",
    )
    args = parser.parse_args(argv)

    if not args.out and not args.check:
        parser.print_usage(sys.stderr)
        return 2

    card_path = pathlib.Path(args.card)
    try:
        text = card_path.read_text(encoding="utf-8")
    except OSError:
        print(f"error: cannot read {args.card}", file=sys.stderr)
        return 2

    try:
        card = load_card(text)
    except CardError as exc:
        print(f"error {exc.code}", file=sys.stderr)
        return 1

    if args.check:
        issues = validate(card)
        for issue in issues:
            print(f"{issue.severity} {issue.code} {issue.field}")
        return 1 if any(issue.severity == "error" for issue in issues) else 0

    if args.out:
        try:
            rendered = render_markdown(card, threshold=args.threshold)
            out_path = pathlib.Path(args.out)
            out_path.write_text(rendered, encoding="utf-8")
        except OSError:
            print(f"error: cannot write {args.out}", file=sys.stderr)
            return 2
        return 0

    return 2  # unreachable, kept for type completeness
