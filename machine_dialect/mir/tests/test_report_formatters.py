"""Tests for report formatters."""

import json

import pytest

from machine_dialect.mir.reporting.optimization_reporter import (
    ModuleMetrics,
    PassMetrics,
)
from machine_dialect.mir.reporting.report_formatter import (
    HTMLReportFormatter,
    JSONReportFormatter,
    TextReportFormatter,
)


def create_test_metrics() -> ModuleMetrics:
    """Create test module metrics."""
    metrics = ModuleMetrics(
        module_name="test_module",
        optimization_level=2,
    )

    # Add pass metrics
    pass1 = PassMetrics(
        pass_name="constant-propagation",
        phase="early",
        metrics={"constants_propagated": 15, "expressions_folded": 5},
        before_stats={"instructions": 100, "blocks": 10},
        after_stats={"instructions": 85, "blocks": 8},
        time_ms=3.5,
    )

    pass2 = PassMetrics(
        pass_name="dead-code-elimination",
        phase="main",
        metrics={"dead_removed": 10, "blocks_removed": 2},
        before_stats={"instructions": 85, "blocks": 8},
        after_stats={"instructions": 75, "blocks": 6},
        time_ms=2.0,
    )

    metrics.add_pass_metrics(pass1)
    metrics.add_pass_metrics(pass2)

    # Add function metrics
    metrics.function_metrics["main"] = {
        "instructions": 50,
        "blocks": 4,
        "loops": 1,
    }

    metrics.function_metrics["helper"] = {
        "instructions": 25,
        "blocks": 2,
        "loops": 0,
    }

    return metrics


class TestTextReportFormatter:
    """Test text report formatter."""

    def test_basic_formatting(self) -> None:
        """Test basic text formatting."""
        formatter = TextReportFormatter(detailed=False)
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "OPTIMIZATION REPORT - test_module" in report
        assert "Optimization Level: 2" in report
        assert "Total Passes Run: 2" in report
        assert "Total Time: 5.50ms" in report
        assert "constant-propagation" in report
        assert "dead-code-elimination" in report

    def test_detailed_formatting(self) -> None:
        """Test detailed text formatting."""
        formatter = TextReportFormatter(detailed=True)
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "DETAILED PASS STATISTICS" in report
        assert "[1] constant-propagation" in report
        assert "[2] dead-code-elimination" in report
        assert "Phase: early" in report
        assert "Phase: main" in report
        assert "Time: 3.50ms" in report
        assert "Time: 2.00ms" in report

    def test_improvements_section(self) -> None:
        """Test that improvements are calculated and shown."""
        formatter = TextReportFormatter(detailed=True)
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "OVERALL IMPROVEMENTS" in report
        # Instructions reduced from 100 to 75 (25% reduction)
        assert "instructions" in report
        assert "reduction" in report

    def test_total_optimizations(self) -> None:
        """Test total optimizations section."""
        formatter = TextReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "TOTAL OPTIMIZATIONS" in report
        assert "constants_propagated" in report
        assert "15" in report
        assert "dead_removed" in report
        assert "10" in report

    def test_function_metrics_section(self) -> None:
        """Test function-level statistics."""
        formatter = TextReportFormatter(detailed=True)
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "FUNCTION-LEVEL STATISTICS" in report
        assert "Function: main" in report
        assert "Function: helper" in report
        assert "instructions" in report
        assert "blocks" in report
        assert "loops" in report

    def test_empty_metrics(self) -> None:
        """Test formatting empty metrics."""
        formatter = TextReportFormatter()
        metrics = ModuleMetrics("empty", optimization_level=0)

        report = formatter.format(metrics)

        assert "OPTIMIZATION REPORT - empty" in report
        assert "Total Passes Run: 0" in report
        assert "Total Time: 0.00ms" in report

    def test_passes_applied_list(self) -> None:
        """Test passes applied list formatting."""
        formatter = TextReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "PASSES APPLIED" in report
        assert "1. constant-propagation" in report
        assert "2. dead-code-elimination" in report

    def test_average_pass_time(self) -> None:
        """Test average pass time calculation."""
        formatter = TextReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "Average Pass Time:" in report
        # (3.5 + 2.0) / 2 = 2.75ms
        assert "2.75ms" in report


