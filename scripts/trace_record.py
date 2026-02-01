#!/usr/bin/env python3
"""Record a performance trace using xctrace."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def record_trace(
    template: str,
    output: str | None = None,
    attach: str | None = None,
    launch: list[str] | None = None,
    all_processes: bool = False,
    time_limit: str | None = None,
    device: str | None = None,
    quiet: bool = False,
) -> dict:
    """Record a trace and return info about the recording."""

    # Build command
    cmd = ["xcrun", "xctrace", "record"]

    cmd.extend(["--template", template])

    if output:
        cmd.extend(["--output", output])
    else:
        # Generate default output name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_slug = template.lower().replace(" ", "_")
        output = f"{template_slug}_{timestamp}.trace"
        cmd.extend(["--output", output])

    if device:
        cmd.extend(["--device", device])

    if time_limit:
        cmd.extend(["--time-limit", time_limit])

    # Target selection (mutually exclusive)
    if attach:
        cmd.extend(["--attach", attach])
    elif launch:
        cmd.append("--launch")
        cmd.append("--")
        cmd.extend(launch)
    elif all_processes:
        cmd.append("--all-processes")
    else:
        # Default to all processes if no target specified
        cmd.append("--all-processes")

    cmd.append("--no-prompt")

    if quiet:
        cmd.append("--quiet")

    if not quiet:
        print(f"Recording with template: {template}")
        if time_limit:
            print(f"Time limit: {time_limit}")
        print(f"Output: {output}")
        print("Recording... (Ctrl+C to stop)\n")

    # Run xctrace
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except KeyboardInterrupt:
        # xctrace handles SIGINT gracefully and saves the trace
        pass

    # Check if trace was created
    if os.path.exists(output):
        size_mb = os.path.getsize(output) / (1024 * 1024)
        return {
            "success": True,
            "output": output,
            "size_mb": round(size_mb, 2),
            "template": template,
        }
    else:
        error = result.stderr if result else "Recording interrupted"
        return {
            "success": False,
            "error": error,
            "template": template,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Record a performance trace",
        epilog="Examples:\n"
        "  %(prog)s --template 'Time Profiler' --attach MyApp --time-limit 10s\n"
        "  %(prog)s --template Allocations --all-processes --time-limit 30s\n"
        "  %(prog)s --template 'App Launch' --launch -- /path/to/MyApp.app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--template", "-t", required=True, help="Instruments template name"
    )
    parser.add_argument("--output", "-o", help="Output .trace file path")
    parser.add_argument("--attach", "-a", help="Attach to process by name or PID")
    parser.add_argument(
        "--launch",
        nargs=argparse.REMAINDER,
        help="Launch command (use -- before command)",
    )
    parser.add_argument(
        "--all-processes", action="store_true", help="Record all processes"
    )
    parser.add_argument("--time-limit", help="Recording time limit (e.g., 10s, 5m)")
    parser.add_argument("--device", help="Device name or UDID")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = record_trace(
        template=args.template,
        output=args.output,
        attach=args.attach,
        launch=args.launch,
        all_processes=args.all_processes,
        time_limit=args.time_limit,
        device=args.device,
        quiet=args.json,
    )

    if args.json:
        print(json.dumps(result))
    else:
        if result["success"]:
            print(f"\nTrace saved: {result['output']} ({result['size_mb']} MB)")
            print(f"Open in Instruments: open '{result['output']}'")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
