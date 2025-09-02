"""Automated regression detection for compilation performance.

This module provides statistical analysis and threshold-based detection
of performance regressions in the compilation pipeline.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from machine_dialect.ast import Program
from machine_dialect.mir.benchmarks.compilation_benchmark import BenchmarkResult, CompilationBenchmark


@dataclass
class RegressionThresholds:
    """Configurable thresholds for regression detection.

    Attributes:
        compilation_time_percent: Maximum allowed increase in compilation time.
        bytecode_size_percent: Maximum allowed increase in bytecode size.
        memory_usage_percent: Maximum allowed increase in memory usage.
        instruction_count_percent: Maximum allowed increase in instruction count.
        min_samples: Minimum samples needed for statistical significance.
        confidence_level: Confidence level for statistical tests (0-1).
    """

    compilation_time_percent: float = 5.0  # 5% threshold
    bytecode_size_percent: float = 10.0  # 10% threshold
    memory_usage_percent: float = 15.0  # 15% threshold
    instruction_count_percent: float = 10.0  # 10% threshold
    min_samples: int = 5
    confidence_level: float = 0.95


@dataclass
class RegressionResult:
    """Result of regression analysis.

    Attributes:
        metric_name: Name of the metric analyzed.
        baseline_value: Baseline metric value.
        current_value: Current metric value.
        percent_change: Percentage change from baseline.
        is_regression: Whether this is a regression.
        is_improvement: Whether this is an improvement.
        confidence: Statistical confidence in the result.
        details: Additional details about the analysis.
    """

    metric_name: str
    baseline_value: float
    current_value: float
    percent_change: float
    is_regression: bool
    is_improvement: bool
    confidence: float
    details: str = ""


@dataclass
class BaselineMetrics:
    """Baseline performance metrics for comparison.

    Attributes:
        timestamp: When baseline was established.
        samples: Number of samples in baseline.
        compilation_time_mean: Mean compilation time.
        compilation_time_stddev: Standard deviation of compilation time.
        bytecode_size_mean: Mean bytecode size.
        bytecode_size_stddev: Standard deviation of bytecode size.
        memory_peak_mean: Mean peak memory usage.
        memory_peak_stddev: Standard deviation of peak memory.
        instruction_count_mean: Mean instruction count.
        instruction_count_stddev: Standard deviation of instruction count.
    """

    timestamp: str
    samples: int
    compilation_time_mean: float
    compilation_time_stddev: float
    bytecode_size_mean: float
    bytecode_size_stddev: float
    memory_peak_mean: float
    memory_peak_stddev: float
    instruction_count_mean: float
    instruction_count_stddev: float

    @classmethod
    def from_benchmarks(cls, results: list[BenchmarkResult]) -> BaselineMetrics:
        """Create baseline from benchmark results.

        Args:
            results: List of benchmark results.

        Returns:
            Baseline metrics.
        """
        if not results:
            raise ValueError("No results to create baseline from")

        compilation_times = [r.compilation_time for r in results]
        bytecode_sizes = [r.bytecode_size for r in results]
        memory_peaks = [r.memory_peak for r in results]
        instruction_counts = [r.instruction_count for r in results]

        return cls(
            timestamp=datetime.now().isoformat(),
            samples=len(results),
            compilation_time_mean=statistics.mean(compilation_times),
            compilation_time_stddev=statistics.stdev(compilation_times) if len(compilation_times) > 1 else 0.0,
            bytecode_size_mean=statistics.mean(bytecode_sizes),
            bytecode_size_stddev=statistics.stdev(bytecode_sizes) if len(bytecode_sizes) > 1 else 0.0,
            memory_peak_mean=statistics.mean(memory_peaks),
            memory_peak_stddev=statistics.stdev(memory_peaks) if len(memory_peaks) > 1 else 0.0,
            instruction_count_mean=statistics.mean(instruction_counts),
            instruction_count_stddev=statistics.stdev(instruction_counts) if len(instruction_counts) > 1 else 0.0,
        )


class RegressionDetector:
    """Detects performance regressions in compilation pipeline."""

    def __init__(self, baseline_path: Path | None = None, thresholds: RegressionThresholds | None = None) -> None:
        """Initialize the regression detector.

        Args:
            baseline_path: Path to baseline metrics file.
            thresholds: Regression detection thresholds.
        """
        self.baseline_path = baseline_path or Path("baseline.json")
        self.thresholds = thresholds or RegressionThresholds()
        self.baseline: BaselineMetrics | None = None
        self.current_results: list[BenchmarkResult] = []

        # Load baseline if it exists
        if self.baseline_path.exists():
            self.load_baseline()

    def load_baseline(self) -> None:
        """Load baseline metrics from file."""
        with open(self.baseline_path) as f:
            data = json.load(f)
            self.baseline = BaselineMetrics(**data)

    def save_baseline(self, baseline: BaselineMetrics) -> None:
        """Save baseline metrics to file.

        Args:
            baseline: Baseline metrics to save.
        """
        with open(self.baseline_path, "w") as f:
            json.dump(asdict(baseline), f, indent=2)
        self.baseline = baseline

    def establish_baseline(self, programs: list[Program], names: list[str] | None = None) -> BaselineMetrics:
        """Establish a new baseline from programs.

        Args:
            programs: Programs to benchmark.
            names: Optional names for programs.

        Returns:
            New baseline metrics.
        """
        if names is None:
            names = [f"baseline_{i}" for i in range(len(programs))]

        benchmark = CompilationBenchmark()
        results = []

        for program, name in zip(programs, names, strict=False):
            result = benchmark.benchmark_compilation(program, name)
            if result:
                results.append(result)

        baseline = BaselineMetrics.from_benchmarks(results)
        self.save_baseline(baseline)
        return baseline

    def check_regression(self, result: BenchmarkResult) -> list[RegressionResult]:
        """Check if a benchmark result shows regression.

        Args:
            result: Benchmark result to check.

        Returns:
            List of regression results for each metric.
        """
        if not self.baseline:
            raise ValueError("No baseline established for comparison")

        regressions = []

        # Check compilation time
        regressions.append(
            self._check_metric(
                "compilation_time",
                self.baseline.compilation_time_mean,
                self.baseline.compilation_time_stddev,
                result.compilation_time,
                self.thresholds.compilation_time_percent,
            )
        )

        # Check bytecode size
        regressions.append(
            self._check_metric(
                "bytecode_size",
                self.baseline.bytecode_size_mean,
                self.baseline.bytecode_size_stddev,
                result.bytecode_size,
                self.thresholds.bytecode_size_percent,
            )
        )

        # Check memory usage
        regressions.append(
            self._check_metric(
                "memory_peak",
                self.baseline.memory_peak_mean,
                self.baseline.memory_peak_stddev,
                result.memory_peak,
                self.thresholds.memory_usage_percent,
            )
        )

        # Check instruction count
        regressions.append(
            self._check_metric(
                "instruction_count",
                self.baseline.instruction_count_mean,
                self.baseline.instruction_count_stddev,
                result.instruction_count,
                self.thresholds.instruction_count_percent,
            )
        )

        return regressions

    def _check_metric(
        self, name: str, baseline_mean: float, baseline_stddev: float, current_value: float, threshold_percent: float
    ) -> RegressionResult:
        """Check a single metric for regression.

        Args:
            name: Metric name.
            baseline_mean: Baseline mean value.
            baseline_stddev: Baseline standard deviation.
            current_value: Current metric value.
            threshold_percent: Threshold percentage.

        Returns:
            Regression result.
        """
        if baseline_mean == 0:
            percent_change = 0.0
        else:
            percent_change = ((current_value - baseline_mean) / baseline_mean) * 100

        # Calculate z-score for statistical significance
        if baseline_stddev > 0:
            z_score = abs((current_value - baseline_mean) / baseline_stddev)
            # Convert z-score to confidence (simplified)
            confidence = min(1.0, z_score / 3.0)  # 3 sigma = ~99.7% confidence
        else:
            confidence = 1.0 if percent_change != 0 else 0.0

        is_regression = percent_change > threshold_percent
        is_improvement = percent_change < -threshold_percent

        details = ""
        if is_regression:
            details = f"Regression detected: {percent_change:.1f}% increase exceeds {threshold_percent}% threshold"
        elif is_improvement:
            details = f"Improvement detected: {abs(percent_change):.1f}% decrease"
        else:
            details = f"Within acceptable range: {percent_change:.1f}% change"

        return RegressionResult(
            metric_name=name,
            baseline_value=baseline_mean,
            current_value=current_value,
            percent_change=percent_change,
            is_regression=is_regression,
            is_improvement=is_improvement,
            confidence=confidence,
            details=details,
        )

    def analyze_trends(self, results: list[BenchmarkResult], window_size: int = 10) -> dict[str, Any]:
        """Analyze performance trends over multiple runs.

        Args:
            results: List of benchmark results.
            window_size: Size of rolling window for trend analysis.

        Returns:
            Dictionary of trend analysis results.
        """
        if len(results) < 2:
            return {"error": "Not enough data for trend analysis"}

        trends = {}

        # Compilation time trend
        compilation_times = [r.compilation_time for r in results]
        trends["compilation_time"] = self._calculate_trend(compilation_times, window_size)

        # Bytecode size trend
        bytecode_sizes = [float(r.bytecode_size) for r in results]
        trends["bytecode_size"] = self._calculate_trend(bytecode_sizes, window_size)

        # Memory usage trend
        memory_peaks = [float(r.memory_peak) for r in results]
        trends["memory_peak"] = self._calculate_trend(memory_peaks, window_size)

        # Instruction count trend
        instruction_counts = [float(r.instruction_count) for r in results]
        trends["instruction_count"] = self._calculate_trend(instruction_counts, window_size)

        return trends

    def _calculate_trend(self, values: list[float], window_size: int) -> dict[str, Any]:
        """Calculate trend statistics for a metric.

        Args:
            values: List of metric values.
            window_size: Size of rolling window.

        Returns:
            Trend statistics.
        """
        if len(values) < 2:
            return {"error": "Not enough data"}

        # Calculate rolling average
        rolling_avg = []
        for i in range(len(values) - window_size + 1):
            window = values[i : i + window_size]
            rolling_avg.append(statistics.mean(window))

        # Calculate trend direction (simplified linear regression)
        if len(rolling_avg) >= 2:
            first_half = statistics.mean(rolling_avg[: len(rolling_avg) // 2])
            second_half = statistics.mean(rolling_avg[len(rolling_avg) // 2 :])
            trend_direction = "increasing" if second_half > first_half else "decreasing"
            trend_strength = abs((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
        else:
            trend_direction = "stable"
            trend_strength = 0

        return {
            "current": values[-1],
            "mean": statistics.mean(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "rolling_average": rolling_avg[-1] if rolling_avg else values[-1],
        }

    def generate_report(self, results: list[RegressionResult]) -> str:
        """Generate a human-readable regression report.

        Args:
            results: List of regression results.

        Returns:
            Formatted report string.
        """
        report = "Performance Regression Analysis Report\n"
        report += "=" * 50 + "\n\n"

        has_regression = any(r.is_regression for r in results)
        has_improvement = any(r.is_improvement for r in results)

        if has_regression:
            report += "⚠️  REGRESSIONS DETECTED\n\n"

        if has_improvement:
            report += "✅ IMPROVEMENTS DETECTED\n\n"

        for result in results:
            status = "❌" if result.is_regression else ("✅" if result.is_improvement else "✓")
            report += f"{status} {result.metric_name}:\n"
            report += f"  Baseline: {result.baseline_value:.4f}\n"
            report += f"  Current:  {result.current_value:.4f}\n"
            report += f"  Change:   {result.percent_change:+.1f}%\n"
            report += f"  {result.details}\n\n"

        if not has_regression and not has_improvement:
            report += "All metrics within acceptable thresholds.\n"

        return report
