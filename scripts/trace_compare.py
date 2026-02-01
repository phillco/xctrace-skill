#!/usr/bin/env python3
"""Compare two trace files for before/after performance analysis."""

import argparse
import json
import os
import sys


def get_trace_size(path: str) -> float:
    """Get trace file size in MB."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Trace not found: {path}")
    return os.path.getsize(path) / (1024 * 1024)


def compare_traces(baseline_path: str, current_path: str) -> dict:
    """Compare two traces and generate comparison report."""

    baseline_size = get_trace_size(baseline_path)
    current_size = get_trace_size(current_path)

    comparison = {
        "baseline": {
            "path": baseline_path,
            "size_mb": round(baseline_size, 2),
        },
        "current": {
            "path": current_path,
            "size_mb": round(current_size, 2),
        },
        "size_diff_mb": round(current_size - baseline_size, 2),
        "size_diff_percent": round(
            ((current_size - baseline_size) / baseline_size) * 100, 1
        )
        if baseline_size > 0
        else 0,
        "recommendation": "",
    }

    # Note: xctrace doesn't have a built-in compare command
    # For detailed comparison, traces need to be opened in Instruments
    comparison["recommendation"] = (
        "For detailed comparison, open both traces in Instruments.app side-by-side. "
        "Use File > Open to load each trace, then compare the same time intervals."
    )

    comparison["manual_steps"] = [
        f"1. Open baseline: open '{baseline_path}'",
        f"2. Open current: open '{current_path}'",
        "3. In Instruments, select matching time ranges",
        "4. Compare call trees, allocations, or other metrics",
    ]

    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Compare two trace files",
        epilog="Examples:\n  %(prog)s --baseline before.trace --current after.trace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--baseline", "-b", required=True, help="Baseline .trace file")
    parser.add_argument(
        "--current", "-c", required=True, help="Current .trace file to compare"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        comparison = compare_traces(args.baseline, args.current)

        if args.json:
            print(json.dumps(comparison, indent=2))
        else:
            print("Trace Comparison")
            print("=" * 40)
            print(
                f"Baseline: {comparison['baseline']['path']} ({comparison['baseline']['size_mb']} MB)"
            )
            print(
                f"Current:  {comparison['current']['path']} ({comparison['current']['size_mb']} MB)"
            )
            print()
            print(
                f"Size difference: {comparison['size_diff_mb']:+.2f} MB ({comparison['size_diff_percent']:+.1f}%)"
            )
            print()
            print("To compare in detail:")
            for step in comparison["manual_steps"]:
                print(f"  {step}")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
