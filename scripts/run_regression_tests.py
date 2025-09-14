#!/usr/bin/env python3
"""Command-line tool for running regression tests on MIR compilation pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Temporarily disabled while compilation_benchmark module is disabled
# from machine_dialect.mir.benchmarks.compilation_benchmark import CompilationBenchmark
# from machine_dialect.mir.benchmarks.comprehensive_regression import (
#     ComprehensiveRegressionDetector,
#     create_regression_suite,
# )
from machine_dialect.mir.benchmarks.regression_detector import RegressionThresholds


def main() -> int:
    """Main entry point for regression testing."""
    parser = argparse.ArgumentParser(description="Run regression tests on MIR compilation pipeline")

    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=Path(".regression_baselines/baseline.json"),
        help="Path to baseline metrics file",
    )

    parser.add_argument(
        "--outputs-path",
        type=Path,
        default=Path(".regression_baselines/expected_outputs.json"),
        help="Path to expected outputs file",
    )

    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current results",
    )

    parser.add_argument(
        "--compilation-threshold",
        type=float,
        default=5.0,
        help="Compilation time regression threshold (percent)",
    )

    parser.add_argument(
        "--bytecode-threshold",
        type=float,
        default=10.0,
        help="Bytecode size regression threshold (percent)",
    )

    parser.add_argument(
        "--memory-threshold",
        type=float,
        default=15.0,
        help="Memory usage regression threshold (percent)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    parser.add_argument(
        "--test",
        type=str,
        help="Run only specific test",
    )

    args = parser.parse_args()

    # Create thresholds (currently unused due to disabled modules)
    _ = RegressionThresholds(
        compilation_time_percent=args.compilation_threshold,
        bytecode_size_percent=args.bytecode_threshold,
        memory_usage_percent=args.memory_threshold,
    )

    # Temporarily disabled while compilation_benchmark module is disabled
    print("Error: Regression testing is temporarily disabled")
    print("The compilation_benchmark and comprehensive_regression modules are currently disabled.")
    return 1

    # # Create detector
    # detector = ComprehensiveRegressionDetector(
    #     baseline_path=args.baseline_path,
    #     thresholds=thresholds,
    #     expected_outputs_path=args.outputs_path,
    # )
    #
    # # Get test suite
    # suite = create_regression_suite()
    #
    # # Filter if specific test requested
    # if args.test:
    #     if args.test not in suite:
    #         print(f"Error: Test '{args.test}' not found in suite")
    #         print(f"Available tests: {', '.join(suite.keys())}")
    #         return 1
    #     suite = {args.test: suite[args.test]}
    #
    # # Create benchmark
    # benchmark = CompilationBenchmark()

    # # Update baseline if requested
    # if args.update_baseline:
    #     print("Updating baseline...")
    #     programs = list(suite.values())
    #     names = list(suite.keys())
    #     baseline = detector.establish_baseline(programs, names)
    #     print(f"Baseline updated with {baseline.samples} samples")
    #     return 0
    #
    # # Run regression tests
    # print(f"Running {len(suite)} regression tests...")
    # print("-" * 60)
    #
    # results = []
    # has_any_regression = False
    #
    # for name, program in suite.items():
    #     if args.verbose:
    #         print(f"Testing {name}...")
    #
    #     # Benchmark
    #     bench_result = benchmark.benchmark_compilation(program, name)
    #
    #     # Check for regression
    #     result = detector.comprehensive_check(program, name, bench_result)
    #     results.append(result)

    #     if result.has_regression:
    #         has_any_regression = True
    #         print(f"❌ {name}: REGRESSION DETECTED")
    #         if result.has_correctness_issue:
    #             print(f"   Correctness: {result.correctness_result.details}")
    #         if result.has_performance_issue:
    #             for perf in result.performance_results:
    #                 if perf.is_regression:
    #                     print(f"   {perf.metric_name}: {perf.percent_change:+.1f}%")
    #     else:
    #         if args.verbose:
    #             print(f"✅ {name}: PASS")
    #             # Show improvements
    #             for perf in result.performance_results:
    #                 if perf.is_improvement:
    #                     print(f"   {perf.metric_name}: {abs(perf.percent_change):.1f}% faster")
    #
    # # Generate report
    # print("\n" + "=" * 60)
    # report = detector.generate_comprehensive_report(results)
    # print(report)
    #
    # # Save report to file for CI
    # with open("regression_report.txt", "w") as f:
    #     f.write(report)
    #
    # # Return exit code
    # return 1 if has_any_regression else 0


if __name__ == "__main__":
    sys.exit(main())
