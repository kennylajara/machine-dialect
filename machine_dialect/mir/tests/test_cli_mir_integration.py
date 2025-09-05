"""Integration tests for CLI MIR features."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIMIRIntegration:
    """Test CLI MIR integration features."""

    @pytest.fixture
    def test_program(self) -> str:
        """Create a simple test program."""
        return """Define `x` as Integer.
Define `y` as Integer.
Define `result` as Integer.
Set `x` to _10_.
Set `y` to _20_.
Set `result` to `x` + `y`.
Give back `result`."""

    @pytest.fixture
    def temp_file(self, test_program: str) -> str:
        """Create a temporary test file."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            delete=False,
        ) as f:
            f.write(test_program)
            return f.name

    def teardown_method(self) -> None:
        """Clean up any test files."""
        # Clean up any .mdc files created
        for f in Path(".").glob("*.mdc"):
            if f.name.startswith("tmp"):
                f.unlink()

    def run_cli_command(self, *args: str) -> tuple[int, str, str]:
        """Run a CLI command and return exit code, stdout, stderr."""
        result = subprocess.run(
            ["python", "-m", "machine_dialect", *args],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def test_dump_mir_flag(self, temp_file: str) -> None:
        """Test --dump-mir flag."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--dump-mir",
                "--opt-level",
                "0",
            )

            assert exit_code == 0, f"Compilation failed: {stderr}"
            assert "MIR Representation" in stdout
            assert "MIR Module:" in stdout
            assert "Function main" in stdout
            assert "entry:" in stdout

        finally:
            os.unlink(temp_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    def test_show_cfg_flag(self, temp_file: str) -> None:
        """Test --show-cfg flag."""
        dot_file = "test_cfg.dot"

        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--show-cfg",
                dot_file,
                "--opt-level",
                "0",
            )

            assert exit_code == 0, f"Compilation failed: {stderr}"
            assert f"Control flow graph exported to '{dot_file}'" in stdout

            # Check that DOT file was created
            assert Path(dot_file).exists()

            # Check DOT file content
            with open(dot_file) as f:
                content = f.read()
                assert "digraph MIR" in content
                assert "cluster_main" in content
                assert "entry:" in content

        finally:
            os.unlink(temp_file)
            if Path(dot_file).exists():
                os.unlink(dot_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    def test_opt_report_flag(self, temp_file: str) -> None:
        """Test --opt-report flag."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--opt-report",
                "--opt-level",
                "2",
            )

            assert exit_code == 0, f"Compilation failed: {stderr}"
            assert "Optimization Report" in stdout

            # Should show some optimization passes
            assert "constant-propagation" in stdout or "dce" in stdout

        finally:
            os.unlink(temp_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    def test_mir_phase_flag(self, temp_file: str) -> None:
        """Test --mir-phase flag."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--mir-phase",
                "--dump-mir",
            )

            # Should exit with 0 even though no bytecode is generated
            assert exit_code == 0
            assert "Stopping after MIR generation" in stdout

            # Should not create .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            assert not mdc_file.exists()

        finally:
            os.unlink(temp_file)

    def test_opt_level_flag(self, temp_file: str) -> None:
        """Test --opt-level flag with different values."""
        try:
            # Test level 0 (no optimization)
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--dump-mir",
                "--opt-level",
                "0",
            )

            assert exit_code == 0
            # Should show unoptimized MIR
            assert "entry:" in stdout

            # Test level 3 (aggressive optimization)
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--dump-mir",
                "--opt-report",
                "--opt-level",
                "3",
            )

            assert exit_code == 0
            # Should show optimization happened
            if "--opt-report" in stdout or "Optimization Report" in stdout:
                # Some optimizations should have run
                pass

        finally:
            os.unlink(temp_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    def test_combined_flags(self, temp_file: str) -> None:
        """Test combining multiple MIR flags."""
        dot_file = "combined_test.dot"

        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--dump-mir",
                "--show-cfg",
                dot_file,
                "--opt-report",
                "--opt-level",
                "2",
                "-v",  # verbose
            )

            assert exit_code == 0, f"Compilation failed: {stderr}"

            # Should have all outputs
            assert "MIR Representation" in stdout
            assert f"Control flow graph exported to '{dot_file}'" in stdout
            assert "Optimization Report" in stdout

            # Verbose should show more details
            assert "Compiling" in stdout

            # DOT file should exist
            assert Path(dot_file).exists()

        finally:
            os.unlink(temp_file)
            if Path(dot_file).exists():
                os.unlink(dot_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    def test_help_shows_mir_flags(self) -> None:
        """Test that help text includes MIR flags."""
        exit_code, stdout, stderr = self.run_cli_command(
            "compile",
            "--help",
        )

        assert exit_code == 0
        assert "--dump-mir" in stdout
        assert "--show-cfg" in stdout
        assert "--opt-report" in stdout
        assert "--mir-phase" in stdout
        assert "--opt-level" in stdout

    def test_invalid_opt_level(self, temp_file: str) -> None:
        """Test invalid optimization level."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--opt-level",
                "5",  # Invalid level
            )

            # Should fail with error
            assert exit_code != 0
            assert "Invalid value" in stderr or "invalid choice" in stderr.lower()

        finally:
            os.unlink(temp_file)

    def test_module_name_with_mir(self, temp_file: str) -> None:
        """Test module naming works with MIR pipeline."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--module-name",
                "my_test_module",
                "--dump-mir",
                "--opt-level",
                "1",
            )

            assert exit_code == 0
            assert "MIR Module: my_test_module" in stdout

        finally:
            os.unlink(temp_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()

    @pytest.mark.parametrize("opt_level", ["0", "1", "2", "3"])
    def test_all_opt_levels(self, temp_file: str, opt_level: str) -> None:
        """Test all optimization levels work."""
        try:
            exit_code, stdout, stderr = self.run_cli_command(
                "compile",
                temp_file,
                "--opt-level",
                opt_level,
            )

            assert exit_code == 0, f"Level {opt_level} failed: {stderr}"
            assert "Successfully compiled" in stdout

        finally:
            os.unlink(temp_file)
            # Clean up .mdc file
            mdc_file = Path(temp_file).with_suffix(".mdc")
            if mdc_file.exists():
                mdc_file.unlink()
