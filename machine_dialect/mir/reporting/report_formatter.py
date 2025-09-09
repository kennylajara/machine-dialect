"""Report formatters for optimization reports.

This module provides different output formats for optimization reports
including text, HTML, and JSON.
"""

import json
from abc import ABC, abstractmethod
from typing import Any

from machine_dialect.mir.reporting.optimization_reporter import ModuleMetrics


class ReportFormatter(ABC):
    """Abstract base class for report formatters."""

    @abstractmethod
    def format(self, metrics: ModuleMetrics) -> str:
        """Format the metrics into a report.

        Args:
            metrics: Module metrics to format.

        Returns:
            Formatted report as a string.
        """
        pass


class TextReportFormatter(ReportFormatter):
    """Formats reports as plain text."""

    def __init__(self, detailed: bool = True) -> None:
        """Initialize text formatter.

        Args:
            detailed: Whether to include detailed per-pass statistics.
        """
        self.detailed = detailed

    def format(self, metrics: ModuleMetrics) -> str:
        """Format metrics as text report.

        Args:
            metrics: Module metrics.

        Returns:
            Text report.
        """
        lines = []
        summary = metrics.get_summary()

        # Header
        lines.append("=" * 70)
        lines.append(f"OPTIMIZATION REPORT - {summary['module_name']}")
        lines.append("=" * 70)
        lines.append("")

        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 30)
        lines.append(f"Optimization Level: {summary['optimization_level']}")
        lines.append(f"Total Passes Run: {summary['total_passes']}")
        lines.append(f"Total Time: {summary['total_time_ms']:.2f}ms")

        if summary["total_time_ms"] > 0:
            avg_time = summary["total_time_ms"] / summary["total_passes"]
            lines.append(f"Average Pass Time: {avg_time:.2f}ms")
        lines.append("")

        # Passes applied
        if summary["passes_applied"]:
            lines.append("PASSES APPLIED")
            lines.append("-" * 30)
            for i, pass_name in enumerate(summary["passes_applied"], 1):
                lines.append(f"{i:2}. {pass_name}")
            lines.append("")

        # Overall improvements
        if summary["improvements"]:
            lines.append("OVERALL IMPROVEMENTS")
            lines.append("-" * 30)
            for metric, improvement in sorted(summary["improvements"].items()):
                if improvement > 0:
                    lines.append(f"  {metric:30} {improvement:6.1f}% reduction")
                elif improvement < 0:
                    lines.append(f"  {metric:30} {-improvement:6.1f}% increase")
            lines.append("")

        # Total metrics
        if summary["total_metrics"]:
            lines.append("TOTAL OPTIMIZATIONS")
            lines.append("-" * 30)
            for metric, value in sorted(summary["total_metrics"].items()):
                if value > 0:
                    lines.append(f"  {metric:30} {value:6}")
            lines.append("")

        # Detailed pass statistics
        if self.detailed and metrics.pass_metrics:
            lines.append("=" * 70)
            lines.append("DETAILED PASS STATISTICS")
            lines.append("=" * 70)

            for i, pass_metrics in enumerate(metrics.pass_metrics, 1):
                lines.append("")
                lines.append(f"[{i}] {pass_metrics.pass_name}")
                lines.append("-" * 50)
                lines.append(f"    Phase: {pass_metrics.phase}")
                lines.append(f"    Time: {pass_metrics.time_ms:.2f}ms")

                if pass_metrics.metrics:
                    lines.append("    Changes:")
                    for key, value in sorted(pass_metrics.metrics.items()):
                        if value > 0:
                            lines.append(f"      - {key}: {value}")

                # Calculate improvements
                improvements = []
                for key in pass_metrics.before_stats:
                    if key in pass_metrics.after_stats:
                        before = pass_metrics.before_stats[key]
                        after = pass_metrics.after_stats[key]
                        if before != after:
                            improvement = pass_metrics.get_improvement(key)
                            improvements.append((key, before, after, improvement))

                if improvements:
                    lines.append("    Impact:")
                    for key, before, after, improvement in improvements:
                        if improvement > 0:
                            lines.append(f"      - {key}: {before} → {after} (-{improvement:.1f}%)")
                        else:
                            lines.append(f"      - {key}: {before} → {after} (+{-improvement:.1f}%)")

        # Function metrics
        if metrics.function_metrics:
            lines.append("")
            lines.append("=" * 70)
            lines.append("FUNCTION-LEVEL STATISTICS")
            lines.append("=" * 70)

            for func_name, func_metrics in metrics.function_metrics.items():
                lines.append("")
                lines.append(f"Function: {func_name}")
                lines.append("-" * 30)
                for key, value in sorted(func_metrics.items()):
                    lines.append(f"  {key:20} {value}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


class HTMLReportFormatter(ReportFormatter):
    """Formats reports as HTML."""

    def format(self, metrics: ModuleMetrics) -> str:
        """Format metrics as HTML report.

        Args:
            metrics: Module metrics.

        Returns:
            HTML report.
        """
        summary = metrics.get_summary()

        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Optimization Report</title>")
        html.append("<style>")
        html.append(
            """
            body { font-family: monospace; margin: 20px; }
            h1 { color: #333; }
            h2 { color: #666; border-bottom: 2px solid #ddd; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .improvement { color: green; font-weight: bold; }
            .regression { color: red; font-weight: bold; }
            .metric { background-color: #f9f9f9; }
            .pass-header { background-color: #e9e9e9; font-weight: bold; }
        """
        )
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        # Header
        html.append(f"<h1>Optimization Report - {summary['module_name']}</h1>")

        # Summary
        html.append("<h2>Summary</h2>")
        html.append("<table>")
        html.append(f"<tr><td>Optimization Level</td><td>{summary['optimization_level']}</td></tr>")
        html.append(f"<tr><td>Total Passes</td><td>{summary['total_passes']}</td></tr>")
        html.append(f"<tr><td>Total Time</td><td>{summary['total_time_ms']:.2f}ms</td></tr>")
        html.append("</table>")

        # Passes Applied
        if summary["passes_applied"]:
            html.append("<h2>Passes Applied</h2>")
            html.append("<ol>")
            for pass_name in summary["passes_applied"]:
                html.append(f"<li>{pass_name}</li>")
            html.append("</ol>")

        # Improvements
        if summary["improvements"]:
            html.append("<h2>Overall Improvements</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Improvement</th></tr>")
            for metric, improvement in sorted(summary["improvements"].items()):
                if improvement > 0:
                    html.append(f"<tr><td>{metric}</td><td class='improvement'>-{improvement:.1f}%</td></tr>")
                elif improvement < 0:
                    html.append(f"<tr><td>{metric}</td><td class='regression'>+{-improvement:.1f}%</td></tr>")
            html.append("</table>")

        # Detailed Pass Statistics
        if metrics.pass_metrics:
            html.append("<h2>Detailed Pass Statistics</h2>")
            html.append("<table>")
            html.append("<tr><th>Pass</th><th>Phase</th><th>Time (ms)</th><th>Metrics</th></tr>")

            for pass_metrics in metrics.pass_metrics:
                metrics_str = ", ".join(f"{k}: {v}" for k, v in pass_metrics.metrics.items() if v > 0)
                html.append("<tr>")
                html.append(f"<td>{pass_metrics.pass_name}</td>")
                html.append(f"<td>{pass_metrics.phase}</td>")
                html.append(f"<td>{pass_metrics.time_ms:.2f}</td>")
                html.append(f"<td>{metrics_str or 'N/A'}</td>")
                html.append("</tr>")

            html.append("</table>")

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)


