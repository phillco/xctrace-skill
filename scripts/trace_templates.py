#!/usr/bin/env python3
"""List available Instruments templates."""

import argparse
import json
import subprocess
import sys


def list_templates() -> list[str]:
    """Get list of available xctrace templates."""
    result = subprocess.run(
        ["xcrun", "xctrace", "list", "templates"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"xctrace failed: {result.stderr}")

    templates = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        # Skip header lines
        if line and not line.startswith("==") and line != "":
            templates.append(line)
    return templates


def main():
    parser = argparse.ArgumentParser(description="List available Instruments templates")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        templates = list_templates()

        if args.json:
            print(json.dumps({"templates": templates, "count": len(templates)}))
        else:
            print(f"Available templates ({len(templates)}):\n")
            for t in templates:
                print(f"  {t}")
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
