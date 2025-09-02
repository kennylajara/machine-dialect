"""MIR generation phase of compilation.

This module handles the MIR lowering phase of compilation.
"""

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_dumper import DumpVerbosity, MIRDumper
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_printer import MIRDotExporter


class MIRGenerationPhase:
    """MIR generation phase."""

    def run(self, context: CompilationContext, hir: ASTNode) -> MIRModule | None:
        """Run MIR generation phase.

        Args:
            context: Compilation context.
            hir: High-level IR (currently AST).

        Returns:
            MIR module or None if generation failed.
        """
        if context.config.verbose:
            print("Lowering to MIR...")

        try:
            # Pass module name if available
            module_name = context.get_module_name()
            mir_module = lower_to_mir(hir, module_name)  # type: ignore[arg-type]

            if context.config.verbose:
                print(f"Generated MIR with {len(mir_module.functions)} functions")

            # Dump MIR if requested
            if context.config.dump_mir and not context.config.mir_phase_only:
                self._dump_mir(mir_module, "initial", context)

            # Export CFG if requested
            if context.config.dump_cfg:
                self._export_cfg(mir_module, context)

            return mir_module

        except Exception as e:
            context.add_error(f"MIR generation error: {e}")
            return None

    def _dump_mir(self, module: MIRModule, phase: str, context: CompilationContext) -> None:
        """Dump MIR representation.

        Args:
            module: MIR module to dump.
            phase: Phase name for labeling.
            context: Compilation context.
        """
        verbosity = DumpVerbosity.from_string(context.config.mir_dump_verbosity)
        dumper = MIRDumper(verbosity=verbosity, use_color=True)

        if phase == "initial":
            print("\n=== MIR Representation ===")
        else:
            print(f"\n=== MIR ({phase}) ===")
        dumper.dump_module(module)

    def _export_cfg(self, module: MIRModule, context: CompilationContext) -> None:
        """Export control flow graph.

        Args:
            module: MIR module.
            context: Compilation context.
        """
        if not context.config.dump_cfg:
            return

        exporter = MIRDotExporter()
        dot_content = exporter.export_module(module)

        with open(context.config.dump_cfg, "w") as f:
            f.write(dot_content)

        # Always print CFG export message (not just in verbose mode)
        print(f"Control flow graph exported to '{context.config.dump_cfg}'")
