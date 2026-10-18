"""Backward-compatible CLI. Remote evaluations require explicit billing flags."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, cast

from . import __version__, compress_prompt
from .benchmarks.laboratory import run_laboratory
from .benchmarks.reporting import write_report
from .benchmarks.runner import run_offline
from .exceptions import TokenPropulsionError
from .security import MAX_INPUT_BYTES
from .strategies import TaskValidator
from .tokenizer import EstimatedTokenizer, TiktokenTokenizer, Tokenizer


def _input(args: argparse.Namespace, text: str | None) -> str:
    if args.file and text is not None:
        raise ValueError("use either text or file")
    if args.file:
        if args.file.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("input exceeds byte limit")
        with args.file.open("rb") as stream:
            return cast(str, stream.read(MAX_INPUT_BYTES + 1).decode("utf-8"))
    if text is None:
        if hasattr(sys.stdin, "buffer"):
            return sys.stdin.buffer.read(MAX_INPUT_BYTES + 1).decode("utf-8")
        return sys.stdin.read(MAX_INPUT_BYTES + 1)
    return text


def _remote(args: argparse.Namespace) -> dict[str, Any]:
    from .adapters.xai import XAIAdapter
    from .benchmarks.remote import run_xai_study
    from .budget import RequestBudget

    if not (args.allow_network and args.authorize_billing and args.model and args.compare):
        raise ValueError("xai needs model, compare, network and explicit billing authorization")
    if args.budget_usd is None or args.reserve_usd_per_request is None:
        raise ValueError("xai requires a budget and reviewed per-request reservation")
    budget = RequestBudget(args.budget_usd, args.reserve_usd_per_request, args.max_requests)
    adapter = XAIAdapter(
        args.model,
        allow_network=True,
        budget=budget,
        max_output_tokens=args.max_output_tokens,
        max_retries=0,
    )
    return run_xai_study(args.dataset, adapter, repeats=args.repeats, billing_authorized=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokenpropulsion",
        description="Offline optimization: compress, analyze, benchmark, compare, doctor, version",
    )
    parser.add_argument("text", nargs="?")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--level", choices=["low", "medium", "high", "adaptive"], default="medium")
    parser.add_argument("--strategy", choices=["conservative", "structural", "lexical", "semantic"])
    parser.add_argument(
        "--contract",
        choices=["paragraph-set"],
        help="declare paragraph multiplicity irrelevant; not a semantic proof",
    )
    parser.add_argument("-f", "--file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument(
        "--json", action="store_true", help="include prompt text in explicit JSON export"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--report",
        nargs="?",
        type=Path,
        const=Path("benchmarks/results/new-run"),
        help="new empty report directory",
    )
    parser.add_argument("--provider", choices=["offline", "xai"], default="offline")
    parser.add_argument("--model")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument(
        "--authorize-billing",
        action="store_true",
        help="authorize billable provider calls; reservations are not a provider hard cap",
    )
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--reserve-usd-per-request", type=float)
    parser.add_argument("--max-requests", type=int, default=32)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--tokenizer", choices=["estimate", "tiktoken"], default="estimate")
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--allow-tokenizer-download", action="store_true")
    args = parser.parse_args(argv)
    try:
        command = (
            args.text
            if args.text in {"compress", "analyze", "benchmark", "compare", "doctor", "version"}
            else "compress"
        )
        if args.prompt is not None and args.text not in {"compress", "analyze", "compare"}:
            parser.error("unexpected extra positional prompt")
        if command == "version":
            output = __version__ + "\n"
        elif command == "doctor":
            output = (
                json.dumps(
                    {
                        "version": __version__,
                        "offline_default": True,
                        "xai_key_configured": bool(os.environ.get("XAI_API_KEY")),
                        "live_provider_verified": False,
                    }
                )
                + "\n"
            )
        elif command == "benchmark":
            if args.dataset is None:
                parser.error("benchmark requires --dataset")
            if args.report and args.report.exists() and any(args.report.iterdir()):
                raise ValueError("report directory contains previous evidence")
            counter: Tokenizer = EstimatedTokenizer()
            if args.tokenizer == "tiktoken":
                counter = TiktokenTokenizer.load(
                    args.encoding, allow_network=args.allow_tokenizer_download
                )
            if args.provider == "xai":
                result = _remote(args)
                if args.report:
                    write_report(result, args.report / "remote.json")
            elif args.report:
                result = run_laboratory(
                    args.dataset, args.report, repeats=args.repeats, tokenizer=counter
                )
            else:
                result = run_offline(args.dataset, args.repeats, args.level)
            output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        else:
            raw = args.prompt if args.text in {"compress", "analyze", "compare"} else args.text
            if args.file and raw is not None:
                parser.error("use either positional text or --file")
            text = _input(args, raw)
            validator = None
            if args.contract:
                validator = TaskValidator(
                    "declared-paragraph-set",
                    lambda a, b: set(re.split(r"\n\n+", a)) == set(re.split(r"\n\n+", b)),
                )
            compressed = compress_prompt(
                text, args.level, strategy=args.strategy, task_validator=validator
            )
            if args.json or command in {"analyze", "compare"}:
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
        elif hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(output.encode("utf-8"))
        else:
            sys.stdout.write(output)
        return 0
    except BrokenPipeError:
        return 1
    except (TokenPropulsionError, OSError, ValueError, UnicodeError, RecursionError):
        print(
            "tokenpropulsion: invalid input, configuration, dataset, or inaccessible file",
            file=sys.stderr,
        )
        return 2
