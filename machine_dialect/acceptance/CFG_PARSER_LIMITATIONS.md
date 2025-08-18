# CFG Parser Limitations

This document comprehensively lists ALL features supported by the main Machine Dialect
parser that are NOT supported by the CFG (Lark-based) parser.

## 1. Utility (Function) Features

### 1.1 Utility Definitions

- **NOT SUPPORTED**: `### **Utility**: \`name\`\` markdown header syntax
- **NOT SUPPORTED**: HTML documentation blocks (`<details>`, `<summary>`, `</details>`, `</summary>`)
- **NOT SUPPORTED**: Markdown block quotes (>) for utility body content
- **NOT SUPPORTED**: `#### Inputs:` section with parameter definitions
- **NOT SUPPORTED**: `#### Outputs:` section with return type definitions
- **NOT SUPPORTED**: Parameter type annotations with **as** in markdown format
- **NOT SUPPORTED**: Default parameter values in markdown format

### 1.2 Utility Calls

- **NOT SUPPORTED**: `Use` keyword (replaced `Call` in main parser)
- **PARTIALLY SUPPORTED**: `Call` keyword exists but lacks full backtick identifier support
- **NOT SUPPORTED**: Named arguments with `where` clause
- **NOT SUPPORTED**: `Set` statement with `using` keyword for capturing return values

## 2. Identifier and Variable Features

### 2.1 Backtick Identifiers

