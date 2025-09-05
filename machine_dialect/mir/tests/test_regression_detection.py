"""Tests for regression detection system."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from machine_dialect.ast import (
    Identifier,
    Program,
    ReturnStatement,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.benchmarks.compilation_benchmark import CompilationBenchmark
from machine_dialect.mir.benchmarks.comprehensive_regression import (
    ComprehensiveRegressionDetector,
    create_regression_suite,
)
from machine_dialect.mir.benchmarks.regression_detector import RegressionDetector, RegressionThresholds


class TestRegressionDetection(unittest.TestCase):
    """Test regression detection functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_path = Path(self.temp_dir) / "baseline.json"
        self.outputs_path = Path(self.temp_dir) / "outputs.json"

    def _create_simple_program(self, value: int) -> Program:
        """Create a simple test program."""
        token = Token(TokenType.KW_SET, "set", 0, 0)
        return Program(
            [
                SetStatement(
                    token,
                    Identifier(Token(TokenType.MISC_IDENT, "x", 0, 0), "x"),
                    WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, str(value), 0, 0), value),
                ),
                ReturnStatement(
                    Token(TokenType.KW_RETURN, "return", 0, 0),
                    Identifier(Token(TokenType.MISC_IDENT, "x", 0, 0), "x"),
                ),
            ]
        )

    def test_baseline_creation(self) -> None:
        """Test creating a performance baseline."""
        detector = RegressionDetector(baseline_path=self.baseline_path)

        # Create test programs
        programs = [self._create_simple_program(i) for i in range(5)]

        # Establish baseline
        baseline = detector.establish_baseline(programs)

        self.assertIsNotNone(baseline)
        self.assertEqual(baseline.samples, 5)
        self.assertGreater(baseline.compilation_time_mean, 0)
        self.assertGreater(baseline.bytecode_size_mean, 0)

        # Check baseline was saved
        self.assertTrue(self.baseline_path.exists())

    def test_regression_detection(self) -> None:
        """Test detecting performance regression."""
        detector = RegressionDetector(
            baseline_path=self.baseline_path,
            thresholds=RegressionThresholds(
                compilation_time_percent=50.0,  # More lenient for test
                bytecode_size_percent=10.0,
                memory_usage_percent=50.0,  # More lenient for test
            ),
        )

        # Establish baseline
        programs = [self._create_simple_program(i) for i in range(5)]
        detector.establish_baseline(programs)

        # Create a benchmark result (simulated)
        benchmark = CompilationBenchmark()
        result = benchmark.benchmark_compilation(programs[0], "test")

        # Check for regression
        regressions = detector.check_regression(result)

        self.assertEqual(len(regressions), 4)  # 4 metrics checked

        # Check that bytecode size and instruction count are consistent
        # (these should not vary for the same program)
        for reg in regressions:
            if reg.metric_name in ["bytecode_size", "instruction_count"]:
                # These should be exactly the same
                self.assertFalse(reg.is_regression)
                self.assertAlmostEqual(reg.percent_change, 0.0, places=1)

    def test_comprehensive_regression(self) -> None:
        """Test comprehensive regression detection."""
        detector = ComprehensiveRegressionDetector(
            baseline_path=self.baseline_path,
            expected_outputs_path=self.outputs_path,
        )

        # Test correctness validation
        program = self._create_simple_program(42)
        correctness = detector.validate_correctness(program, "test1")

        self.assertTrue(correctness.is_correct)
        self.assertEqual(correctness.actual_output, 42)

        # Run comprehensive check
        benchmark = CompilationBenchmark()
        bench_result = benchmark.benchmark_compilation(program, "test1")

        comprehensive = detector.comprehensive_check(program, "test1", bench_result)

        self.assertFalse(comprehensive.has_regression)
        self.assertFalse(comprehensive.has_correctness_issue)

        # Generate report
        report = detector.generate_comprehensive_report([comprehensive])
        self.assertIn("All tests passed", report)

    def test_regression_suite(self) -> None:
        """Test the standard regression suite."""
        suite = create_regression_suite()

        self.assertIn("arithmetic", suite)
        self.assertIn("control_flow", suite)

        # Run suite through detector
        detector = ComprehensiveRegressionDetector(
            baseline_path=self.baseline_path,
            expected_outputs_path=self.outputs_path,
        )

        results = []
        for name, program in suite.items():
            result = detector.comprehensive_check(program, name)
            results.append(result)

        # Generate report
        report = detector.generate_comprehensive_report(results)
        self.assertIsNotNone(report)

    def test_trend_analysis(self) -> None:
        """Test performance trend analysis."""
        detector = RegressionDetector(baseline_path=self.baseline_path)

        # Create multiple benchmark results
        benchmark = CompilationBenchmark()
        programs = [self._create_simple_program(i) for i in range(10)]

        results = []
        for i, program in enumerate(programs):
            result = benchmark.benchmark_compilation(program, f"test_{i}")
            results.append(result)

        # Analyze trends
        trends = detector.analyze_trends(results, window_size=3)

        self.assertIn("compilation_time", trends)
        self.assertIn("bytecode_size", trends)

        # Check trend structure
        ct_trend = trends["compilation_time"]
        self.assertIn("mean", ct_trend)
        self.assertIn("trend_direction", ct_trend)
        self.assertIn("trend_strength", ct_trend)


if __name__ == "__main__":
    unittest.main()
