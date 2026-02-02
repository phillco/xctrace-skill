#!/usr/bin/env python3
"""Analyze a trace file and generate a performance summary."""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def get_trace_info(input_path: str) -> dict:
    """Get basic info about a trace file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Trace not found: {input_path}")

    size_mb = os.path.getsize(input_path) / (1024 * 1024)

    # Get TOC
    result = subprocess.run(
        ["xcrun", "xctrace", "export", "--input", input_path, "--toc"],
        capture_output=True,
        text=True,
    )

    info = {
        "path": input_path,
        "size_mb": round(size_mb, 2),
        "runs": [],
        "schemas": [],
    }

    if result.returncode == 0:
        try:
            root = ET.fromstring(result.stdout)
            for run in root.findall(".//run"):
                run_num = run.get("number")
                tables = []
                for table in run.findall(".//table"):
                    schema = table.get("schema")
                    if schema:
                        tables.append(schema)
                        if schema not in info["schemas"]:
                            info["schemas"].append(schema)
                info["runs"].append({"number": run_num, "tables": tables})
        except ET.ParseError:
            pass

    return info


def analyze_trace(input_path: str, verbose: bool = False) -> dict:
    """Analyze trace and extract key insights."""
    info = get_trace_info(input_path)

    analysis = {
        "file": info["path"],
        "size_mb": info["size_mb"],
        "runs": len(info["runs"]),
        "available_data": info["schemas"],
        "insights": [],
    }

    # Provide insights based on available schemas
    schema_insights = {
        "time-profile": "CPU profiling data available - look for hot functions",
        "allocations": "Memory allocation data - check for excessive allocations",
        "leaks": "Memory leak detection - review any leaked objects",
        "hangs": "Hang/hitch data - identifies UI responsiveness issues",
        "signpost": "Signpost intervals - custom performance markers",
        "os-signpost": "OS-level signposts - system performance data",
        "kdebug": "Kernel debug data - low-level system tracing",
        "metal-gpu": "Metal GPU data - graphics performance",
        "core-animation": "Core Animation commits - UI rendering",
    }

    for schema in info["schemas"]:
        schema_lower = schema.lower()
        for key, insight in schema_insights.items():
            if key in schema_lower:
                analysis["insights"].append(insight)
                break

    if not analysis["insights"]:
        analysis["insights"].append(
            f"Trace contains {len(info['schemas'])} data tables. "
            "Open in Instruments.app for detailed analysis."
        )

    # Add suggestions
    analysis["next_steps"] = [
        f"Open in Instruments: open '{input_path}'",
        "Export specific data: trace_export.py --xpath '<query>'",
    ]

    if verbose:
        analysis["all_schemas"] = info["schemas"]
        analysis["runs_detail"] = info["runs"]

    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a trace file and generate summary",
        epilog="Examples:\n"
        "  %(prog)s --input recording.trace\n"
        "  %(prog)s --input recording.trace --verbose",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, help="Input .trace file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed info"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        analysis = analyze_trace(args.input, verbose=args.verbose)

        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            print(f"Trace Analysis: {analysis['file']}")
            print(f"Size: {analysis['size_mb']} MB")
            print(f"Runs: {analysis['runs']}")
            print()

            if analysis["insights"]:
                print("Insights:")
                for insight in analysis["insights"]:
                    print(f"  - {insight}")
                print()

            print("Available data types:")
            for schema in analysis["available_data"][:10]:
                print(f"  - {schema}")
            if len(analysis["available_data"]) > 10:
                print(f"  ... and {len(analysis['available_data']) - 10} more")
            print()

            print("Next steps:")
            for step in analysis["next_steps"]:
                print(f"  {step}")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
