"""Tests for if statements with empty blocks."""

from machine_dialect.parser import Parser


class TestIfEmptyBlock:
    """Test that if statements with empty blocks generate appropriate errors."""

    def test_if_with_empty_consequence_block(self) -> None:
        """Test that an if statement with an empty consequence block generates an error."""
        source = """if True then:
>
"""
        parser = Parser()
        _ = parser.parse(source)

        # Should have an error about empty consequence block
        assert len(parser.errors) > 0
        assert any("must have a non-empty consequence block" in str(error) for error in parser.errors)

    def test_if_with_empty_else_block(self) -> None:
        """Test that an else block that is empty generates an error."""
        source = """if True then:
> Set x to 1.
else:
>
"""
        parser = Parser()
        _ = parser.parse(source)

        # Should have an error about empty else block
        assert len(parser.errors) > 0
        assert any("must not be empty" in str(error) for error in parser.errors)

    def test_nested_if_with_empty_block(self) -> None:
        """Test that nested if statements also require non-empty blocks."""
        source = """if True then:
> if False then:
> >
> Set x to 1."""

        parser = Parser()
        _ = parser.parse(source)

        # Should have an error about the nested if's empty block
        assert len(parser.errors) > 0
        assert any("must have a non-empty consequence block" in str(error) for error in parser.errors)

    def test_if_with_only_empty_lines_in_block(self) -> None:
        """Test that a block with only empty lines is still considered empty."""
        source = """if True then:
>
>
>
"""
        parser = Parser()
        _ = parser.parse(source)

        # Should have an error about empty consequence block
        assert len(parser.errors) > 0
        assert any("must have a non-empty consequence block" in str(error) for error in parser.errors)
