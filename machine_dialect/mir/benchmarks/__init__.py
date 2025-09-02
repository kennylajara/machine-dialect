"""MIR compilation benchmarking tools."""

from machine_dialect.mir.benchmarks.compilation_benchmark import (
    BenchmarkResult,
    CompilationBenchmark,
    run_standard_benchmarks,
)
from machine_dialect.mir.benchmarks.regression_detector import (
    BaselineMetrics,
    RegressionDetector,
    RegressionResult,
    RegressionThresholds,
)

__all__ = [
    "BaselineMetrics",
    "BenchmarkResult",
    "CompilationBenchmark",
    "RegressionDetector",
    "RegressionResult",
    "RegressionThresholds",
    "run_standard_benchmarks",
]
