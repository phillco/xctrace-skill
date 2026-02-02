# xctrace-skill

A [Claude Code](https://github.com/anthropics/claude-code) skill for iOS/macOS performance profiling using Apple's Instruments toolchain (`xctrace`).

## Why a Skill Instead of an MCP Server?

MCP servers load all their tools into the context window at session start (thousands of tokens). Skills use **progressive disclosure** - only ~25 tokens for the description, with full documentation loaded on-demand when relevant.

This means you can have profiling capabilities available without paying the context cost until you actually need them.

## Installation

Clone to your Claude Code skills directory:

```bash
git clone https://github.com/phillco/xctrace-skill.git ~/.claude/skills/xctrace-skill
```

Restart Claude Code. The skill will be automatically detected.

## Usage

Claude automatically invokes these scripts when you ask things like:
- "This scroll is janky, can you profile it?"
- "Check for memory leaks in MyApp"
- "What libraries does this binary link against?"
- "Compare performance before and after my changes"

## Scripts

| Script | Purpose |
|--------|---------|
| `trace_templates.py` | List available Instruments templates (Time Profiler, Allocations, etc.) |
| `trace_record.py` | Record performance traces with configurable templates and time limits |
| `trace_attach.py` | Attach to and profile a running process |
| `trace_export.py` | Export trace data to XML/JSON for analysis |
| `trace_analyze.py` | Generate performance summaries from trace files |
| `trace_compare.py` | Compare two traces (before/after optimization) |
| `binary_inspect.py` | Inspect Mach-O binaries (linked libraries, symbols, Swift symbols) |

All scripts support `--help` for detailed options and `--json` for machine-readable output.

## Common Templates

| Template | Use Case |
|----------|----------|
| Time Profiler | CPU usage, find slow functions |
| Allocations | Memory usage, object lifetimes |
| Leaks | Memory leaks |
| SwiftUI | SwiftUI view body evaluations |
| Animation Hitches | UI jank, dropped frames |
| App Launch | Startup time analysis |
| Swift Concurrency | Actor isolation, task scheduling |

## Requirements

- macOS 12+
- Xcode Command Line Tools
- Python 3

## License

MIT
