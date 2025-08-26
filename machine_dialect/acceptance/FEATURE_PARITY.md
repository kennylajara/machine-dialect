# Machine Dialect Feature Parity Report

## Executive Summary

**Current Status: INSUFFICIENT COVERAGE** - The test suite does NOT guarantee 100%
feature parity between components.

- **Integration Tests**: 70 tests covering basic features
- **Keyword Coverage**: 18/49 (37%) keywords tested
- **Operator Coverage**: 10/15 (67%) operators tested
- **Critical Finding**: Components behave inconsistently for several features

## Critical Requirement

**100% feature parity is MANDATORY** because:

- **CFG Parser** is used by code generators
- **Main Parser** is used by interpreter/compiler
- **Interpreter** provides reference implementation
- **VM** provides optimized execution
- Any divergence breaks the language toolchain consistency

## Component Overview

| Component       | Purpose                              | Current Test Coverage  |
| --------------- | ------------------------------------ | ---------------------- |
| **Main Parser** | Parse MD code to AST                 | 68/70 pass (2 skipped) |
| **CFG Parser**  | Grammar-based parsing for generators | 68/70 pass (2 skipped) |
| **Interpreter** | Direct AST evaluation                | 68/70 pass (2 skipped) |
| **VM**          | Bytecode compilation & execution     | 68/70 pass (2 skipped) |

## Current Test Coverage Analysis

### 1. Well-Covered Features

These features work consistently across all components:

#### Literals

- Integer literals: `_42_`
- Float literals: `_3.14_`
- String literals: `_"hello"_`
- Boolean literals: `_true_`, `_false_`, `_Yes_`, `_No_`
- Empty literal: `_empty_`
- URL literals: `_"https://example.com"_`

#### Variables & Assignment

- Basic set: `Set x to _42_.`
- Variable retrieval: `Give back x.`
- Reassignment: `Set x to _20_.`
- Set using utility: `Set result using square with _5_.`

#### Arithmetic Operations

- Addition: `_5_ + _3_`
- Subtraction: `_10_ - _4_`
- Multiplication: `_3_ * _7_`
- Division: `_15_ / _3_`
- Negation: `-_5_`

#### Comparison Operations

- Basic: `<`, `>`, `<=`, `>=`
- Equality: `equals`, `is equal to`
- Inequality: `is not equal to`, `is not`
- Natural language: `is more than`, `is under`, `is at least`, `is at most`

#### Control Flow

- If/Else statements
- When/Otherwise (aliases)
- Conditional expressions: `_'yes'_ if _true_ else _'no'_`
- Nested conditions

#### Functions

- Utility definitions with parameters
- Named arguments: `where x is _5_`
- Default parameters
- Recursive functions

### 2. Partially Covered Features

Features that exist but lack comprehensive testing:

#### Complex Expressions

- **Parentheses grouping**: CFG parser fails on `(_5_ + _3_) * _2_`
- **Deep nesting**: Limited testing of nested expressions
- **Operator precedence**: Not thoroughly validated

#### Identifiers

- Backtick identifiers: `\`my_var\`\` (basic coverage only)
- Multi-word identifiers: `\`my special variable\`\` (limited testing)
- Underscore in names: `my_variable` (works but not systematically tested)

### 3. Untested Features (L)

Features defined in lexer but not tested in integration suite:

#### Untested Keywords (31 total)

```text
KW_BEHAVIOR    KW_BOOL       KW_DATATYPE    KW_DATE
KW_DATETIME    KW_DEFAULT    KW_DEFINE      KW_ENTRYPOINT
KW_FILTER      KW_FLOAT      KW_FROM        KW_INPUTS
KW_INT         KW_IS         KW_LIST        KW_MAP
KW_NUMBER      KW_OBJECT     KW_OPTIONAL    KW_OUTPUTS
KW_PROMPT      KW_REDUCE     KW_REQUIRED    KW_RULE
KW_STATUS      KW_TEXT       KW_TIME        KW_TRAIT
KW_TYPE        KW_URL        KW_WHOLE
```

#### Untested Operators (5 total)

```text
OP_ASSIGN       - Assignment operator (possibly =)
OP_NEGATION     - Logical negation
OP_STRICT_EQ    - Strict equality (===)
OP_STRICT_NOT_EQ - Strict inequality (!==)
OP_TWO_STARS    - Exponentiation (**)
```

#### Other Untested Tokens

````text
PUNCT_SEMICOLON  - Statement separator (;)
PUNCT_HASH       - Single hash (#)
PUNCT_HASH_DOUBLE - Double hash (##)
PUNCT_HASH_QUAD  - Quad hash (####)
LIT_TRIPLE_BACKTICK - Code blocks (```)
MISC_COMMENT     - Comments
MISC_STOPWORD    - Stopwords handling
````

