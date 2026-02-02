#!/usr/bin/env python3
"""Inspect Mach-O binaries using otool and nm."""

import argparse
import json
import subprocess
import sys


def get_headers(binary_path: str) -> dict:
    """Get Mach-O headers using otool -h."""
    result = subprocess.run(
        ["xcrun", "otool", "-h", binary_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"otool failed: {result.stderr}")

    return {"raw": result.stdout.strip()}


def get_libraries(binary_path: str) -> list[str]:
    """Get linked libraries using otool -L."""
    result = subprocess.run(
        ["xcrun", "otool", "-L", binary_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"otool failed: {result.stderr}")

    libraries = []
    for line in result.stdout.strip().split("\n")[1:]:  # Skip first line (binary path)
        line = line.strip()
        if line:
            # Extract library path (before version info in parens)
            lib = line.split(" (")[0].strip()
            if lib:
                libraries.append(lib)
    return libraries


def get_symbols(binary_path: str, limit: int = 50) -> list[dict]:
    """Get symbols using nm."""
    result = subprocess.run(
        ["xcrun", "nm", "-g", binary_path],  # -g for external symbols only
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # nm may fail on some binaries, try without -g
        result = subprocess.run(
            ["xcrun", "nm", binary_path],
            capture_output=True,
            text=True,
        )

    symbols = []
    for line in result.stdout.strip().split("\n")[:limit]:
        parts = line.split()
        if len(parts) >= 2:
            # Format: [address] type name
            if len(parts) == 3:
                symbols.append(
                    {
                        "address": parts[0],
                        "type": parts[1],
                        "name": parts[2],
                    }
                )
            elif len(parts) == 2:
                symbols.append(
                    {
                        "type": parts[0],
                        "name": parts[1],
                    }
                )
    return symbols


def get_swift_symbols(binary_path: str, limit: int = 50) -> list[str]:
    """Get demangled Swift symbols."""
    # Get symbols and pipe through swift-demangle
    nm_result = subprocess.run(
        ["xcrun", "nm", binary_path],
        capture_output=True,
        text=True,
    )

    if nm_result.returncode != 0:
        return []

    # Filter for Swift symbols (start with _$s) and demangle
    swift_mangled = []
    for line in nm_result.stdout.split("\n"):
        if "_$s" in line or "_$S" in line:
            parts = line.split()
            if parts:
                swift_mangled.append(parts[-1])

    if not swift_mangled:
        return []

    # Demangle
    demangle_input = "\n".join(swift_mangled[:limit])
    demangle_result = subprocess.run(
        ["xcrun", "swift-demangle"],
        input=demangle_input,
        capture_output=True,
        text=True,
    )

    if demangle_result.returncode == 0:
        return [
            s.strip() for s in demangle_result.stdout.strip().split("\n") if s.strip()
        ]
    return swift_mangled[:limit]


def main():
    parser = argparse.ArgumentParser(
        description="Inspect Mach-O binary files",
        epilog="Examples:\n"
        "  %(prog)s --libraries /path/to/MyApp.app/MyApp\n"
        "  %(prog)s --swift-symbols /path/to/binary --limit 100",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("binary", help="Path to binary file")
    parser.add_argument("--headers", action="store_true", help="Show Mach-O headers")
    parser.add_argument(
        "--libraries", "-L", action="store_true", help="Show linked libraries"
    )
    parser.add_argument("--symbols", "-s", action="store_true", help="Show symbols")
    parser.add_argument(
        "--swift-symbols", action="store_true", help="Show demangled Swift symbols"
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Limit number of symbols (default: 50)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Default to libraries if nothing specified
    if not any([args.headers, args.libraries, args.symbols, args.swift_symbols]):
        args.libraries = True

    try:
        result = {"binary": args.binary}

        if args.headers:
            headers = get_headers(args.binary)
            result["headers"] = headers

        if args.libraries:
            libs = get_libraries(args.binary)
            result["libraries"] = libs
            result["library_count"] = len(libs)

        if args.symbols:
            syms = get_symbols(args.binary, args.limit)
            result["symbols"] = syms
            result["symbol_count"] = len(syms)

        if args.swift_symbols:
            swift_syms = get_swift_symbols(args.binary, args.limit)
            result["swift_symbols"] = swift_syms
            result["swift_symbol_count"] = len(swift_syms)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Binary: {args.binary}\n")

            if args.headers and "headers" in result:
                print("Headers:")
                print(result["headers"]["raw"])
                print()

            if args.libraries and "libraries" in result:
                print(f"Linked Libraries ({result['library_count']}):")
                for lib in result["libraries"]:
                    print(f"  {lib}")
                print()

            if args.symbols and "symbols" in result:
                print(f"Symbols ({result['symbol_count']} shown):")
                for sym in result["symbols"]:
                    print(f"  [{sym.get('type', '?')}] {sym['name']}")
                print()

            if args.swift_symbols and "swift_symbols" in result:
                print(f"Swift Symbols ({result['swift_symbol_count']} shown):")
                for sym in result["swift_symbols"]:
                    print(f"  {sym}")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
