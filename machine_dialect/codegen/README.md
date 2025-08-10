# Codegen Module

## Overview

The **Codegen** module takes a **Machine Dialect AST** (produced by the Parser) and
translates it into **bytecode** ready to be consumed by the **Virtual Machine (VM)**.
This document covers:

- Backend design (AST walk → bytecode)
- Bytecode format and auxiliary tables (constants, symbols)
- Calling conventions and scope handling
- Control flow support (if/else, blocks)
- Testing and extension guidelines

> This README assumes familiarity with the **AST** and **Parser** modules documented in their
> respective READMEs.

______________________________________________________________________

## Architecture

### Components

```text
codegen/
├── __init__.py           # Public API
├── emitter.py            # Instruction assembler/emitter
├── codegen.py            # AST visitor → bytecode
├── isa.py                # Instruction set architecture definition
├── symtab.py             # Symbol table(s) and scope management
├── constpool.py          # Constant pool (deduplication)
├── objects.py            # Compiled artifacts (Chunk, Function, Module)
└── tests/                # Test suite
```

### High-Level Flow

1. **AST Visitor**: `CodeGenerator` walks the AST in *post-order*.
1. **Symbol Resolution**: `SymbolTable` handles locals, parameters, and globals.
1. **Constants**: `ConstantPool` deduplicates numbers, strings, and other literals.
1. **Emission**: `Emitter` turns nodes into opcodes and manages jump patching.
1. **Packaging**: Produces a `Chunk` or `FunctionObject` with bytecode and metadata.

______________________________________________________________________

## ISA (Instruction Set Architecture)

The VM is **stack-based**. Each instruction may have immediate operands (little‑endian integers).

### Core Instructions

```text
# Load/store
LOAD_CONST   <u16 idx>        ; Push constant[idx] to stack
LOAD_LOCAL   <u16 slot>       ; Push local[slot]
STORE_LOCAL  <u16 slot>       ; local[slot] = pop()
LOAD_GLOBAL  <u16 idx>        ; Push global with name in const[idx] (identifier)
STORE_GLOBAL <u16 idx>        ; Assign to global with name in const[idx]

# Arithmetic / logic (operate on top of stack)
ADD, SUB, MUL, DIV, MOD
EQ, NEQ, LT, GT, LTE, GTE
NOT, AND, OR                   ; AND/OR are stack logic ops (no short-circuit)

# Control flow
JUMP        <i16 rel>         ; PC += rel
JUMP_IF_FALSE <i16 rel>       ; jump if pop() is falsy
POP                           ; discard top of stack

# Functions (if applicable)
CALL       <u8 nargs>         ; call target with nargs arguments
RETURN                        ; return (top of stack, or empty)

# Misc
DUP, SWAP, NOP
```

> Note: If the language requires **short-circuit** `and`/`or`, implement it in codegen with
> `JUMP_IF_FALSE` / `JUMP` instead of a single `AND`/`OR` opcode.

______________________________________________________________________

## Auxiliary Structures

### ConstantPool

- Deduplicates: `int`, `float`, `string`, *identifiers*, and optionally *function refs*.
- Indexed by insertion order, uses string interning.

```python
pool.add(42)         # -> idx 0
pool.add("hello")    # -> idx 1
pool.add("hello")    # -> idx 1 (reused)
```

### SymbolTable and Scopes

- `SymbolTable` manages nested scopes (blocks, functions).
- Local variables get consecutive slots (u16).
- Unresolved identifiers are treated as globals (by name) if allowed.

```text
Scope(root)
└── Scope(function foo)
    ├── param x -> slot 0
    └── local y -> slot 1
```

______________________________________________________________________

## AST → Bytecode Mapping

Below are common translation rules aligned with the project AST.

### Literals

- `IntegerLiteral(v)` → `LOAD_CONST <idx(v)>`
- `FloatLiteral(v)`   → `LOAD_CONST <idx(v)>`
- `StringLiteral(v)`  → `LOAD_CONST <idx(v)>`
- `BooleanLiteral(v)` → `LOAD_CONST <idx(v)>`
- `EmptyLiteral()`    → `LOAD_CONST <idx(empty)>` *(if modeled as constant)*

### Identifiers

- As **expression**: if local → `LOAD_LOCAL <slot>`; if global → `LOAD_GLOBAL <idx(name)>`.

### Prefix Operators

- `PrefixExpression('-', right)`:

  ```text
  <codegen(right)>
  LOAD_CONST <idx(-1)>
  MUL
  ```

- `PrefixExpression('not', right)`:

  ```text
  <codegen(right)>
  NOT
  ```

### Infix Operators

- `InfixExpression(left, '+', right)`:

  ```text
  <codegen(left)>
  <codegen(right)>
  ADD
  ```

- Comparisons / equality follow same pattern and emit `LT`, `GTE`, `EQ`, `NEQ`, etc.

### Assignments (SetStatement)

```text
# Set x to 2 + 3.
<codegen(2)>
<codegen(3)>
ADD
# local if defined, else global
STORE_LOCAL <slot(x)>  |  STORE_GLOBAL <idx("x")>
```

### Calls (CallStatement / expressions with Arguments)

```text
# Call print with "Hello", name: "Kenny".
# Convention: push CALLEE, then positional args, then named arg pairs, then arity.
<codegen(`print`)>           ; usually resolves to global
LOAD_CONST <idx("Hello")>
LOAD_CONST <idx("name")>
LOAD_CONST <idx("Kenny")>
CALL <nargs=3>               ; if named args supported, see Conventions section
POP                           ; if used as statement
```

