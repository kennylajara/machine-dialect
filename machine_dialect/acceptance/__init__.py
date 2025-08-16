"""Acceptance testing module for Machine Dialect components.

This module provides comprehensive acceptance tests that validate
all components (parser, interpreter, compiler, VM, CFG grammar) work
correctly with the same input.
"""

from machine_dialect.acceptance.integration_tests import IntegrationTestRunner

__all__ = ["IntegrationTestRunner"]
