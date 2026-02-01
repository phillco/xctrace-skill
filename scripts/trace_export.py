#!/usr/bin/env python3
"""Export trace data to XML/JSON for analysis."""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET


def export_toc(input_path: str) -> dict:
    """Export table of contents from trace file."""
    result = subprocess.run(
        ["xcrun", "xctrace", "export", "--input", input_path, "--toc"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"xctrace export failed: {result.stderr}")

    # Parse XML output
    try:
        root = ET.fromstring(result.stdout)
        toc = parse_toc_xml(root)
        return {"success": True, "toc": toc, "raw_xml": result.stdout}
    except ET.ParseError as e:
        return {"success": True, "raw": result.stdout, "parse_error": str(e)}


def parse_toc_xml(root: ET.Element) -> dict:
    """Parse xctrace TOC XML into structured dict."""
    toc = {"runs": []}

    for run in root.findall(".//run"):
        run_info = {
            "number": run.get("number"),
            "tables": [],
        }
        for table in run.findall(".//table"):
            run_info["tables"].append(
                {
                    "schema": table.get("schema"),
                    "target": table.get("target-pid"),
                }
            )
        toc["runs"].append(run_info)

    return toc


def export_xpath(input_path: str, xpath: str, output_path: str | None = None) -> dict:
    """Export specific data using XPath query."""
    cmd = ["xcrun", "xctrace", "export", "--input", input_path, "--xpath", xpath]
    if output_path:
        cmd.extend(["--output", output_path])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"xctrace export failed: {result.stderr}")

    return {
        "success": True,
        "output": output_path if output_path else "stdout",
        "data": result.stdout if not output_path else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export trace data for analysis",
        epilog="Examples:\n"
        "  %(prog)s --input recording.trace --toc\n"
        "  %(prog)s --input recording.trace --xpath '/trace-toc/run[@number=\"1\"]/data/table'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, help="Input .trace file")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--toc", action="store_true", help="Export table of contents")
    parser.add_argument("--xpath", help="XPath query for specific data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.toc and not args.xpath:
        args.toc = True  # Default to TOC

    try:
        if args.toc:
            result = export_toc(args.input)
        else:
            result = export_xpath(args.input, args.xpath, args.output)

        if args.json:
            # Don't include raw_xml in JSON output (too large)
            if "raw_xml" in result:
                del result["raw_xml"]
            print(json.dumps(result, indent=2))
        else:
            if args.toc and "toc" in result:
                toc = result["toc"]
                print(f"Trace: {args.input}")
                print(f"Runs: {len(toc['runs'])}\n")
                for run in toc["runs"]:
                    print(f"  Run {run['number']}:")
                    for table in run["tables"]:
                        print(f"    - {table['schema']}")
            elif "raw" in result:
                print(result["raw"])
            elif "data" in result and result["data"]:
                print(result["data"])
            else:
                print(f"Exported to: {result.get('output')}")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
