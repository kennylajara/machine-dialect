# Machine Dialect Syntax Specification

Machine Dialect is a natural language programming language that uses English-like syntax within
Markdown documents. This document provides the complete syntax specification based on the
implementation analysis.

Machine Dialect source files are Markdown documents (`.md`).

## Lexical Elements

### Case Sensitivity

- **Keywords**: Case-insensitive (`Set`, `set`, `SET` are all valid)
- **Identifiers**: Case-preserving (stored as written)
- **Boolean literals**: Case-insensitive (`True`, `true`, `TRUE` all work)

### Token Types

#### 1. Identifiers

Identifiers name variables, functions, and other entities.

**Rules:**

- Must start with a letter (a-z, A-Z) or underscore (\_)
- Can contain letters, digits, underscores, spaces, and hyphens after the first character
- Cannot be empty
- Cannot start with underscore followed by only digits (e.g., `_42` is invalid)
- Pattern `_digits_` is invalid (e.g., `_42_`, `__123__`)

**Syntax:**

- Bare identifier: `myVariable`, `user_name`, `data-processor`
- Backtick-wrapped: `` `identifier` `` (required in statements, preserves spaces)

#### 2. Literals

##### Integer Literals

- Regular: `42`, `0`, `-17`
- Underscore-wrapped: `_42_`, `_-17_`
- Must be valid decimal integers
- Negative numbers supported with minus sign

##### Float Literals

- Regular: `3.14`, `0.5`, `-2.7`
- Underscore-wrapped: `_3.14_`, `_-2.7_`
- Decimal point required (`.5` becomes `0.5`)
- At least one digit required after decimal point

##### String Literals

- Double quotes: `"Hello, World!"`
- Single quotes: `'Hello, World!'`
- Underscore-wrapped: `_"Hello"_`, `_'Hello'_`
- Backslash can escape quotes: `\"`, `\'`
- Note: Other escape sequences (`\n`, `\t`, etc.) are not processed

##### URL Literals

- Same syntax as strings but validated as URLs
- Must be valid RFC 3986 URLs
- Example: `"https://example.com"`

##### Boolean Literals

- True values: `True`, `Yes` (case-insensitive)
- False values: `False`, `No` (case-insensitive)
- Underscore-wrapped: `_Yes_`, `_No_`

##### Empty Literal

- Keyword: `empty`
- Represents null/nil/undefined values

##### Triple Backtick Literals

- Multi-line code blocks: ```` ```content``` ````
- Used for embedding code or multi-line but not implemented yet

#### 3. Keywords

Primary keywords (case-insensitive):

- **Control flow**: `if`, `when`, `whenever`, `then`, `else`, `otherwise`
- **Variables**: `Set`, `to`, `as`
- **Functions**: `call`, `apply`, `with`, `give back`, `gives back`
- **Actions**: `action`, `interaction`, `behavior`, `behaviour`
- **Types**: `Integer`, `Float`, `Boolean`, `Number`, `Text`, `URL`, `Date`, `DateTime`, `Time`
- **Logic**: `and`, `or`, `not`
- **Special**: `empty`, `required`, `optional`, `default`
- **Output**: `Say`
- **Object-oriented**: `template`, `trait`, `take`, `Tell`

Multi-word keywords are recognized as single tokens:

- `give back`, `gives back`
- `is equal to`, `is not equal to`
- `is greater than`, `is less than`
- etc.

#### 4. Operators

##### Arithmetic Operators

- Addition: `+`
- Subtraction: `-`
- Multiplication: `*`
- Division: `/`
- Power: `**`

##### Comparison Operators

**Symbolic:**

- Less than: `<`
- Greater than: `>`
- Less than or equal: `<=`
- Greater than or equal: `>=`

**Natural language (recognized as single tokens):**

- Value equality: `equals`, `is equal to`, `is the same as`
- Value inequality: `is not equal to`, `does not equal`, `doesn't equal`, `is different from`,
  `is not`, `isn't`
- Strict equality: `is strictly equal to`, `is exactly equal to`, `is identical to`
- Strict inequality: `is not strictly equal to`, `is not exactly equal to`,
  `is not identical to`
- Relational: `is greater than`, `is more than`, `is less than`, `is under`, `is fewer than`
- Relational with equality: `is greater or equal to`, `is at least`, `is no less than`,
  `is less than or equal to`, `is at most`, `is no more than`

##### Logical Operators (Boolean only)

- AND: `and` (requires boolean operands)
- OR: `or` (requires boolean operands)
- NOT: `not` (prefix operator, requires boolean operand)

#### 5. Delimiters and Punctuation

- Parentheses: `(`, `)`
- Braces: `{`, `}`
- Period: `.` (statement terminator)
- Comma: `,` (argument separator, ternary separator)
- Semicolon: `;` (alternative to comma in ternary)
- Colon: `:` (named arguments)
- Hash: `#`, `##`, `###`, `####` (Markdown headers)

#### 6. Special Tokens

