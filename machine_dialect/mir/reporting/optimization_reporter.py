"""Optimization reporter for collecting and aggregating pass statistics.

This module provides infrastructure for collecting optimization statistics
from various passes and generating comprehensive reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricType(Enum):
    """Types of metrics collected."""

    COUNT = "count"  # Simple count (e.g., instructions removed)
    PERCENTAGE = "percentage"  # Percentage value
    SIZE = "size"  # Size in bytes
    TIME = "time"  # Time in milliseconds
    RATIO = "ratio"  # Ratio between two values


@dataclass
class PassMetrics:
    """Metrics collected from a single optimization pass.

    Attributes:
        pass_name: Name of the optimization pass.
        phase: Optimization phase (early, middle, late).
        metrics: Dictionary of metric name to value.
        before_stats: Statistics before the pass.
        after_stats: Statistics after the pass.
        time_ms: Time taken to run the pass in milliseconds.
    """

    pass_name: str
    phase: str = "main"
    metrics: dict[str, int] = field(default_factory=dict)
    before_stats: dict[str, int] = field(default_factory=dict)
    after_stats: dict[str, int] = field(default_factory=dict)
    time_ms: float = 0.0

    def get_improvement(self, metric: str) -> float:
        """Calculate improvement percentage for a metric.

        Args:
            metric: Metric name.

        Returns:
            Improvement percentage (positive means reduction).
        """
        before = self.before_stats.get(metric, 0)
        after = self.after_stats.get(metric, 0)
        if before == 0:
            return 0.0
        return ((before - after) / before) * 100


@dataclass
class ModuleMetrics:
    """Metrics for an entire module.

    Attributes:
        module_name: Name of the module.
        function_metrics: Metrics for each function.
        pass_metrics: Metrics from each pass.
        total_time_ms: Total optimization time.
        optimization_level: Optimization level used.
    """

    module_name: str
    function_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    pass_metrics: list[PassMetrics] = field(default_factory=list)
    total_time_ms: float = 0.0
    optimization_level: int = 0

    def add_pass_metrics(self, metrics: PassMetrics) -> None:
        """Add metrics from a pass.

        Args:
            metrics: Pass metrics to add.
        """
        self.pass_metrics.append(metrics)
        self.total_time_ms += metrics.time_ms

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dictionary of summary statistics.
        """
        summary = {
            "module_name": self.module_name,
            "optimization_level": self.optimization_level,
            "total_passes": len(self.pass_metrics),
            "total_time_ms": self.total_time_ms,
            "passes_applied": [m.pass_name for m in self.pass_metrics],
        }

        # Aggregate improvements
        total_improvements = {}
        for metrics in self.pass_metrics:
            for key in metrics.before_stats:
                if key in metrics.after_stats:
                    improvement = metrics.get_improvement(key)
                    if key not in total_improvements:
                        total_improvements[key] = 0.0
                    total_improvements[key] += improvement

        summary["improvements"] = total_improvements

        # Calculate total metrics
        total_metrics = {}
        for metrics in self.pass_metrics:
            for key, value in metrics.metrics.items():
                if key not in total_metrics:
                    total_metrics[key] = 0
                total_metrics[key] += value

        summary["total_metrics"] = total_metrics

        return summary