> Named arguments can be:
>
> 1. Normalized to positionals in codegen (reordering before CALL), or
> 1. Supported with `CALL_NAMED <nargs> <nkvpairs>` pushing key/value pairs.

### IfStatement and Blocks

```text
If <cond>:
> <consequence>
Otherwise:
> <alternative>
```

Translation with patching:

```text
<codegen(cond)>
JUMP_IF_FALSE <to_else>     ; patch later
<codegen(block_true)>
JUMP <to_end>               ; skip else
<patch: to_else = here>
<codegen(block_false)>
<patch: to_end = here>
```

### ReturnStatement

```text
<codegen(expr)>
RETURN
```

### SayStatement (example of I/O to stdlib)

```text
<codegen(expr)>
LOAD_GLOBAL <idx("say")>
SWAP
CALL <nargs=1>
POP
```

______________________________________________________________________

## Calling Conventions

- **Stack order** before `CALL n`:
  1. callee
  1. arg₀ … argₙ₋₁
- **Return**: result is left on top of stack; `RETURN` leaves it there.
- **Parameters**: materialized as function locals (slots 0..n-1).

If supporting **methods**, slot 0 (or arg₀) can be reserved for `self/this`.

______________________________________________________________________

## Compiled Artifact Format

### Chunk / FunctionObject

```text
Chunk:
- magic: u32            ; "¾¾Êþ" (BE BE CA FE)
- flags: u16            ; version, endian, etc.
- const_count: u16
- code_size: u32
- const_pool: [Const]   ; see below
- code: [u8]            ; linear bytecode
- lineinfo?: ...        ; optional PC → (line, col) mapping
- locals?: u16          ; max slots
- params?: u8           ; arity if function
```

**Const** types:

- TAG_INT (i64), TAG_FLOAT (f64), TAG_STR (len+bytes), TAG_IDENT (interned),
  TAG_FUNCREF (index to another Chunk), TAG_EMPTY

______________________________________________________________________

## Errors and Source Mapping

- Each AST node carries a source `token` → pass to `Emitter` to fill *lineinfo*
  (optional).
- On emission failure (e.g., unresolved identifier), record a codegen error with `(line, col)`.

______________________________________________________________________

## Full Example

Source (Machine Dialect pseudo-code):

```text
Set **x** to _2_ + _3_.
If **x** > _3_:
> Say _"ok"_.
Otherwise:
> Say _"no"_.
```

Bytecode (annotated):

```text
; consts: [2, 3, "x", "ok", "no"]
0:  LOAD_CONST 0        ; 2
3:  LOAD_CONST 1        ; 3
6:  ADD
7:  STORE_GLOBAL 2      ; "x"
10: LOAD_GLOBAL 2       ; x
13: LOAD_CONST 1        ; 3
16: GT
17: JUMP_IF_FALSE +8    ; else branch
20: LOAD_CONST 3        ; "ok"
23: LOAD_GLOBAL <say>
26: SWAP
27: CALL 1
29: POP
30: JUMP +8
33: LOAD_CONST 4        ; "no"
36: LOAD_GLOBAL <say>
39: SWAP
40: CALL 1
42: POP
```

______________________________________________________________________

## Testing

### Unit tests

- **constpool**: deduplication, ordering, serialization.
- **symtab**: slot assignment, nesting, shadowing.
- **emitter**: operand encoding, jump patching, range checks.
- **codegen**: golden tests AST → bytecode (snapshots).
- **errors**: proper reporting with line/col.

Run:

```bash
pytest machine_dialect/codegen/tests/ -v
```

### Suggested Golden Tests

1. Literals / arithmetic expressions
1. Comparisons and logic (with/without short-circuit)
1. Assignments (locals vs globals)
1. Nested if/else
1. Calls with `n` args (and named args if supported)
1. Mid-block and end returns

______________________________________________________________________

## Extension Guide

### Adding a New Instruction

1. Define opcode in `isa.py` (enum + operand spec).
1. Implement encoding in `emitter.py` (endianness, size, validation).
1. Adjust `CodeGenerator` to emit it.
1. Update VM (if needed) and add tests.

### New AST Node / Syntax

1. Ensure the Parser builds it (see Parser README).
1. Implement `CodeGenerator.visit_<Node>()`.
1. If it needs symbols/constants, extend `symtab`/`constpool`.
1. Add golden tests and error cases.

______________________________________________________________________

## Best Practices

- **Post-order**: generate children first, then node’s own instruction.
- **Idempotency**: don’t emit code for error nodes.
- **Clean stack**: statements leave stack unchanged.
- **Operand ranges**: validate `u8/u16/i16` before emitting (overflow errors).
- **Intern strings**: avoid duplicates in constants and identifiers.
- **Line info**: useful for stack traces and debugging.

______________________________________________________________________

## API (Draft)

```python
from machine_dialect.codegen import CodeGenerator
from machine_dialect.ast import Program

def compile(program: Program) -> "Chunk":
    gen = CodeGenerator()
    return gen.compile(program)
```

- `CodeGenerator.compile(program)` → `Chunk`
- `Chunk.to_bytes()` → `bytes` (serialization)
- `disassemble(bytes)` (optional) → human-readable

______________________________________________________________________

## Relationship with Other Modules

- **AST**: defines node structure for visiting (see AST README).
- **Parser**: builds the AST (see Parser README).
- **VM**: consumes the `Chunk` to execute.

______________________________________________________________________

## Roadmap (Optional)

- Short-circuit `and`/`or` via jumps
- Simple constant folding in codegen
- Dead code elimination for trivial jumps
- Closure support (capturing upvalues)
- Debugger and disassembler
