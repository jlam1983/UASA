#!/usr/bin/env python3
"""Main entry point for Multi-File Type Input System."""

import sys
import argparse
import json
from pathlib import Path

from multi_file_input import (
    DataIngestionPipeline,
    JSONNormalizer,
    ChannelAdapterFactory,
    IngestionError,
)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-File Type Input System - Data Ingestion Pipeline"
    )
    parser.add_argument(
        "source",
        help="Source file path or URL",
    )
    parser.add_argument(
        "-c",
        "--channel",
        choices=["file", "api", "stream", "iot", "database"],
        default="file",
        help="Input channel type (default: file)",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="File type (csv, json, xml, xlsx, yaml, parquet, avro)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Include raw data in normalized output",
    )
    parser.add_argument(
        "--config",
        help="Path to configuration YAML file",
    )

    args = parser.parse_args()

    normalizer = JSONNormalizer(include_raw=args.include_raw)
    pipeline = DataIngestionPipeline(normalizer=normalizer)

    try:
        result = pipeline.ingest(
            source=args.source,
            channel_type=args.channel,
            file_type=args.type,
        )

        output = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Output written to {args.output}")
        else:
            print(output)

    except IngestionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
