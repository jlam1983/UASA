#!/usr/bin/env python3
"""Command line interface for Content Sampler."""

import sys
import json
import argparse
from pathlib import Path

from content_sampler import ContentSampler


def main():
    parser = argparse.ArgumentParser(description="Content Sampler - Sample, Analyze, and Label")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-s", "--sample-size", type=int, default=1000, help="Sample size")
    parser.add_argument("--strategy", choices=["random", "stratified", "systematic", "time_based", "cluster"], default="random", help="Sampling strategy")
    parser.add_argument("--stratify-by", help="Field to stratify by")
    parser.add_argument("--analyze-schema", action="store_true", help="Analyze schema")
    parser.add_argument("--optimize-for", choices=["sqlite", "postgresql", "mysql", "sqlserver", "mongodb"], help="Optimize schema for target")
    parser.add_argument("--detect-noise", action="store_true", help="Detect noise")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both raw array and normalized format
    if isinstance(data, dict) and "records" in data:
        records = [r["_source"] for r in data["records"]]
    elif isinstance(data, list):
        records = data
    else:
        print("Error: Input must be JSON array or normalized format", file=sys.stderr)
        sys.exit(1)

    # Initialize sampler
    sampler = ContentSampler(default_strategy=args.strategy)

    # Build kwargs
    kwargs = {}
    if args.stratify_by:
        kwargs["stratify_by"] = args.stratify_by

    # Sample with analysis
    result = sampler.sample_with_analysis(
        records,
        sample_size=args.sample_size,
        strategy=args.strategy,
        analyze_schema=args.analyze_schema or args.optimize_for is not None,
        detect_noise=args.detect_noise,
        **kwargs
    )

    # Optimize schema if requested
    if args.optimize_for and "schema_analysis" in result:
        result["optimized_schema"] = sampler.optimize_schema(
            result["schema_analysis"],
            target=args.optimize_for
        )

    # Output
    output = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