- **NOT SUPPORTED**: Backtick-wrapped identifiers (\`identifier\`)
- **NOT SUPPORTED**: Backtick identifiers in function calls
- **NOT SUPPORTED**: Backtick identifiers in expressions
- **NOT SUPPORTED**: Multi-word backtick identifiers (\`multi word name\`)

### 2.2 Bold Variables

- **NOT SUPPORTED**: Bold variable syntax (**variable**)
- **NOT SUPPORTED**: Bold variables in set statements
- **NOT SUPPORTED**: Bold variables in expressions

## 3. HTML/Markdown Tags

### 3.1 Documentation Tags

- **NOT SUPPORTED**: `<details>` tag (TokenType.TAG_DETAILS_START)
- **NOT SUPPORTED**: `</details>` tag (TokenType.TAG_DETAILS_END)
- **NOT SUPPORTED**: `<summary>` tag (TokenType.TAG_SUMMARY_START)
- **NOT SUPPORTED**: `</summary>` tag (TokenType.TAG_SUMMARY_END)

### 3.2 Markdown Headers

- **NOT SUPPORTED**: Level 3 headers (###) for utilities
- **NOT SUPPORTED**: Level 4 headers (####) for inputs/outputs sections
- **NOT SUPPORTED**: Bold text in headers

## 4. Advanced Keywords

### 4.1 Type Keywords

- **NOT SUPPORTED**: `Boolean` type keyword
- **NOT SUPPORTED**: `Float` type keyword
- **NOT SUPPORTED**: `Integer` type keyword
- **NOT SUPPORTED**: `Number` type keyword
- **NOT SUPPORTED**: `Text` type keyword
- **NOT SUPPORTED**: `List` type keyword
- **NOT SUPPORTED**: `URL` type keyword
- **NOT SUPPORTED**: `Date` type keyword
- **NOT SUPPORTED**: `DateTime` type keyword
- **NOT SUPPORTED**: `Time` type keyword
- **NOT SUPPORTED**: `DataType` keyword
- **NOT SUPPORTED**: `Whole Number` type keyword

### 4.2 Function-Related Keywords

- **NOT SUPPORTED**: `Utility` keyword
- **NOT SUPPORTED**: `using` keyword (for Set with function calls)
- **NOT SUPPORTED**: `Inputs` keyword
- **NOT SUPPORTED**: `Outputs` keyword
- **NOT SUPPORTED**: `Use` keyword (modern function call syntax)
- **NOT SUPPORTED**: `required` keyword
- **NOT SUPPORTED**: `optional` keyword
- **NOT SUPPORTED**: `default` keyword

### 4.3 Behavior Keywords

- **NOT SUPPORTED**: `behavior`/`behaviors`/`behaviour`/`behaviours` keywords
- **NOT SUPPORTED**: `trait`/`traits` keywords
- **NOT SUPPORTED**: `rule` keyword
- **NOT SUPPORTED**: `template` keyword
- **NOT SUPPORTED**: `prompt` keyword
- **NOT SUPPORTED**: `Status` keyword

### 4.4 Module/Structure Keywords

- **NOT SUPPORTED**: `define` keyword
- **NOT SUPPORTED**: `from` keyword
- **NOT SUPPORTED**: `entrypoint` keyword
- **NOT SUPPORTED**: `filter` keyword
- **NOT SUPPORTED**: `take`/`takes` keywords

### 4.5 Alternative Keywords

- **NOT SUPPORTED**: `when`/`whenever` as alternatives to `if`
- **NOT SUPPORTED**: `otherwise` as alternative to `else`
- **NOT SUPPORTED**: `Tell` keyword

## 5. Natural Language Operators

### 5.1 Additional Comparison Forms

- **PARTIALLY SUPPORTED**: Some natural language operators work, but not all variants
- **NOT SUPPORTED**: `is more than` (alternative to `is greater than`)
- **NOT SUPPORTED**: `is under` (alternative to `is less than`)
- **NOT SUPPORTED**: `is fewer than` (alternative to `is less than`)
- **NOT SUPPORTED**: `is at least` (alternative to `is greater or equal to`)
- **NOT SUPPORTED**: `is no less than` (alternative to `is greater or equal to`)
- **NOT SUPPORTED**: `is at most` (alternative to `is less than or equal to`)
- **NOT SUPPORTED**: `is no more than` (alternative to `is less than or equal to`)
- **NOT SUPPORTED**: `doesn't equal` (contraction form)
- **NOT SUPPORTED**: `isn't` (contraction form)

## 6. Literal Features

### 6.1 Boolean Alternatives

- **NOT SUPPORTED**: `Yes` as alternative to `True`
- **NOT SUPPORTED**: `No` as alternative to `False`

### 6.2 URL Literals

- **LIMITED SUPPORT**: Basic URL literals work, but complex URLs may fail
- **NOT SUPPORTED**: URLs with query parameters and fragments in all contexts

## 7. Block Structure Features

### 7.1 Nested Block Markers

- **LIMITED SUPPORT**: Simple block content with > markers
- **NOT SUPPORTED**: Complex nested blocks with multiple > levels
- **NOT SUPPORTED**: Block content with embedded expressions
- **NOT SUPPORTED**: Block content with utility definitions

## 8. Expression Features

### 8.1 Complex Expressions

- **NOT SUPPORTED**: Expressions with backtick identifiers
- **NOT SUPPORTED**: Expressions with bold variables
- **NOT SUPPORTED**: Mixed identifier styles in same expression

## 9. Statement Features

### 9.1 Action/Interaction Features

- **LIMITED SUPPORT**: Basic action/interaction structure
- **NOT SUPPORTED**: Full parameter type annotations
- **NOT SUPPORTED**: Default parameter values in actions/interactions
- **NOT SUPPORTED**: Complex block content in actions/interactions

### 9.2 Set Statement Variants

- **NOT SUPPORTED**: `Set` with `using` for function call assignment
- **NOT SUPPORTED**: `Set` with backtick identifiers
- **NOT SUPPORTED**: `Set` with bold variables

## 10. Comment Features

### 10.1 Advanced Comments

- **BASIC SUPPORT**: Single-line # comments
- **NOT SUPPORTED**: Multi-line comment blocks
- **NOT SUPPORTED**: Inline comments within statements

## 11. LaTeX Math Features

### 11.1 Math Blocks

- **NOT SUPPORTED**: LaTeX math blocks with `$$...$$`
- **NOT SUPPORTED**: Inline math expressions
- **NOT SUPPORTED**: Complex mathematical notation

## 12. Error Recovery

### 12.1 Parser Resilience

- **NOT SUPPORTED**: Panic mode error recovery
- **NOT SUPPORTED**: Multiple error reporting
- **NOT SUPPORTED**: Error synchronization at statement boundaries

## Summary

The CFG parser is a **simplified validation parser** that covers basic Machine Dialect syntax
but lacks support for:

1. **Modern function syntax** (utilities, Use keyword, using keyword)
1. **Rich documentation features** (HTML tags, markdown headers)
1. **Advanced identifier formats** (backticks, bold text)
1. **Type system keywords** (Boolean, Integer, Float, etc.)
1. **Natural language operator variants**
1. **Complex nested structures**
1. **Error recovery mechanisms**

The CFG parser is suitable for:

- Basic syntax validation
- Simple arithmetic and boolean expressions
- Basic control flow (if/else)
- Simple variable assignments
- Basic literals

The CFG parser is NOT suitable for:

- Modern Machine Dialect programs with utilities
- Programs with rich documentation
- Complex type annotations
- Programs using advanced identifier formats
- Production use cases requiring full language support

## Recommendation

For any production use or full language support, **always use the main parser**
(`machine_dialect.parser.Parser`). The CFG parser should only be used for:

- Educational purposes
- Simple syntax validation
- Testing grammar concepts
- Backward compatibility with very old Machine Dialect code

## Migration Path

To make code compatible with the CFG parser:

1. Remove all utility definitions and calls
1. Replace `Use` with direct expressions
1. Remove all backtick identifiers
1. Remove all bold variable syntax
1. Remove all HTML documentation tags
1. Simplify all natural language operators to basic forms
1. Remove type annotations
1. Flatten nested block structures
