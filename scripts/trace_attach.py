#!/usr/bin/env python3
"""Attach to a running process and record a trace."""

import argparse
import json
import subprocess
import sys
from trace_record import record_trace


def find_process(name: str) -> dict | None:
    """Find a process by name and return its info."""
    result = subprocess.run(
        ["pgrep", "-l", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    lines = result.stdout.strip().split("\n")
    if not lines or not lines[0]:
        return None

    # Return first match
    parts = lines[0].split(None, 1)
    if len(parts) >= 2:
        return {"pid": parts[0], "name": parts[1]}
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Attach to a running process and record a trace",
        epilog="Examples:\n"
        "  %(prog)s --name MyApp --template 'Time Profiler' --time-limit 10s\n"
        "  %(prog)s --pid 1234 --template Allocations --time-limit 30s",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", "-n", help="Process name to attach to")
    parser.add_argument("--pid", "-p", help="Process ID to attach to")
    parser.add_argument(
        "--template",
        "-t",
        default="Time Profiler",
        help="Instruments template (default: Time Profiler)",
    )
    parser.add_argument(
        "--time-limit", default="10s", help="Recording time limit (default: 10s)"
    )
    parser.add_argument("--output", "-o", help="Output .trace file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.name and not args.pid:
        parser.error("Either --name or --pid is required")

    try:
        # Resolve process name to PID if needed
        attach_target = args.pid
        process_info = None

        if args.name and not args.pid:
            process_info = find_process(args.name)
            if not process_info:
                raise RuntimeError(f"Process not found: {args.name}")
            attach_target = process_info["pid"]
            if not args.json:
                print(
                    f"Found process: {process_info['name']} (PID {process_info['pid']})"
                )

        result = record_trace(
            template=args.template,
            output=args.output,
            attach=attach_target,
            time_limit=args.time_limit,
            quiet=args.json,
        )

        if process_info:
            result["process"] = process_info

        if args.json:
            print(json.dumps(result))
        else:
            if result["success"]:
                print(f"\nTrace saved: {result['output']} ({result['size_mb']} MB)")
                print(f"Open in Instruments: open '{result['output']}'")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