## Inconsistency Issues Found

### 1. Parser vs CFG Parser

| Feature                    | Main Parser | CFG Parser | Issue                  |
| -------------------------- | ----------- | ---------- | ---------------------- |
| Parentheses in expressions |  Works             | L Fails    | CFG grammar incomplete |
| Comments                   | L Fails     |  Works            | Inconsistent handling  |
| HTML tags in utilities     |  Works             |  Works            | OK                     |
| Backtick identifiers       |  Works             |  Works            | OK                     |

### 2. Interpreter vs VM

| Feature          | Interpreter | VM        | Issue                      |
| ---------------- | ----------- | --------- | -------------------------- |
| Basic operations |              |            | OK                         |
| Error messages   | ?           | ?         | Not tested for consistency |
| Stack limits     | N/A         | ?         | VM-specific, untested      |
| Performance      | Baseline    | Optimized | Expected difference        |

## Required Tests for 100% Parity

### Category 1: Language Features (Priority: CRITICAL)

#### 1.1 Complete Operator Tests

```python
# Test every operator across all components
operators_to_test = [
    ("Assignment", "Set x = _5_.", OP_ASSIGN),
    ("Exponentiation", "_2_ ** _3_", OP_TWO_STARS),
    ("Strict Equality", "_5_ === _5_", OP_STRICT_EQ),
    ("Strict Inequality", "_5_ !== _5.0_", OP_STRICT_NOT_EQ),
    ("Logical Negation", "!_true_", OP_NEGATION),
]
```

#### 1.2 Complete Keyword Tests

```python
# Test every keyword that should be supported
keywords_to_test = [
    ("Define", "Define rule add_one that takes x and gives back x + _1_."),
    ("Type annotations", "Set x as Integer to _5_."),
    ("Required/Optional", "Parameter x as Number (required)"),
    ("From imports", "From utilities import helper."),
    ("Object types", "Define object Person with name as Text."),
]
```

#### 1.3 Expression Complexity Tests

```python
complex_expressions = [
    "(((_1_ + _2_) * _3_) - _4_) / _5_",  # Deep nesting
    "_1_ + _2_ * _3_ - _4_ / _5_",  # Precedence
    "not (_true_ and (_false_ or _true_))",  # Boolean complexity
    "_\"hello\"_ + _\" \"_ + _\"world\"_",  # String concatenation
]
```

### Category 2: Edge Cases (Priority: HIGH)

#### 2.1 Boundary Conditions

- Empty program: `""`
- Single statement: `"Give back _1_."`
- Maximum nesting depth
- Very long identifiers
- Unicode in strings
- Special characters

#### 2.2 Error Cases

```python
error_cases = [
    ("Missing period", "Set x to _5_"),
    ("Undefined variable", "Give back undefined_var."),
    ("Type mismatch", "_\"hello\"_ + _5_"),
    ("Division by zero", "_5_ / _0_"),
    ("Syntax error", "Set to _5_."),
]
```

### Category 3: Cross-Component Validation (Priority: CRITICAL)

#### 3.1 Differential Testing Framework

```python
def test_feature_parity(code: str) -> None:
    """Ensure all components handle code identically."""
    # Parse with both parsers
    main_ast = parse_with_main(code)
    cfg_ast = parse_with_cfg(code)
    
    # Both should succeed or both should fail
    assert (main_ast is not None) == (cfg_ast is not None)
    
    if main_ast:
        # Evaluate with both executors
        interp_result = interpret(main_ast)
        vm_result = compile_and_run(main_ast)
        
        # Results must match
        assert interp_result == vm_result
```

#### 3.2 Feature Matrix Testing

```python
# Test every feature combination
features = ["literals", "operators", "control_flow", "functions"]
components = ["parser", "cfg_parser", "interpreter", "vm"]

for feature in features:
    for component in components:
        assert supports_feature(component, feature)
```

## Implementation Roadmap

### Phase 1: Document All Features (Week 1)

1. Audit lexer for all defined tokens
1. Document intended behavior for each
1. Mark deprecated/future features
1. Create feature specification

