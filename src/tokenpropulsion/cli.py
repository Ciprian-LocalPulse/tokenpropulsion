"""Text on stdout; statistics on stderr. JSON is an explicit prompt-bearing export."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__, compress_prompt
from .benchmarks.runner import run_offline
from .exceptions import TokenPropulsionError
from .security import MAX_INPUT_BYTES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokenpropulsion", description="Offline prompt formatting"
    )
    parser.add_argument("text", nargs="?")
    parser.add_argument("--level", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("-f", "--file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--json", action="store_true", help="include prompt text in JSON")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        if args.text == "benchmark":
            if args.dataset is None:
                parser.error("benchmark requires --dataset")
            result = run_offline(args.dataset, args.repeats, args.level)
            output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        else:
            if args.file and args.text not in {None, "analyze"}:
                parser.error("use either positional text or --file")
            if args.file:
                if args.file.stat().st_size > MAX_INPUT_BYTES:
                    raise ValueError("input exceeds byte limit")
                with args.file.open("rb") as stream:
                    text = stream.read(MAX_INPUT_BYTES + 1).decode("utf-8")
            elif args.text in {None, "analyze"}:
                if hasattr(sys.stdin, "buffer"):
                    text = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1).decode("utf-8")
                else:
                    text = sys.stdin.read(MAX_INPUT_BYTES + 1)
            else:
                text = args.text
            compressed = compress_prompt(text, args.level)
            if args.json or args.text == "analyze":
                output = json.dumps(compressed.to_dict(), ensure_ascii=False, indent=2) + "\n"
            else:
                output = compressed.optimized_text
            if args.stats:
                stats = compressed.to_dict()
                for key in ("original_text", "optimized_text", "transformations"):
                    stats.pop(key)
                print(json.dumps(stats), file=sys.stderr)
        if args.output:
            args.output.write_text(output, encoding="utf-8", newline="")
        else:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout.buffer.write(output.encode("utf-8"))
            else:
                sys.stdout.write(output)
        return 0
    except BrokenPipeError:
        return 1
    except (TokenPropulsionError, OSError, ValueError, UnicodeError):
        print("tokenpropulsion: invalid input, dataset, or inaccessible file", file=sys.stderr)
        return 2
