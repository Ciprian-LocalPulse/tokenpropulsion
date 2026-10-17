"""Explicit network experiment. Review the entire dataset first. Costs money."""

import argparse
from pathlib import Path

from tokenpropulsion.adapters.xai import XAIAdapter
from tokenpropulsion.benchmarks.quality import evaluate
from tokenpropulsion.benchmarks.reporting import write_report
from tokenpropulsion.benchmarks.runner import run_remote

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--allow-network", action="store_true", required=True)
args = parser.parse_args()
adapter = XAIAdapter(args.model, allow_network=args.allow_network)
write_report(
    run_remote(args.dataset, adapter, lambda output, row: evaluate(output, row["expected_output"])),
    args.output,
)
