# Machine Dialect CLI Usage

## Installation

### For Development (Editable Mode)

```bash
# Clone the repository
git clone https://github.com/yourusername/machine-dialect.git
cd machine-dialect

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### For Regular Use

```bash
# Install from source
pip install .

# Or with uv
uv pip install .
```

## Available Commands

After installation, you can use either `md` or `machine-dialect` command:

### Show Help

```bash
md --help
md --version
```

### Compile Source Files

```bash
# Basic compilation
md compile program.md

# With custom output file
md compile program.md -o output.mdc

# Show disassembly after compilation
md compile program.md -d

# Verbose mode
md compile program.md -v

# Combine options
md compile program.md -o myprogram.mdc -v -d
```

### Run Compiled Programs

```bash
# Run normally
md run program.mdc

# Debug mode (shows VM state at each step)
md run program.mdc -d
```

### Disassemble Bytecode

```bash
# Show bytecode disassembly
md disasm program.mdc
```

### Interactive Shell (REPL)

```bash
# Start interactive shell
md shell

# Start in token debug mode
md shell --tokens
```

## Example Workflow

1. **Create a Machine Dialect program** (`example.md`):

   ```markdown
   Set `x` to _10_.
   Set `y` to _20_.
   Set `sum` to `x` + `y`.
   Set `product` to `x` * `y`.
   ```

1. **Compile the program**:

   ```bash
   md compile example.md -v
   ```

   Output:

   ```txt
   Compiling 'example.md'...
   Successfully compiled to 'example.mdc'
     Main chunk: 28 bytes
     Constants: 7
   ```

1. **Run the compiled program**:

   ```bash
   md run example.mdc -d
   ```

1. **Inspect the bytecode**:

   ```bash
   md disasm example.mdc
   ```

1. **Use the interactive shell**:

   ```bash
   md shell
   ```

   Then in the shell:

   ```txt
   md> Set `test` to _42_.

   AST:
   --------------------------------------------------
     Set test to 42
   --------------------------------------------------

   md> exit
   Goodbye!
   ```

## Machine Dialect Syntax Reminder

- **Variables**: Use backticks: `` `variable` ``
- **Literals**: Use underscores: `_10_`, `_"text"_`, `_True_`
- **Statements**: Must end with periods (`.`)
- **Comments**: Not supported in parser (yet)

## Troubleshooting

### Command not found

If `md` command is not found after installation:

1. Make sure your virtual environment is activated
1. Check if the package is installed: `pip list | grep machine-dialect`
1. Try using the full command: `python -m machine_dialect`

### Parsing errors

Common issues:

- Using `**variable**` instead of `` `variable` ``
- Forgetting underscores for literals
- Missing periods at the end of statements
- Including markdown headers (`#`) in source files

### Installation in editable mode

For development, always use editable mode (`-e` flag) so changes to the source code are immediately
reflected without reinstalling:

```bash
uv pip install -e .
# or
pip install -e .
```
