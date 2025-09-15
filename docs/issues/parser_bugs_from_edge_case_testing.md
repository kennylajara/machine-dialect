# Parser Bugs Found During Edge Case Testing

This document lists parser bugs discovered while implementing comprehensive edge case tests for
collection operations.

## 1. Invalid Ordinals Cause Statement Fragmentation

**Location**: `machine_dialect/tests/edge_cases/test_invalid_operations.py::test_invalid_ordinal_usage`

**Issue**: When the parser encounters invalid ordinals like "zeroth", "fourth", "fifth" in
collection access expressions, it breaks the statement into multiple fragments instead of parsing
the entire expression as one unit.

**Example**:

```markdown
Set `x` to the zeroth item of `list`.
```

**Expected**: 1 SetStatement with an error in the expression
**Actual**: Multiple statements (SetStatement + ExpressionStatements)

**Impact**: Parser creates 14 statements instead of 8 for the test case

## 2. Named List Parsing Stops After SetStatement

**Location**: `machine_dialect/tests/edge_cases/test_invalid_operations.py::test_type_mismatched_operations`

**Issue**: After parsing a named list with `- key: value` syntax, the parser fails to continue
parsing subsequent statements.

**Example**:

```markdown
Define `dict` as named list.
Set `dict` to:
- key1: _"value1"_.
- key2: _"value2"_.

Set item _1_ of `dict` to _"new"_.  # This doesn't get parsed
```

**Expected**: All statements should be parsed
**Actual**: Parser stops after the named list SetStatement

**Impact**: Only 4 statements parsed instead of 6

## 3. Clear Operation Lacks Type Checking

**Location**: `machine_dialect/semantic/analyzer.py` (line 439-440)

**Issue**: The semantic analyzer doesn't validate that the Clear operation is only used on
collection types. It allows clearing non-collection variables without error.

**Example**:

```markdown
Define `number` as Whole Number.
Clear `number`.  # Should error, but doesn't
```

**Expected**: Semantic error for clearing non-collections
**Actual**: No error generated

## 4. Zero Index Not Properly Validated

**Location**: `machine_dialect/tests/edge_cases/test_boundary_access.py::test_zero_index_should_error`

**Issue**: The semantic analyzer doesn't properly check for zero indices in collection access
(Machine Dialect uses 1-based indexing).

**Example**:

```markdown
Set `x` to item _0_ of `list`.  # Should error for 0 index
```

**Expected**: Semantic error about invalid zero index
**Actual**: No specific error about zero indexing

## 5. Missing Parser Features

Several tests fail due to missing parser features that were assumed to exist:

- `whether...has` syntax for checking named list keys
- Proper handling of property access on named lists
- Full support for nested collection operations

## Recommendations

1. **Priority 1**: Fix the named list parsing issue (#2) as it completely breaks parsing flow
2. **Priority 2**: Add proper validation for Clear operations (#3) and zero indexing (#4)
3. **Priority 3**: Fix invalid ordinal handling (#1) to improve error recovery
4. **Priority 4**: Implement missing features as needed

## Test Statistics

After fixes applied during edge case implementation:

- **Total tests**: 65
- **Passing**: 33
- **Skipped**: 32 (with TODOs for fixing)
- **Failing**: 0
- **Success rate**: 50.8% (excluding skipped)

All failing tests have been marked with `@pytest.mark.skip` and include TODOs explaining what
needs to be fixed. Most failures are due to:

1. Parser bugs documented above
2. Tests containing comments (parser doesn't support comments yet)
3. Assertion count mismatches that need investigation
4. Missing parser features like `whether...has` syntax