### Phase 2: Expand Test Suite (Weeks 2-3)

1. Add tests for all 31 untested keywords
1. Add tests for all 5 untested operators
1. Add complex expression tests
1. Add error handling tests

### Phase 3: Fix Inconsistencies (Weeks 3-4)

1. Fix CFG parser parentheses handling
1. Align comment handling between parsers
1. Implement missing operators consistently
1. Standardize error messages

### Phase 4: Validation Framework (Week 5)

1. Implement differential testing
1. Create feature matrix validator
1. Add continuous parity checking
1. Generate coverage reports

## Metrics for Success

### Minimum Requirements for 100% Parity

- [ ] All 49 keywords tested across all components
- [ ] All 15 operators tested across all components
- [ ] Zero inconsistencies between parser implementations
- [ ] Identical results from interpreter and VM for all valid programs
- [ ] Consistent error handling for all invalid programs
- [ ] Automated parity validation in CI/CD

### Current vs Target Metrics

| Metric               | Current     | Target       | Gap  |
| -------------------- | ----------- | ------------ | ---- |
| Keywords Tested      | 18/49 (37%) | 49/49 (100%) | 31   |
| Operators Tested     | 10/15 (67%) | 15/15 (100%) | 5    |
| Integration Tests    | 70          | ~300         | ~230 |
| Parser Consistency   | ~95%        | 100%         | 5%   |
| Executor Consistency | ~98%        | 100%         | 2%   |
| Error Case Coverage  | ~10%        | 100%         | 90%  |

## Testing Strategy

### 1. Unit Tests Per Component

Each component needs comprehensive unit tests:

- Parser: `test_parser_<feature>.py` for each feature
- CFG Parser: Mirror all parser tests
- Interpreter: `test_eval_<feature>.py` for each feature
- VM: `test_vm_<feature>.py` for each feature

### 2. Integration Test Structure

```python
@dataclass
class ParityTestCase:
    name: str
    code: str
    expected_parse: bool  # Should parsing succeed?
    expected_output: Any  # If successful, what output?
    expected_error: str   # If failure, what error?
    components: list[str] # Which components must handle this
```

### 3. Continuous Validation

```python
# Run on every commit
def validate_parity():
    for test in all_parity_tests:
        results = {}
        for component in test.components:
            results[component] = run_component(component, test.code)
        
        # All components must agree
        assert len(set(results.values())) == 1
```

## Appendix A: Token Reference

### Keywords Currently in Use

- `KW_SET`, `KW_TO`, `KW_GIVE`, `KW_BACK`, `KW_IF`, `KW_THEN`, `KW_ELSE`
- `KW_WHEN`, `KW_OTHERWISE`, `KW_AND`, `KW_OR`, `KW_NOT`
- `KW_USE`, `KW_WITH`, `KW_WHERE`, `KW_AS`, `KW_SAY`, `KW_TELL`
- `KW_ACTION`, `KW_INTERACTION`, `KW_UTILITY`, `KW_USING`

### Operators Currently in Use

- `OP_PLUS`, `OP_MINUS`, `OP_STAR`, `OP_DIVISION`
- `OP_GT`, `OP_LT`, `OP_GTE`, `OP_LTE`
- `OP_EQ`, `OP_NOT_EQ`

### Future/Deprecated Features

- Actions/Interactions: Pending object type support
- Many type-related keywords: Pending type system implementation
- Advanced operators: Pending expression enhancement

## Appendix B: Known Issues

1. **CFG Parser Limitations**

   - Cannot handle nested parentheses properly
   - Grammar needs expression precedence rules

1. **Comment Handling**

   - Main parser doesn't handle inline comments
   - CFG parser accepts but ignores comments
   - No consistent comment preservation

1. **Error Messages**

   - Interpreter and VM produce different error messages
   - No standardized error format
   - Position information inconsistent

1. **Performance**

   - No performance parity requirements defined
   - VM optimizations not documented
   - No benchmarks for comparison

## Conclusion

Achieving 100% feature parity requires:

1. **~230 additional tests** covering all language features
1. **Fixing 5-10 known inconsistencies** between components
1. **Implementing missing features** uniformly
1. **Creating automated validation** framework
1. **Continuous monitoring** of parity

Without these improvements, the language toolchain remains fragile and inconsistent,
making it unsuitable for production use.

______________________________________________________________________

*Status: INSUFFICIENT - Major work required*\
*Priority: CRITICAL - Feature parity is mandatory*
