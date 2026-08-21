from __future__ import annotations

import argparse
from collections.abc import Sequence

from .evaluator import ArtifactValidationError, evaluate_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a prediction from frozen disk artifacts only."
    )
    parser.add_argument("--prediction", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--metric-spec", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        evaluate_files(
            prediction_path=args.prediction,
            oracle_path=args.oracle,
            split_manifest_path=args.split,
            metric_spec_path=args.metric_spec,
            output_path=args.out,
        )
    except ArtifactValidationError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
