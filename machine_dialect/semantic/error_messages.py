"""Error message generation for semantic analysis.

This module provides helpful error messages with context and suggestions
for semantic analysis errors.
"""

from difflib import SequenceMatcher


class ErrorMessageGenerator:
    """Generates helpful error messages with context and suggestions."""

    @staticmethod
    def undefined_variable(var_name: str, line: int, position: int, similar_vars: list[str] | None = None) -> str:
        """Generate error message for undefined variable.

        Args:
            var_name: Variable name that's undefined
            line: Line number
            position: Column position
            similar_vars: List of similar variable names

        Returns:
            Formatted error message
        """
        base_msg = f"Variable '{var_name}' is not defined"

        # Add line/position info
        location = f" at line {line}, column {position}"

        # Add suggestions if similar variables exist
        suggestion = ""
        if similar_vars:
            if len(similar_vars) == 1:
                suggestion = f"\nDid you mean '{similar_vars[0]}'?"
            else:
                vars_list = "', '".join(similar_vars[:3])
                suggestion = f"\nDid you mean one of: '{vars_list}'?"

        # Add hint for defining variable
        hint = f"\nHint: Add 'Define `{var_name}` as Type.' before using it"

        return base_msg + location + suggestion + hint

    @staticmethod
    def type_mismatch(
        var_name: str,
        expected_types: list[str],
        actual_type: str,
        line: int,
        position: int,
        value_repr: str | None = None,
    ) -> str:
        """Generate error message for type mismatch.

        Args:
            var_name: Variable name
            expected_types: List of expected type names
            actual_type: Actual type found
            line: Line number
            position: Column position
            value_repr: String representation of the value

        Returns:
            Formatted error message
        """
        location = f"Error at line {line}, column {position}:"

        if len(expected_types) == 1:
            expected_str = expected_types[0]
            main_msg = f"Cannot set {expected_str} variable '{var_name}' to {actual_type} value"
        else:
            expected_str = " or ".join(expected_types)
            main_msg = f"Cannot set '{var_name}' to {actual_type} value"

        if value_repr:
            main_msg += f" {value_repr}"

        type_info = f"\nExpected: {expected_str}\nActual: {actual_type}"

        # Add conversion hint if applicable
        hint = ""
        if actual_type == "Whole Number" and "Float" in expected_types:
            try:
                # Try to convert value_repr to int first to ensure proper formatting
                if value_repr and value_repr.isdigit():
                    hint = f"\nHint: Use _{value_repr}.0_ to make it a Float"
                else:
                    hint = f"\nHint: Use _{value_repr or 'value'}.0_ to make it a Float"
            except Exception:
                hint = "\nHint: Use _value.0_ to make it a Float"
        elif actual_type == "Float" and "Whole Number" in expected_types:
            hint = "\nHint: Float values cannot be assigned to Whole Number variables"

        return f"{location}\n{main_msg}{type_info}{hint}"

    @staticmethod
    def redefinition(
        var_name: str, new_line: int, new_position: int, original_line: int, original_position: int
    ) -> str:
        """Generate error message for variable redefinition.

        Args:
            var_name: Variable name
            new_line: Line of redefinition attempt
            new_position: Column of redefinition attempt
            original_line: Line of original definition
            original_position: Column of original definition

        Returns:
            Formatted error message
        """
        location = f"Error at line {new_line}, column {new_position}:"
        main_msg = f"Variable '{var_name}' is already defined"
        original = f"\nOriginal definition at line {original_line}, column {original_position}"
        hint = "\nHint: Variables cannot be redefined. Use 'Set' to change the value"

        return f"{location}\n{main_msg}{original}{hint}"

    @staticmethod
    def uninitialized_use(var_name: str, line: int, position: int, definition_line: int) -> str:
        """Generate error message for using uninitialized variable.

        Args:
            var_name: Variable name
            line: Line where used
            position: Column where used
            definition_line: Line where defined

        Returns:
            Formatted error message
        """
        location = f"Error at line {line}, column {position}:"
        main_msg = f"Variable '{var_name}' is used before being initialized"
        definition = f"\nVariable was defined at line {definition_line}"
        hint = f"\nHint: Add 'Set `{var_name}` to value.' before using it"

        return f"{location}\n{main_msg}{definition}{hint}"

    @staticmethod
    def invalid_type(type_name: str, line: int, position: int, valid_types: list[str]) -> str:
        """Generate error message for invalid type name.

        Args:
            type_name: Invalid type name
            line: Line number
            position: Column position
            valid_types: List of valid type names

        Returns:
            Formatted error message
        """
        location = f"Error at line {line}, column {position}:"
        main_msg = f"Unknown type '{type_name}'"

        # Find similar valid types
        similar = ErrorMessageGenerator._find_similar(type_name, valid_types)
        suggestion = ""
        if similar:
            if len(similar) == 1:
                suggestion = f"\nDid you mean '{similar[0]}'?"
            else:
                suggestion = f"\nDid you mean one of: {', '.join(similar[:3])}"

        valid_list = "\nValid types: " + ", ".join(sorted(valid_types))

        return f"{location}\n{main_msg}{suggestion}{valid_list}"

    @staticmethod
    def _find_similar(name: str, candidates: list[str], threshold: float = 0.6) -> list[str]:
        """Find similar names using edit distance.

        Args:
            name: Name to match
            candidates: List of candidate names
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar names
        """
        similarities = []
        for candidate in candidates:
            ratio = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
            if ratio >= threshold:
                similarities.append((candidate, ratio))

        # Sort by similarity and return names only
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in similarities[:5]]