- **Stopwords**: Common English words (`a`, `an`, `the`, `is`, `are`, etc.) that are recognized
  but typically ignored. Useful to make texts more readable while maintaining it parseable
- **Comments**: Content between `<summary>` and `</summary>` tags
- **Tags**: `<summary>`, `</summary>`, `<details>`, `</details>`

## Statements

### 1. Set Statement (Variable Assignment)

Assigns a value to a variable.

**Syntax:**

```markdown
Set `identifier` to expression.
```

**Rules:**

- `Set` keyword is case-insensitive
- Identifier must be in backticks
- `to` keyword required
- Statement must end with period
- Expression can be any valid expression

**Examples:**

```markdown
Set `count` to 0.
Set `name` to "Alice".
Set `result` to 5 + 3.
Set `flag` to True.
```

### 2. Return Statement

Returns a value from a function or block.

**Syntax:**

```markdown
give back expression.
gives back expression.
```

**Rules:**

- Both `give back` and `gives back` are valid
- Case-insensitive
- Must be followed by an expression
- Statement must end with period

**Examples:**

```markdown
give back 42.
gives back **x** + **y**.
give back "Success".
```

### 3. Say Statement (Output)

Outputs/displays a value.

**Syntax:**

```markdown
Say expression.
```

**Rules:**

- `Say` keyword (currently case-sensitive with capital S, should be case-insensitive)
- Must be followed by an expression
- Statement must end with period

**Examples:**

```markdown
Say "Hello, World!".
Say **message**.
Say 2 + 2.
```

### 4. Call Statement

Invokes a function with optional arguments.

**Syntax:**

```markdown
call `function_name`.
call `function_name` with arguments.
```

**Rules:**

- `call` keyword (case-insensitive)
- Function name must be in backticks
- Arguments are optional, introduced by `with`
- Statement must end with period

**Argument Formats:**

- Positional: `with value1, value2`
- Named: `with param1: value1, param2: value2`
- Mixed: `with value1, param2: value2` (positional must come first)

**Examples:**

```markdown
call `print`.
call `add` with 5, 3.
call `greet` with name: "Bob", age: 25.
call `calculate` with **x**, **y**.
```

### 5. If Statement

Conditional execution of code blocks.

**Syntax:**

```markdown
if condition then
> consequence_block

if condition then
> consequence_block
else
> alternative_block
```

**Rules:**

- `if`, `when`, `whenever` are synonyms
- `then` keyword required after condition
- Blocks marked with `>` prefix (indentation)
- `else` or `otherwise` for alternative branch
- Each statement in blocks must end with period

**Examples:**

```markdown
if **x** is greater than 0 then
> Say "Positive".

when **user** equals "admin" then
> Set `access` to True.
else
> Set `access` to False.
```

### 6. Action Statement (Private Method)

Defines a private method that can only be called within the same scope.

**Syntax:**

```markdown
### **Action**: `name`

<details>
<summary>Optional description</summary>

> body statements

</details>
```

**Rules:**

- Must start with `###` (three hash marks)
- `Action` keyword must be wrapped in double asterisks
- Colon (`:`) required after `**Action**`
- Action name must be in backticks
- Body wrapped in `<details>` tags
- Optional `<summary>` tag for description
- Body statements prefixed with `>` (block syntax)
- Parameters (inputs/outputs) not yet fully implemented

**Examples:**

```markdown
### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

> Set `noise` to _"WEE-OO WEE-OO"_.
> Say `noise`.

</details>
```

### 7. Interaction Statement (Public Method)

Defines a public method that can be called from outside the scope.

**Syntax:**

```markdown
### **Interaction**: `name`

<details>
<summary>Optional description</summary>

> body statements

</details>
```

**Rules:**

- Same structure as Action but uses `**Interaction**` keyword
- Public visibility (can be called externally)
- Must start with `###` (three hash marks)
- Body wrapped in `<details>` tags
- Parameters (inputs/outputs) not yet fully implemented

**Examples:**

```markdown
### **Interaction**: `turn alarm off`

<details>
<summary>Turns off the alarm when it is on.</summary>

> if `alarm is on` then
> > Set `alarm is on` to _No_.
> > Say _"Alarm has been turned off"_.

</details>
```

## Expressions

### 1. Conditional (Ternary) Expression

**Syntax:**

```markdown
consequence if condition, else alternative
consequence when condition, otherwise alternative
consequence if condition; else alternative
```

**Rules:**

- `if` or `when` for condition
- Comma or semicolon before `else`/`otherwise`
- All three parts required

**Examples:**

```markdown
"Yes" if **x** > 0, else "No"
100 when **flag** is True, otherwise 0
```

### 2. Binary Operations

**Arithmetic:**

```markdown
**a** + **b**
**x** - 5
**price** * 1.2
**total** / **count**
```

**Comparison:**

```markdown
**x** equals 10
**name** is not "admin"
**age** is greater than 18
**score** is less than or equal to 100
```

