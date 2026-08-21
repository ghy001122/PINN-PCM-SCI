from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .qpop_conversion import (
    QPopConversionError,
    QPopConversionRequest,
    convert_qpop_run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert one completed native Q-POP run into a canonical artifact bundle."
    )
    parser.add_argument("--native-run", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = convert_qpop_run(
            QPopConversionRequest(
                native_run_dir=args.native_run,
                conversion_spec_path=args.spec,
                bundle_dir=args.bundle,
            )
        )
    except QPopConversionError as exc:
        print(json.dumps({"status": "REJECTED", "error_code": exc.code}), file=sys.stderr)
        return 2
    print(json.dumps(report.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
