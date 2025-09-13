"""CFG Parser for simplified Machine Dialect™ using Lark."""

from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import LarkError


class CFGParser:
    """Parser for simplified Machine Dialect™ using Lark CFG."""

    def __init__(self) -> None:
        """Initialize the parser with the grammar file."""
        grammar_path = Path(__file__).parent / "machine_dialect.lark"
        with open(grammar_path) as f:
            grammar_content = f.read()

        self.parser = Lark(grammar_content, parser="lalr", start="start", debug=False)

    def parse(self, code: str) -> Tree[Any]:
        """Parse Machine Dialect™ code into an AST.

        Args:
            code: The Machine Dialect™ code to parse.

        Returns:
            A Lark Tree representing the parsed AST.

        Raises:
            LarkError: If the code cannot be parsed.
        """
        # Handle empty or whitespace-only input
        if not code or not code.strip():
            # Return an empty tree for empty programs
            from lark import Tree

            return Tree("program", [Tree("statement_list", [])])

        try:
            return self.parser.parse(code)
        except LarkError as e:
            # Convert Lark errors to match main parser behavior
            raise ValueError(f"Syntax error: {e}") from e

    def validate(self, code: str) -> bool:
        """Validate if the code conforms to the grammar.

        Args:
            code: The Machine Dialect™ code to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            self.parse(code)
            return True
        except (LarkError, ValueError):
            return False

    def get_grammar_rules(self) -> str:
        """Get the grammar rules in a format suitable for GPT-5 CFG.

        Returns:
            String representation of grammar rules.
        """
        grammar_path = Path(__file__).parent / "machine_dialect.lark"
        with open(grammar_path) as f:
            return f.read()

    def tree_to_dict(self, tree: Tree[Any] | Token) -> dict[str, Any]:
        """Convert a Lark tree to a dictionary representation.

        Args:
            tree: The Lark tree or token to convert.

        Returns:
            Dictionary representation of the tree.
        """
        if isinstance(tree, Token):
            return {"type": "token", "name": tree.type, "value": tree.value}

        return {"type": "tree", "name": tree.data, "children": [self.tree_to_dict(child) for child in tree.children]}

    def pretty_print(self, tree: Tree[Any]) -> str:
        """Pretty print a parsed tree.

        Args:
            tree: The Lark tree to print.

        Returns:
            A formatted string representation of the tree.
        """
        return str(tree.pretty())
