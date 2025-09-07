"""Tests for optimization reporter."""

from machine_dialect.mir.reporting.optimization_reporter import (
    ModuleMetrics,
    OptimizationReporter,
    PassMetrics,
)


class TestPassMetrics:
    """Test PassMetrics functionality."""

    def test_pass_metrics_creation(self) -> None:
        """Test creating pass metrics."""
        metrics = PassMetrics(
            pass_name="constant-propagation",
            phase="early",
            metrics={"constants_propagated": 10},
            before_stats={"instructions": 100},
            after_stats={"instructions": 90},
            time_ms=5.5,
        )

        assert metrics.pass_name == "constant-propagation"
        assert metrics.phase == "early"
        assert metrics.metrics["constants_propagated"] == 10
        assert metrics.time_ms == 5.5

    def test_get_improvement(self) -> None:
        """Test calculating improvement percentage."""
        metrics = PassMetrics(
            pass_name="dce",
            before_stats={"instructions": 100, "blocks": 10},
            after_stats={"instructions": 80, "blocks": 8},
        )

        # 20% reduction in instructions
        assert metrics.get_improvement("instructions") == 20.0

        # 20% reduction in blocks
        assert metrics.get_improvement("blocks") == 20.0

        # No change for missing metric
        assert metrics.get_improvement("missing") == 0.0

    def test_get_improvement_zero_before(self) -> None:
        """Test improvement calculation with zero before value."""
        metrics = PassMetrics(
            pass_name="test",
            before_stats={"count": 0},
            after_stats={"count": 10},
        )

        assert metrics.get_improvement("count") == 0.0


class TestModuleMetrics:
    """Test ModuleMetrics functionality."""

    def test_module_metrics_creation(self) -> None:
        """Test creating module metrics."""
        metrics = ModuleMetrics(
            module_name="test_module",
            optimization_level=2,
        )

        assert metrics.module_name == "test_module"
        assert metrics.optimization_level == 2
        assert metrics.total_time_ms == 0.0
        assert len(metrics.pass_metrics) == 0

    def test_add_pass_metrics(self) -> None:
        """Test adding pass metrics."""
        module_metrics = ModuleMetrics("test")

        pass1 = PassMetrics("pass1", time_ms=10.0)
        pass2 = PassMetrics("pass2", time_ms=15.0)

        module_metrics.add_pass_metrics(pass1)
        module_metrics.add_pass_metrics(pass2)

        assert len(module_metrics.pass_metrics) == 2
        assert module_metrics.total_time_ms == 25.0

    def test_get_summary(self) -> None:
        """Test getting module summary."""
        module_metrics = ModuleMetrics(
            module_name="test",
            optimization_level=2,
        )

        # Add some pass metrics
        pass1 = PassMetrics(
            pass_name="constant-propagation",
            metrics={"constants_propagated": 5},
            before_stats={"instructions": 100},
            after_stats={"instructions": 95},
            time_ms=2.0,
        )

        pass2 = PassMetrics(
            pass_name="dce",
            metrics={"dead_removed": 10},
            before_stats={"instructions": 95},
            after_stats={"instructions": 85},
            time_ms=3.0,
        )

        module_metrics.add_pass_metrics(pass1)
        module_metrics.add_pass_metrics(pass2)

        summary = module_metrics.get_summary()

        assert summary["module_name"] == "test"
        assert summary["optimization_level"] == 2
        assert summary["total_passes"] == 2
        assert summary["total_time_ms"] == 5.0
        assert "constant-propagation" in summary["passes_applied"]
        assert "dce" in summary["passes_applied"]

        # Check aggregated metrics
        assert summary["total_metrics"]["constants_propagated"] == 5
        assert summary["total_metrics"]["dead_removed"] == 10

        # Check improvements
        assert "instructions" in summary["improvements"]