class JSONReportFormatter(ReportFormatter):
    """Formats reports as JSON."""

    def format(self, metrics: ModuleMetrics) -> str:
        """Format metrics as JSON report.

        Args:
            metrics: Module metrics.

        Returns:
            JSON report.
        """
        data: dict[str, Any] = {
            "module_name": metrics.module_name,
            "optimization_level": metrics.optimization_level,
            "total_time_ms": metrics.total_time_ms,
            "summary": metrics.get_summary(),
            "passes": [],
            "functions": metrics.function_metrics,
        }

        # Add detailed pass information
        for pass_metrics in metrics.pass_metrics:
            pass_data: dict[str, Any] = {
                "name": pass_metrics.pass_name,
                "phase": pass_metrics.phase,
                "time_ms": pass_metrics.time_ms,
                "metrics": pass_metrics.metrics,
                "before_stats": pass_metrics.before_stats,
                "after_stats": pass_metrics.after_stats,
                "improvements": {},
            }

            # Calculate improvements
            for key in pass_metrics.before_stats:
                if key in pass_metrics.after_stats:
                    improvement = pass_metrics.get_improvement(key)
                    if improvement != 0:
                        pass_data["improvements"][key] = improvement

            data["passes"].append(pass_data)

        return json.dumps(data, indent=2)
