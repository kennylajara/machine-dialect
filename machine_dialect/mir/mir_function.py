"""MIR Function Representation.

This module defines the MIRFunction class that represents a function
in the MIR, including its parameters, locals, temporaries, and CFG.
"""

from .basic_block import CFG
from .mir_types import MIRType, MIRUnionType
from .mir_values import ScopedVariable, Temp, Variable


class MIRFunction:
    """A function in MIR representation.

    Contains all the information about a function including its
    signature, local variables, temporaries, and control flow graph.
    """

    def __init__(
        self,
        name: str,
        params: list[Variable | ScopedVariable] | None = None,
        return_type: MIRType = MIRType.EMPTY,
    ) -> None:
        """Initialize a MIR function.

        Args:
            name: Function name.
            params: List of parameter variables.
            return_type: Return type of the function.
        """
        self.name = name
        self.params = params if params is not None else []
        self.return_type = return_type
        self.locals: dict[str, Variable] = {}
        self.temporaries: list[Temp] = []
        self.cfg = CFG()
        self.is_ssa = False
        self._next_temp_id = 0
        self._next_var_version: dict[str, int] = {}

    def add_local(self, var: Variable) -> None:
        """Add a local variable.

        Args:
            var: The variable to add.
        """
        self.locals[var.name] = var

    def declare_local(self, name: str, mir_type: MIRType) -> Variable:
        """Declare a function-local variable.

        Args:
            name: The variable name.
            mir_type: The type of the variable.

        Returns:
            A ScopedVariable with LOCAL scope.
        """
        from .mir_values import ScopedVariable, VariableScope

        var = ScopedVariable(name, VariableScope.LOCAL, mir_type)
        self.locals[name] = var
        return var

    def get_local(self, name: str) -> Variable | None:
        """Get a local variable by name.

        Args:
            name: Variable name.

        Returns:
            The variable or None if not found.
        """
        return self.locals.get(name)

    def new_temp(self, mir_type: MIRType | MIRUnionType) -> Temp:
        """Create a new temporary.

        Args:
            mir_type: Type of the temporary.

        Returns:
            A new temporary.
        """
        temp = Temp(mir_type, self._next_temp_id)
        self._next_temp_id += 1
        self.temporaries.append(temp)
        return temp

    def new_var_version(self, var_name: str) -> int:
        """Get a new SSA version for a variable.

        Args:
            var_name: Variable name.

        Returns:
            The next version number.
        """
        if var_name not in self._next_var_version:
            self._next_var_version[var_name] = 1
        version = self._next_var_version[var_name]
        self._next_var_version[var_name] += 1
        return version

    def get_param_by_name(self, name: str) -> Variable | None:
        """Get a parameter by name.

        Args:
            name: Parameter name.

        Returns:
            The parameter variable or None if not found.
        """
        for param in self.params:
            if param.name == name:
                return param
        return None

    def to_string(self, include_cfg: bool = True) -> str:
        """Convert function to string representation.

        Args:
            include_cfg: Whether to include the CFG in the output.

        Returns:
            String representation of the function.
        """
        lines = []

        # Function signature
        params_str = ", ".join(f"{p.name}: {p.type}" for p in self.params)
        if self.return_type != MIRType.EMPTY:
            lines.append(f"function {self.name}({params_str}) -> {self.return_type} {{")
        else:
            lines.append(f"function {self.name}({params_str}) {{")

        # Locals
        if self.locals:
            lines.append("  locals:")
            for name, var in self.locals.items():
                lines.append(f"    {name}: {var.type}")

        # Temporaries (summary)
        if self.temporaries:
            lines.append(f"  temporaries: {len(self.temporaries)}")

        # SSA status
        lines.append(f"  ssa: {self.is_ssa}")

        # CFG
        if include_cfg:
            lines.append("  cfg:")
            cfg_str = str(self.cfg)
            for line in cfg_str.split("\n"):
                lines.append(f"    {line}")

        lines.append("}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return string representation."""
        return self.to_string()

    def __repr__(self) -> str:
        """Return debug representation."""
        return f"MIRFunction({self.name}, params={len(self.params)}, locals={len(self.locals)})"
