"""Test that all passes are properly registered."""

import importlib
import inspect
import pkgutil

from machine_dialect.mir.optimization_pass import AnalysisPass, OptimizationPass, Pass
from machine_dialect.mir.optimizations import register_all_passes
from machine_dialect.mir.pass_manager import PassManager


class TestPassRegistration:
    """Test that all pass classes are registered."""

    def test_all_passes_registered(self) -> None:
        """Verify that all Pass subclasses are registered."""
        # Get all registered passes
        pm = PassManager()
        register_all_passes(pm)
        registered_names = set(pm.registry._passes.keys())

        # Find all Pass subclasses
        all_pass_classes = set()

        # Import all modules in mir.analyses and mir.optimizations
        import machine_dialect.mir.analyses as analyses_pkg
        import machine_dialect.mir.optimizations as opt_pkg

        for pkg in [analyses_pkg, opt_pkg]:
            for _importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):
                if not ispkg:
                    try:
                        module = importlib.import_module(modname)
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # Check if it's a concrete Pass subclass
                            if (
                                issubclass(obj, Pass)
                                and obj not in [Pass, OptimizationPass, AnalysisPass]
                                and not inspect.isabstract(obj)
                                # Exclude base classes that contain "Pass" in name but are abstract
                                and not (name.endswith("Pass") and name != obj.__name__)
                            ):
                                # Try to instantiate to get the pass name
                                try:
                                    instance = obj()
                                    info = instance.get_info()
                                    all_pass_classes.add(info.name)
                                except (TypeError, AttributeError):
                                    # Skip abstract classes or classes with required args
                                    pass
                    except ImportError:
                        # Some modules might have additional dependencies
                        pass

        # Check that all found passes are registered
        unregistered = all_pass_classes - registered_names

        assert unregistered == set(), (
            f"Found unregistered passes: {sorted(unregistered)}. "
            f"Add them to register_all_passes() in mir/optimizations/__init__.py"
        )

        # Also verify we have a reasonable number of passes
        assert len(registered_names) > 10, f"Expected at least 10 registered passes, found {len(registered_names)}"