class TestHTMLReportFormatter:
    """Test HTML report formatter."""

    def test_basic_html_structure(self) -> None:
        """Test basic HTML structure."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<!DOCTYPE html>" in report
        assert "<html>" in report
        assert "</html>" in report
        assert "<head>" in report
        assert "<body>" in report
        assert "<title>Optimization Report</title>" in report

    def test_html_content(self) -> None:
        """Test HTML content."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<h1>Optimization Report - test_module</h1>" in report
        assert "<h2>Summary</h2>" in report
        assert "Optimization Level" in report
        assert "Total Passes" in report
        assert "constant-propagation" in report
        assert "dead-code-elimination" in report

    def test_html_tables(self) -> None:
        """Test HTML tables."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<table>" in report
        assert "<tr>" in report
        assert "<td>" in report
        assert "<th>" in report

    def test_html_styling(self) -> None:
        """Test HTML styling."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<style>" in report
        assert "font-family: monospace" in report
        assert ".improvement" in report
        assert ".regression" in report

    def test_html_improvements(self) -> None:
        """Test HTML improvements section."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<h2>Overall Improvements</h2>" in report
        assert "class='improvement'" in report

    def test_html_detailed_stats(self) -> None:
        """Test HTML detailed statistics."""
        formatter = HTMLReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        assert "<h2>Detailed Pass Statistics</h2>" in report
        assert "constant-propagation" in report
        assert "3.50" in report  # Time

    def test_empty_html_report(self) -> None:
        """Test empty HTML report."""
        formatter = HTMLReportFormatter()
        metrics = ModuleMetrics("empty")

        report = formatter.format(metrics)

        assert "<!DOCTYPE html>" in report
        assert "Optimization Report - empty" in report


class TestJSONReportFormatter:
    """Test JSON report formatter."""

    def test_json_structure(self) -> None:
        """Test JSON structure."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        assert data["module_name"] == "test_module"
        assert data["optimization_level"] == 2
        assert data["total_time_ms"] == 5.5
        assert "summary" in data
        assert "passes" in data
        assert "functions" in data

    def test_json_passes(self) -> None:
        """Test JSON passes data."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        assert len(data["passes"]) == 2

        pass1 = data["passes"][0]
        assert pass1["name"] == "constant-propagation"
        assert pass1["phase"] == "early"
        assert pass1["time_ms"] == 3.5
        assert pass1["metrics"]["constants_propagated"] == 15

    def test_json_improvements(self) -> None:
        """Test JSON improvements calculation."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        pass1 = data["passes"][0]
        assert "improvements" in pass1
        assert "instructions" in pass1["improvements"]
        # 100 -> 85 is 15% improvement
        assert pass1["improvements"]["instructions"] == 15.0

    def test_json_function_metrics(self) -> None:
        """Test JSON function metrics."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        assert "main" in data["functions"]
        assert data["functions"]["main"]["instructions"] == 50
        assert data["functions"]["main"]["loops"] == 1

        assert "helper" in data["functions"]
        assert data["functions"]["helper"]["instructions"] == 25

    def test_json_summary(self) -> None:
        """Test JSON summary data."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        summary = data["summary"]
        assert summary["module_name"] == "test_module"
        assert summary["total_passes"] == 2
        assert "passes_applied" in summary
        assert len(summary["passes_applied"]) == 2

    def test_json_formatting(self) -> None:
        """Test JSON is properly formatted."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)

        # Should be indented
        assert "\n  " in report

        # Should be valid JSON
        try:
            json.loads(report)
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON generated")

    def test_empty_json_report(self) -> None:
        """Test empty JSON report."""
        formatter = JSONReportFormatter()
        metrics = ModuleMetrics("empty")

        report = formatter.format(metrics)
        data = json.loads(report)

        assert data["module_name"] == "empty"
        assert len(data["passes"]) == 0
        assert len(data["functions"]) == 0

    def test_json_before_after_stats(self) -> None:
        """Test JSON before/after statistics."""
        formatter = JSONReportFormatter()
        metrics = create_test_metrics()

        report = formatter.format(metrics)
        data = json.loads(report)

        pass1 = data["passes"][0]
        assert pass1["before_stats"]["instructions"] == 100
        assert pass1["after_stats"]["instructions"] == 85
        assert pass1["before_stats"]["blocks"] == 10
        assert pass1["after_stats"]["blocks"] == 8