class TestOptimizationReporter:
    """Test OptimizationReporter functionality."""

    def test_reporter_creation(self) -> None:
        """Test creating optimization reporter."""
        reporter = OptimizationReporter("my_module")

        assert reporter.module_metrics.module_name == "my_module"
        assert reporter.current_pass is None

    def test_pass_tracking(self) -> None:
        """Test tracking optimization passes."""
        reporter = OptimizationReporter("test")

        # Start a pass
        reporter.start_pass(
            "constant-propagation",
            phase="early",
            before_stats={"instructions": 100},
        )

        assert reporter.current_pass is not None
        assert reporter.current_pass.pass_name == "constant-propagation"

        # End the pass
        reporter.end_pass(
            metrics={"constants_propagated": 5},
            after_stats={"instructions": 95},
            time_ms=2.5,
        )

        assert reporter.current_pass is None
        assert len(reporter.module_metrics.pass_metrics) == 1

        pass_metrics = reporter.module_metrics.pass_metrics[0]
        assert pass_metrics.pass_name == "constant-propagation"
        assert pass_metrics.metrics["constants_propagated"] == 5
        assert pass_metrics.time_ms == 2.5

    def test_multiple_passes(self) -> None:
        """Test tracking multiple optimization passes."""
        reporter = OptimizationReporter("test")

        # First pass
        reporter.start_pass("pass1", before_stats={"size": 1000})
        reporter.end_pass(
            metrics={"changes": 10},
            after_stats={"size": 900},
            time_ms=5.0,
        )

        # Second pass
        reporter.start_pass("pass2", before_stats={"size": 900})
        reporter.end_pass(
            metrics={"changes": 5},
            after_stats={"size": 850},
            time_ms=3.0,
        )

        assert len(reporter.module_metrics.pass_metrics) == 2
        assert reporter.module_metrics.total_time_ms == 8.0

    def test_function_metrics(self) -> None:
        """Test adding function-specific metrics."""
        reporter = OptimizationReporter("test")

        reporter.add_function_metrics(
            "main",
            {
                "instructions": 50,
                "blocks": 5,
                "loops": 2,
            },
        )

        reporter.add_function_metrics(
            "helper",
            {
                "instructions": 20,
                "blocks": 2,
                "loops": 0,
            },
        )

        assert len(reporter.module_metrics.function_metrics) == 2
        assert reporter.module_metrics.function_metrics["main"]["loops"] == 2
        assert reporter.module_metrics.function_metrics["helper"]["instructions"] == 20

    def test_optimization_level(self) -> None:
        """Test setting optimization level."""
        reporter = OptimizationReporter("test")
        reporter.set_optimization_level(3)

        assert reporter.module_metrics.optimization_level == 3

    def test_generate_summary(self) -> None:
        """Test generating text summary."""
        reporter = OptimizationReporter("test_module")
        reporter.set_optimization_level(2)

        # Add a pass
        reporter.start_pass(
            "constant-propagation",
            before_stats={"instructions": 100},
        )
        reporter.end_pass(
            metrics={"constants_propagated": 10},
            after_stats={"instructions": 90},
            time_ms=5.0,
        )

        summary = reporter.generate_summary()

        assert "Module: test_module" in summary
        assert "Optimization Level: 2" in summary
        assert "Total Passes: 1" in summary
        assert "Total Time: 5.00ms" in summary
        assert "constant-propagation" in summary
        assert "instructions: 10.0% reduction" in summary
        assert "constants_propagated: 10" in summary

    def test_generate_detailed_report(self) -> None:
        """Test generating detailed report."""
        reporter = OptimizationReporter("test_module")

        # Add multiple passes
        reporter.start_pass("pass1", before_stats={"size": 1000})
        reporter.end_pass(
            metrics={"optimized": 5},
            after_stats={"size": 950},
            time_ms=2.0,
        )

        reporter.start_pass("pass2", before_stats={"size": 950})
        reporter.end_pass(
            metrics={"optimized": 3},
            after_stats={"size": 920},
            time_ms=1.5,
        )

        # Add function metrics
        reporter.add_function_metrics(
            "main",
            {"complexity": 10, "lines": 50},
        )

        report = reporter.generate_detailed_report()

        assert "OPTIMIZATION REPORT" in report
        assert "DETAILED PASS STATISTICS" in report
        assert "Pass: pass1" in report
        assert "Pass: pass2" in report
        assert "Time: 2.00ms" in report
        assert "Time: 1.50ms" in report
        assert "FUNCTION METRICS" in report
        assert "Function: main" in report
        assert "complexity: 10" in report

    def test_get_report_data(self) -> None:
        """Test getting raw report data."""
        reporter = OptimizationReporter("test")

        reporter.start_pass("test_pass")
        reporter.end_pass(metrics={"changes": 5})

        data = reporter.get_report_data()

        assert isinstance(data, ModuleMetrics)
        assert data.module_name == "test"
        assert len(data.pass_metrics) == 1

    def test_empty_reporter(self) -> None:
        """Test reporter with no passes."""
        reporter = OptimizationReporter("empty")

        summary = reporter.generate_summary()

        assert "Module: empty" in summary
        assert "Total Passes: 0" in summary
        assert "Total Time: 0.00ms" in summary

    def test_end_pass_without_start(self) -> None:
        """Test ending a pass without starting one."""
        reporter = OptimizationReporter("test")

        # This should not crash
        reporter.end_pass(metrics={"test": 1})

        # No pass should be recorded
        assert len(reporter.module_metrics.pass_metrics) == 0