class OptimizationReporter:
    """Collects and reports optimization statistics.

    This class aggregates statistics from multiple optimization passes
    and generates comprehensive reports about the optimization process.
    """

    def __init__(self, module_name: str = "unknown") -> None:
        """Initialize the reporter.

        Args:
            module_name: Name of the module being optimized.
        """
        self.module_metrics = ModuleMetrics(module_name=module_name)
        self.current_pass: PassMetrics | None = None

    def start_pass(
        self,
        pass_name: str,
        phase: str = "main",
        before_stats: dict[str, int] | None = None,
    ) -> None:
        """Start tracking a new pass.

        Args:
            pass_name: Name of the pass.
            phase: Optimization phase.
            before_stats: Statistics before the pass.
        """
        self.current_pass = PassMetrics(
            pass_name=pass_name,
            phase=phase,
            before_stats=before_stats or {},
        )

    def end_pass(
        self,
        metrics: dict[str, int] | None = None,
        after_stats: dict[str, int] | None = None,
        time_ms: float = 0.0,
    ) -> None:
        """End tracking the current pass.

        Args:
            metrics: Pass-specific metrics.
            after_stats: Statistics after the pass.
            time_ms: Time taken by the pass.
        """
        if self.current_pass:
            self.current_pass.metrics = metrics or {}
            self.current_pass.after_stats = after_stats or {}
            self.current_pass.time_ms = time_ms
            self.module_metrics.add_pass_metrics(self.current_pass)
            self.current_pass = None

    def add_function_metrics(self, func_name: str, metrics: dict[str, Any]) -> None:
        """Add metrics for a specific function.

        Args:
            func_name: Function name.
            metrics: Function metrics.
        """
        self.module_metrics.function_metrics[func_name] = metrics

    def add_custom_stats(self, pass_name: str, stats: dict[str, int]) -> None:
        """Add custom statistics for a pass.

        Args:
            pass_name: Name of the pass.
            stats: Statistics to add.
        """
        # Create a pass metrics entry for custom stats
        metrics = PassMetrics(pass_name=pass_name, phase="bytecode", metrics=stats)
        self.module_metrics.add_pass_metrics(metrics)

    def set_optimization_level(self, level: int) -> None:
        """Set the optimization level.

        Args:
            level: Optimization level (0-3).
        """
        self.module_metrics.optimization_level = level

    def get_report_data(self) -> ModuleMetrics:
        """Get the collected metrics.

        Returns:
            Module metrics.
        """
        return self.module_metrics

    def generate_summary(self) -> str:
        """Generate a text summary of optimizations.

        Returns:
            Text summary.
        """
        summary = self.module_metrics.get_summary()
        lines = []

        lines.append(f"Module: {summary['module_name']}")
        lines.append(f"Optimization Level: {summary['optimization_level']}")
        lines.append(f"Total Passes: {summary['total_passes']}")
        lines.append(f"Total Time: {summary['total_time_ms']:.2f}ms")
        lines.append("")

        if summary["passes_applied"]:
            lines.append("Passes Applied:")
            for pass_name in summary["passes_applied"]:
                lines.append(f"  - {pass_name}")
            lines.append("")

        if summary["improvements"]:
            lines.append("Improvements:")
            for metric, improvement in summary["improvements"].items():
                if improvement > 0:
                    lines.append(f"  {metric}: {improvement:.1f}% reduction")
            lines.append("")

        if summary["total_metrics"]:
            lines.append("Total Changes:")
            for metric, value in summary["total_metrics"].items():
                if value > 0:
                    lines.append(f"  {metric}: {value}")

        return "\n".join(lines)

    def generate_detailed_report(self) -> str:
        """Generate a detailed report with per-pass statistics.

        Returns:
            Detailed text report.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("OPTIMIZATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(self.generate_summary())
        lines.append("")
        lines.append("=" * 60)
        lines.append("DETAILED PASS STATISTICS")
        lines.append("=" * 60)

        # Per-pass details
        for metrics in self.module_metrics.pass_metrics:
            lines.append("")
            lines.append(f"Pass: {metrics.pass_name}")
            lines.append(f"Phase: {metrics.phase}")
            lines.append(f"Time: {metrics.time_ms:.2f}ms")

            if metrics.metrics:
                lines.append("Metrics:")
                for key, value in metrics.metrics.items():
                    if value > 0:
                        lines.append(f"  {key}: {value}")

            # Show improvements
            improvements = []
            for key in metrics.before_stats:
                if key in metrics.after_stats:
                    improvement = metrics.get_improvement(key)
                    if improvement > 0:
                        improvements.append(
                            f"  {key}: {metrics.before_stats[key]} → "
                            f"{metrics.after_stats[key]} "
                            f"({improvement:.1f}% reduction)"
                        )

            if improvements:
                lines.append("Improvements:")
                lines.extend(improvements)

            lines.append("-" * 40)

        # Function-specific metrics if available
        if self.module_metrics.function_metrics:
            lines.append("")
            lines.append("=" * 60)
            lines.append("FUNCTION METRICS")
            lines.append("=" * 60)

            for func_name, func_metrics in self.module_metrics.function_metrics.items():
                lines.append("")
                lines.append(f"Function: {func_name}")
                for key, value in func_metrics.items():
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)
