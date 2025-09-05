"""Tests for the Environment class."""

import pytest

from machine_dialect.interpreter.objects import Boolean, Empty, Environment, Float, String, WholeNumber


class TestEnvironment:
    """Test the Environment class for variable storage and retrieval."""

    def test_environment_initialization(self) -> None:
        """Test that a new environment starts with an empty store."""
        env = Environment()
        assert env.store == {}
        assert len(env.store) == 0

    def test_environment_set_and_get(self) -> None:
        """Test basic variable storage and retrieval."""
        env = Environment()
        value = WholeNumber(42)

        # Set a variable
        env["x"] = value

        # Get the variable
        assert env["x"] is value
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 42

    def test_environment_contains(self) -> None:
        """Test checking if a variable exists in the environment."""
        env = Environment()

        # Variable doesn't exist yet
        assert "x" not in env

        # Add variable
        env["x"] = WholeNumber(100)

        # Now it exists
        assert "x" in env
        assert "y" not in env

    def test_environment_overwrite(self) -> None:
        """Test that variables can be overwritten with new values."""
        env = Environment()

        # Set initial value
        env["x"] = WholeNumber(10)
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 10

        # Overwrite with new value
        env["x"] = WholeNumber(20)
        assert isinstance(env["x"], WholeNumber)
        assert env["x"].value == 20

        # Overwrite with different type
        env["x"] = String("hello")
        assert isinstance(env["x"], String)
        assert env["x"].value == "hello"

    def test_environment_key_error(self) -> None:
        """Test that accessing undefined variables raises KeyError."""
        env = Environment()

        with pytest.raises(KeyError):
            _ = env["undefined_variable"]

    def test_environment_multiple_variables(self) -> None:
        """Test storing multiple variables of different types."""
        env = Environment()

        # Store various types
        env["int_var"] = WholeNumber(42)
        env["float_var"] = Float(3.14)
        env["string_var"] = String("hello")
        env["bool_var"] = Boolean(True)
        env["empty_var"] = Empty()

        # Verify all are stored correctly
        assert len(env.store) == 5
        assert isinstance(env["int_var"], WholeNumber)
        assert env["int_var"].value == 42
        assert isinstance(env["float_var"], Float)
        assert env["float_var"].value == 3.14
        assert isinstance(env["string_var"], String)
        assert env["string_var"].value == "hello"
        assert isinstance(env["bool_var"], Boolean)
        assert env["bool_var"].value is True
        assert isinstance(env["empty_var"], Empty)
        assert env["empty_var"].value is None

    def test_environment_copy(self) -> None:
        """Test copying environment state to a new environment."""
        env1 = Environment()
        env1["x"] = WholeNumber(10)
        env1["y"] = String("test")

        # Create new environment and copy state
        env2 = Environment()
        env2.store.update(env1.store)

        # Verify copies
        assert isinstance(env2["x"], WholeNumber)
        assert env2["x"].value == 10
        assert isinstance(env2["y"], String)
        assert env2["y"].value == "test"

        # Verify they're independent
        env1["x"] = WholeNumber(20)
        assert isinstance(env1["x"], WholeNumber)
        assert env1["x"].value == 20
        assert isinstance(env2["x"], WholeNumber)
        assert env2["x"].value == 10  # Unchanged

    def test_environment_special_characters_in_names(self) -> None:
        """Test variable names with spaces and special characters."""
        env = Environment()

        # Machine Dialect allows variable names with spaces
        env["my variable"] = WholeNumber(100)
        env["variable-with-dash"] = String("dash")
        env["variable_with_underscore"] = Boolean(False)

        assert isinstance(env["my variable"], WholeNumber)
        assert env["my variable"].value == 100
        assert isinstance(env["variable-with-dash"], String)
        assert env["variable-with-dash"].value == "dash"
        assert isinstance(env["variable_with_underscore"], Boolean)
        assert env["variable_with_underscore"].value is False

    def test_environment_case_sensitivity(self) -> None:
        """Test that variable names are case-sensitive."""
        env = Environment()

        env["Variable"] = WholeNumber(1)
        env["variable"] = WholeNumber(2)
        env["VARIABLE"] = WholeNumber(3)

        assert isinstance(env["Variable"], WholeNumber)
        assert env["Variable"].value == 1
        assert isinstance(env["variable"], WholeNumber)
        assert env["variable"].value == 2
        assert isinstance(env["VARIABLE"], WholeNumber)
        assert env["VARIABLE"].value == 3
        assert len(env.store) == 3

    def test_environment_store_direct_access(self) -> None:
        """Test that the store dictionary can be accessed directly."""
        env = Environment()

        # Direct store manipulation
        env.store["direct"] = WholeNumber(99)

        # Should be accessible via getitem
        assert isinstance(env["direct"], WholeNumber)
        assert env["direct"].value == 99

        # And via contains
        assert "direct" in env

    def test_environment_iteration(self) -> None:
        """Test iterating over environment variables."""
        env = Environment()
        env["a"] = WholeNumber(1)
        env["b"] = WholeNumber(2)
        env["c"] = WholeNumber(3)

        # Get all keys
        keys = list(env.store.keys())
        assert set(keys) == {"a", "b", "c"}

        # Get all values
        values = list(env.store.values())
        assert all(isinstance(v, WholeNumber) for v in values)
        int_values = [v for v in values if isinstance(v, WholeNumber)]
        assert {v.value for v in int_values} == {1, 2, 3}

    def test_environment_clear(self) -> None:
        """Test clearing all variables from an environment."""
        env = Environment()
        env["x"] = WholeNumber(1)
        env["y"] = WholeNumber(2)

        assert len(env.store) == 2

        # Clear the store
        env.store.clear()

        assert len(env.store) == 0
        assert "x" not in env
        assert "y" not in env

    def test_environment_independent_instances(self) -> None:
        """Test that different Environment instances are independent."""
        env1 = Environment()
        env2 = Environment()

        env1["x"] = WholeNumber(100)

        # env2 should not have the variable
        assert "x" not in env2

        # Adding to env2 shouldn't affect env1
        env2["y"] = String("separate")
        assert "y" not in env1
