"""Unit tests for the Compiler class.

This module contains comprehensive unit tests for the main Compiler class,
testing compilation of files and strings, error handling, and output generation.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from machine_dialect.codegen.bytecode_module import BytecodeModule
from machine_dialect.compiler.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel
from machine_dialect.compiler.context import CompilationContext


class TestCompilerInit:
    """Test Compiler initialization."""

    def test_init_with_default_config(self) -> None:
        """Test compiler initialization with default configuration."""
        with patch("machine_dialect.compiler.compiler.CompilationPipeline"):
            compiler = Compiler()

            assert compiler.config is not None
            assert isinstance(compiler.config, CompilerConfig)
            assert compiler.pipeline is not None

    def test_init_with_custom_config(self) -> None:
        """Test compiler initialization with custom configuration."""
        with patch("machine_dialect.compiler.compiler.CompilationPipeline"):
            config = CompilerConfig(optimization_level=OptimizationLevel.AGGRESSIVE, verbose=True, debug=True)
            compiler = Compiler(config)

            assert compiler.config is config
            assert compiler.config.optimization_level == OptimizationLevel.AGGRESSIVE
            assert compiler.config.verbose is True
            assert compiler.config.debug is True


class TestCompileFile:
    """Test Compiler.compile_file method."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_compile_file_success_no_output_path(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test successful file compilation without specified output path."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = Mock(spec=BytecodeModule)
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"
        mock_context.bytecode_module.serialize.return_value = b"bytecode"
        mock_pipeline.compile_file.return_value = mock_context

        # Create compiler with mocked pipeline
        compiler = Compiler()

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Set `x` to _42_.")
            source_path = Path(f.name)

        try:
            # Mock file operations
            with patch("builtins.open", mock_open()):
                result = compiler.compile_file(source_path)

                assert result is True
                mock_pipeline.compile_file.assert_called_once_with(source_path)
                mock_context.print_errors_and_warnings.assert_called_once()
                mock_context.has_errors.assert_called_once()
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_compile_file_success_with_output_path(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test successful file compilation with specified output path."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = Mock(spec=BytecodeModule)
        mock_context.get_output_path.return_value = Path("custom_output.mdb")
        mock_context.get_module_name.return_value = "test_module"
        mock_context.bytecode_module.serialize.return_value = b"bytecode"
        mock_pipeline.compile_file.return_value = mock_context

        # Create compiler with mocked pipeline
        compiler = Compiler()

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Set `x` to _42_.")
            source_path = Path(f.name)

        try:
            output_path = Path("custom_output.mdb")
            # Mock file operations
            with patch("builtins.open", mock_open()):
                result = compiler.compile_file(source_path, output_path)

                assert result is True
                assert compiler.config.output_path == output_path
                mock_pipeline.compile_file.assert_called_once_with(source_path)
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compile_file_with_errors(self, mock_pipeline_class: Mock) -> None:
        """Test file compilation with compilation errors."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = True
        mock_pipeline.compile_file.return_value = mock_context

        # Create compiler with mocked pipeline
        compiler = Compiler()

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Invalid syntax here")
            source_path = Path(f.name)

        try:
            result = compiler.compile_file(source_path)

            assert result is False
            mock_context.print_errors_and_warnings.assert_called_once()
            mock_context.has_errors.assert_called_once()
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compile_file_save_module_failure(self, mock_pipeline_class: Mock) -> None:
        """Test file compilation with module save failure."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = Mock(spec=BytecodeModule)
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"
        mock_context.bytecode_module.serialize.return_value = b"bytecode"
        mock_pipeline.compile_file.return_value = mock_context

        # Create compiler with mocked pipeline
        compiler = Compiler()

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Set `x` to _42_.")
            source_path = Path(f.name)

        try:
            # Mock file write failure
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                result = compiler.compile_file(source_path)

                assert result is False
                mock_context.add_error.assert_called_once()
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compile_file_mir_phase_only(self, mock_pipeline_class: Mock) -> None:
        """Test file compilation in MIR-only mode."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = None  # No bytecode in MIR-only mode
        mock_pipeline.compile_file.return_value = mock_context

        # Setup compiler with MIR-only config
        config = CompilerConfig(mir_phase_only=True)
        compiler = Compiler(config)

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Set `x` to _42_.")
            source_path = Path(f.name)

        try:
            result = compiler.compile_file(source_path)

            assert result is True
            # Should not try to save module or get output path in MIR-only mode
            mock_context.get_output_path.assert_not_called()
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_compile_file_verbose_mode(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test file compilation in verbose mode."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = Mock(spec=BytecodeModule)
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"
        mock_context.bytecode_module.serialize.return_value = b"bytecode"
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "mir_functions": 1,
            "bytecode_chunks": 1,
        }
        mock_pipeline.compile_file.return_value = mock_context

        # Setup compiler with verbose config
        config = CompilerConfig(verbose=True)
        compiler = Compiler(config)

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Set `x` to _42_.")
            source_path = Path(f.name)

        try:
            # Mock file operations
            with patch("builtins.open", mock_open()):
                result = compiler.compile_file(source_path)

                assert result is True
                # Should print verbose messages
                assert mock_print.called
                # Check that compilation summary was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Compilation Summary" in str(call) for call in print_calls)
        finally:
            source_path.unlink()


class TestCompileString:
    """Test Compiler.compile_string method."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compile_string_default_module_name(self, mock_pipeline_class: Mock) -> None:
        """Test string compilation with default module name."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_pipeline.compile.return_value = mock_context

        compiler = Compiler()
        source = "Set `x` to _42_."
        result = compiler.compile_string(source)

        assert result is mock_context
        assert compiler.config.module_name == "__main__"
        mock_pipeline.compile.assert_called_once()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compile_string_custom_module_name(self, mock_pipeline_class: Mock) -> None:
        """Test string compilation with custom module name."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_context = Mock(spec=CompilationContext)
        mock_pipeline.compile.return_value = mock_context

        compiler = Compiler()
        source = "Set `x` to _42_."
        module_name = "test_module"
        result = compiler.compile_string(source, module_name)

        assert result is mock_context
        assert compiler.config.module_name == module_name
        mock_pipeline.compile.assert_called_once()

        # Check that context was created correctly
        call_args = mock_pipeline.compile.call_args[0][0]
        assert isinstance(call_args, CompilationContext)
        assert call_args.source_path == Path("<string>")
        assert call_args.source_content == source


class TestSaveModule:
    """Test Compiler._save_module method."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_save_module_no_bytecode(self, mock_pipeline_class: Mock) -> None:
        """Test save module when no bytecode module exists."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.bytecode_module = None

        result = compiler._save_module(mock_context)

        assert result is False

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_save_module_success(self, mock_pipeline_class: Mock) -> None:
        """Test successful module save."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_bytecode_module = Mock(spec=BytecodeModule)
        mock_bytecode_module.serialize.return_value = b"bytecode_data"
        mock_context.bytecode_module = mock_bytecode_module
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"

        with patch("builtins.open", mock_open()) as mock_file:
            result = compiler._save_module(mock_context)

            assert result is True
            mock_bytecode_module.serialize.assert_called_once()
            mock_file().write.assert_called_once_with(b"bytecode_data")
            assert mock_bytecode_module.name == "test_module"

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_save_module_write_error(self, mock_pipeline_class: Mock) -> None:
        """Test module save with write error."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_bytecode_module = Mock(spec=BytecodeModule)
        mock_bytecode_module.serialize.return_value = b"bytecode_data"
        mock_context.bytecode_module = mock_bytecode_module
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"

        # Mock file write error
        with patch("builtins.open", side_effect=OSError("Disk full")):
            result = compiler._save_module(mock_context)

            assert result is False
            mock_context.add_error.assert_called_once()
            error_msg = mock_context.add_error.call_args[0][0]
            assert "Failed to save module" in error_msg

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_save_module_verbose(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test module save in verbose mode."""
        config = CompilerConfig(verbose=True)
        compiler = Compiler(config)

        mock_context = Mock(spec=CompilationContext)
        mock_bytecode_module = Mock(spec=BytecodeModule)
        mock_bytecode_module.serialize.return_value = b"bytecode_data"
        mock_context.bytecode_module = mock_bytecode_module
        mock_context.get_output_path.return_value = Path("output.mdb")
        mock_context.get_module_name.return_value = "test_module"

        with patch("builtins.open", mock_open()):
            result = compiler._save_module(mock_context)

            assert result is True
            mock_print.assert_called_once()
            assert "Wrote compiled module" in mock_print.call_args[0][0]


class TestShowDisassembly:
    """Test Compiler._show_disassembly method."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_show_disassembly_no_bytecode(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test disassembly when no bytecode module exists."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.bytecode_module = None

        compiler._show_disassembly(mock_context)

        mock_print.assert_not_called()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_show_disassembly_with_bytecode(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test disassembly with bytecode module."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.bytecode_module = Mock(spec=BytecodeModule)

        compiler._show_disassembly(mock_context)

        # Should print disassembly header and placeholder message
        assert mock_print.call_count == 2
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Disassembly" in call for call in print_calls)
        assert any("not yet implemented" in call for call in print_calls)


class TestPrintSuccess:
    """Test Compiler._print_success method."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_print_success_basic_stats(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test success message with basic statistics."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.get_statistics.return_value = {"source_file": "test.md", "module_name": "test_module"}

        compiler._print_success(mock_context)

        # Check that summary was printed
        assert mock_print.called
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Compilation Summary" in call for call in print_calls)
        assert any("test.md" in call for call in print_calls)
        assert any("test_module" in call for call in print_calls)

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_print_success_with_mir_functions(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test success message with MIR function count."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "mir_functions": 3,
        }

        compiler._print_success(mock_context)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Functions: 3" in call for call in print_calls)

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_print_success_with_optimizations_string(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test success message with optimizations as string."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "optimizations": "Applied constant folding and DCE",
        }

        compiler._print_success(mock_context)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Optimizations applied" in call for call in print_calls)

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_print_success_with_optimizations_dict(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test success message with optimizations as dictionary."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "optimizations": {"total_transformations": 5},
        }

        compiler._print_success(mock_context)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Optimizations applied: 5" in call for call in print_calls)

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_print_success_with_bytecode_chunks(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test success message with bytecode chunk count."""
        compiler = Compiler()
        mock_context = Mock(spec=CompilationContext)
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "bytecode_chunks": 2,
        }

        compiler._print_success(mock_context)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Bytecode chunks: 2" in call for call in print_calls)


class TestIntegration:
    """Integration tests for the Compiler class."""

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    @patch("builtins.print")
    def test_full_compilation_workflow(self, mock_print: Mock, mock_pipeline_class: Mock) -> None:
        """Test complete compilation workflow from file to bytecode."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_bytecode_module = Mock(spec=BytecodeModule)
        mock_bytecode_module.serialize.return_value = b"compiled_bytecode"

        mock_context = Mock(spec=CompilationContext)
        mock_context.has_errors.return_value = False
        mock_context.bytecode_module = mock_bytecode_module
        mock_context.get_output_path.return_value = Path("test_output.mdb")
        mock_context.get_module_name.return_value = "test_module"
        mock_context.get_statistics.return_value = {
            "source_file": "test.md",
            "module_name": "test_module",
            "mir_functions": 2,
            "optimizations": "Applied optimizations",
            "bytecode_chunks": 1,
        }
        mock_pipeline.compile_file.return_value = mock_context

        # Setup compiler
        config = CompilerConfig(verbose=True, optimization_level=OptimizationLevel.STANDARD)
        compiler = Compiler(config)

        # Create test source file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """
# Test Program

Set `result` to _42_.
Give back `result`.
"""
            )
            source_path = Path(f.name)

        try:
            with patch("builtins.open", mock_open()) as mock_file:
                result = compiler.compile_file(source_path, Path("test_output.mdb"))

                assert result is True
                mock_pipeline.compile_file.assert_called_once_with(source_path)
                mock_context.print_errors_and_warnings.assert_called_once()
                mock_bytecode_module.serialize.assert_called_once()
                mock_file().write.assert_called_once_with(b"compiled_bytecode")
        finally:
            source_path.unlink()

    @patch("machine_dialect.compiler.compiler.CompilationPipeline")
    def test_compiler_error_handling_flow(self, mock_pipeline_class: Mock) -> None:
        """Test compiler error handling in realistic scenarios."""
        # Setup mocks
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Mock FileNotFoundError from pipeline
        mock_pipeline.compile_file.side_effect = FileNotFoundError("File not found")

        compiler = Compiler()

        # Test with non-existent source file - should raise error from pipeline
        with pytest.raises(FileNotFoundError):
            compiler.compile_file(Path("nonexistent.md"))
