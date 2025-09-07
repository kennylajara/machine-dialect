#!/usr/bin/env python3
"""
Visualize benchmark results with a performance chart.
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_results(filename: str = "benchmark_results.json") -> dict[str, Any]:
    """Load benchmark results from JSON file."""
    if not Path(filename).exists():
        print(f"Error: {filename} not found. Run the benchmark first.")
        sys.exit(1)

    with open(filename) as f:
        data: dict[str, Any] = json.load(f)
        return data


def print_chart(results: dict[str, Any]) -> None:
    """Print a visual bar chart of performance results."""
    # Sort by median time
    sorted_results = sorted(results["results"], key=lambda x: x["median_ms"])

    if not sorted_results:
        print("No results to display")
        return

    # Find the maximum time for scaling
    max_time = max(r["median_ms"] for r in sorted_results)

    # Chart width
    chart_width = 50

    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON - Fibonacci(40)")
    print("=" * 80)
    print(f"\n{'Language':<25} {'Time (ms)':<12} Performance")
    print("-" * 80)

    for r in sorted_results:
        name = r["language"]
        time_ms = r["median_ms"]
        mode = r["mode"]
        valid = r.get("valid", True)

        # Calculate bar length
        bar_length = int((time_ms / max_time) * chart_width)
        bar = "█" * bar_length

        # Format the output
        valid_mark = "" if valid else " ⚠"
        name_display = f"{name}{valid_mark}"

        # Color coding based on mode
        mode_marker = {"compiled": "●", "jit": "◆", "interpreted": "○", "bytecode": "■"}.get(mode, "·")

        print(f"{name_display:<25} {time_ms:<12.1f} {mode_marker} {bar}")

    print("\n" + "=" * 80)
    print("LEGEND:")
    print("● Compiled  ◆ JIT  ○ Interpreted  ■ Bytecode  ⚠ Invalid Output")
    print("=" * 80)

    # Performance tiers
    print("\nPERFORMANCE TIERS:")
    tiers = [
        ("Tier 1 (< 500ms)", "Native compiled with optimizations"),
        ("Tier 2 (500-1000ms)", "Native compiled with GC / JIT warming up"),
        ("Tier 3 (1-3s)", "JIT compiled languages"),
        ("Tier 4 (3-10s)", "Optimized interpreters"),
        ("Tier 5 (10-30s)", "Standard interpreters"),
        ("Tier 6 (> 30s)", "Unoptimized interpreters"),
    ]

    for tier, desc in tiers:
        # Count languages in this tier
        tier_langs = []
        if "< 500" in tier:
            tier_langs = [r["language"] for r in sorted_results if r["median_ms"] < 500]
        elif "500-1000" in tier:
            tier_langs = [r["language"] for r in sorted_results if 500 <= r["median_ms"] < 1000]
        elif "1-3s" in tier:
            tier_langs = [r["language"] for r in sorted_results if 1000 <= r["median_ms"] < 3000]
        elif "3-10s" in tier:
            tier_langs = [r["language"] for r in sorted_results if 3000 <= r["median_ms"] < 10000]
        elif "10-30s" in tier:
            tier_langs = [r["language"] for r in sorted_results if 10000 <= r["median_ms"] < 30000]
        else:  # > 30s
            tier_langs = [r["language"] for r in sorted_results if r["median_ms"] >= 30000]

        if tier_langs:
            print(f"  {tier:<20} {desc}")
            print(f"    Languages: {', '.join(tier_langs)}")

    print("\n" + "=" * 80)

    # Summary statistics
    if sorted_results:
        fastest = sorted_results[0]
        slowest = sorted_results[-1]

        print("SUMMARY:")
        print(f"  Fastest: {fastest['language']} ({fastest['median_ms']:.1f}ms)")
        print(f"  Slowest: {slowest['language']} ({slowest['median_ms']:.1f}ms)")

        if fastest["median_ms"] > 0:
            speedup = slowest["median_ms"] / fastest["median_ms"]
            print(f"  Range: {speedup:.1f}x difference between fastest and slowest")

        # Calculate average by mode
        modes: dict[str, list[float]] = {}
        for r in sorted_results:
            mode = r["mode"]
            if mode not in modes:
                modes[mode] = []
            modes[mode].append(r["median_ms"])

        print("\n  Average by execution mode:")
        for mode, times in sorted(modes.items()):
            avg = sum(times) / len(times)
            print(f"    {mode.capitalize():<15} {avg:,.1f}ms (n={len(times)})")

    print("=" * 80)


def main() -> None:
    """Main entry point."""
    results = load_results()
    print_chart(results)

    # Export summary for documentation
    print("\nMarkdown table for documentation:")
    print("\n| Rank | Language | Time (ms) | Mode | Relative Speed |")
    print("|------|----------|-----------|------|----------------|")

    sorted_results = sorted(results["results"], key=lambda x: x["median_ms"])
    if sorted_results:
        baseline = sorted_results[0]["median_ms"]
        for i, r in enumerate(sorted_results, 1):
            relative = r["median_ms"] / baseline if baseline > 0 else 0
            print(f"| {i} | {r['language']} | {r['median_ms']:.1f} | {r['mode']} | {relative:.1f}x |")


if __name__ == "__main__":
    main()