**Logical (Boolean operands only):**

```markdown
**is_valid** and **has_permission**
**is_active** or **is_pending**
True and False
```

### 3. Unary Operations

**Logical Negation (Boolean operand only):**

```markdown
not **is_active**
not True
not (**a** and **b**)
```

**Negative:**

```markdown
-**x**
-42
```

### 4. Grouped Expressions

Use parentheses to override precedence:

```markdown
(**a** + **b**) * **c**
not (**x** and **y**)
```

## Operator Precedence

From highest to lowest (higher precedence operators are evaluated first):

1. **Grouping** - Parentheses `()`
1. **Unary** - Unary operators (`not`, unary `-`)
1. **Multiplicative** - Multiplication, division (`*`, `/`)
1. **Additive** - Addition, subtraction (binary `+`, `-`)
1. **Relational** - Comparisons (`<`, `>`, `<=`, `>=`)
1. **Equality** - Equality tests (`equals`, `is not`, `is strictly equal to`, etc.)
1. **Logical AND** - Boolean AND (`and`)
1. **Logical OR** - Boolean OR (`or`)
1. **Conditional** - Ternary expressions (`if`/`when`)

Note: The parser uses these precedence levels to determine the order of operations in expressions.

## Statement Termination Rules

1. **Period Required:**

   - All statements must end with a period
   - Statements inside blocks must end with periods
   - Expression statements require periods unless at EOF

1. **Period Optional:**

   - Last statement before EOF (if not in a block)
   - Expressions within other expressions don't need periods

## Block Syntax

Blocks are marked with `>` prefix for each line:

```markdown
if condition then
> Set `x` to 1.
> Set `y` to 2.
> give back `x` + `y`.
```

**Rules:**

- Each line in a block starts with `>`
- Blocks can be nested (use multiple `>` for deeper nesting)
- Empty blocks are not allowed (syntax error)
- All statements in blocks must end with periods

## Error Recovery

The parser uses panic-mode recovery:

- On syntax error, skips tokens until finding a period or EOF
- Attempts to continue parsing after errors
- Collects multiple errors in a single parse
- Maximum of 20 panic recoveries before stopping

## Type System (Planned)

The language supports type annotations in certain contexts:

- `Integer` - Whole numbers
- `Float` - Decimal numbers
- `Number` - Either Integer or Float
- `Text` - String values
- `Boolean` - True/False values
- `URL` - Valid URLs
- `Date`, `DateTime`, `Time` - Temporal types
- `List` - Collection type
- `empty` - Null/undefined value

## Special Constructs

### Double-Asterisk Keywords

Keywords (and only keywords) can be wrapped in double asterisks:

```markdown
**Set** `x` to 5.
**give back** 42.
```

**Rules:**

- Only valid keywords accepted (not identifiers, stopwords, or literals)
- Multi-word keywords supported: `**give back**`, `**is equal to**`
- The parser treats these as the keyword tokens themselves

### Backtick Identifiers

Identifiers in backticks preserve exact formatting:

```markdown
Set `my variable` to 10.
call `process data`.
```

**Rules:**

- Required in Set statements
- Required for function names in Call statements
- Preserves spaces and special characters
- Stopwords in backticks become identifiers

## Example Program

```markdown
---
executable: true
---

# Store's Alarm System

## Traits

**Define** `alarm is on` **as** a **status**.\
_Whether the store's alarm is turned on_ (**default**: _Yes_).

**Define** `door is open` **as** a **status**.\
_Whether the store's door is currently open_ (**default**: _No_).

**Define** `people inside` **as** a **whole number**.\
_How many people are in the store_ (**default**: _0_).

## Behaviors

### **Action**: `make noise`

<details>
<summary>Emits the sound of the alarm.</summary>

> Set `noise` to _"WEE-OO WEE-OO WEE-OO"_.\
> **Say** `noise`.

</details>

#### Inputs

- `sound` **as** Text (required)
- `volume` **as** Whole Number (optional, default: 60)

#### Outputs

- `success` **as** Status

### **Interaction**: `turn alarm off`

<details>
<summary>Turns off the alarm when it is on.</summary>

> **if** `alarm is on` **then**:
>
> > **Set** `alarm is on` **to** _No_.\
> > **Say** _"Alarm has been turned off"_

</details>

## Rule

### 1. Alarm makes noise when security is violated

**if** `alarm is on` **and** **either** `people inside` **is at least** _1_ **or** `door is open`
**then**, **trigger** `make noise`.
```

## Compilation Requirements

For valid Machine Dialect code:

1. All statements must be properly terminated with periods
1. Identifiers in statements must be in backticks
1. Blocks must be properly indented with `>` markers
1. No empty blocks allowed
1. Parentheses and braces must be balanced
1. String literals must have closing quotes
1. Triple backticks must be properly closed
1. Arguments must follow positional-before-named rule
1. Keywords must be valid (case-insensitive)
1. Identifiers must follow naming rules
