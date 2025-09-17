# Machine Dialect™

The **Machine Dialect™ programming language** is designed to look like natural language and feel
like structured documentation. It is written in Markdown and intended to be both human-friendly
and AI-native — readable by people, generatable and parsable by machines.

> ⚠️ **ALPHA VERSION** ⚠️
>
> The Machine Dialect™ language is currently in **ALPHA** stage. We are rapidly iterating on the language
> design and implementation. During this phase:
>
> - **Breaking changes will be frequent** and without deprecation warnings
> - The syntax and semantics are still evolving based on user feedback
> - APIs and compiler behavior may change between any versions
> - No backward compatibility is maintained during alpha
>
> We encourage experimentation and feedback, but please be aware that code written today
> may require updates to work with future versions.

## Table of Contents

- [Why Another Programming Language?](#why-another-programming-language)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

## Why Another Programming Language?

Modern programming languages were made for humans to instruct machines. But now that machines
can understand and generate human-like language, it's time to rethink the language itself.

The Machine Dialect™ language is designed for a world where:

- **AI writes most of the code**, and humans supervise, modify, and approve
- Code is **visually readable**, even by non-programmers
- The structure of the program is as **intuitive as a document**, and lives comfortably inside
  Markdown files

### The Philosophy of Machine Dialect™

- **Natural structure**: Programs are written as paragraphs, headings, lists — not brackets,
  semicolons, and cryptic symbols
- **AI-first**: Syntax is deterministic enough for parsing, but optimized for LLMs to
  generate and understand effortlessly
- **Human-friendly**: Uses everyday words over technical jargon. Markdown keeps everything readable,
  diffable, and renderable
- **Self-documenting**: Looks like pseudocode. Reads like an explanation of what the code does

## Installation

### From PyPI (Recommended)

```bash
pip install machine-dialect
```

### From Source

For development installation, please see our [Contributing Guide](CONTRIBUTING.md#development-setup)
for detailed setup instructions.

## Getting started

### Writing Your First Program

Create a file `hello.md`:

> Define `greeting` as _Text_.\
> Set `greeting` to _"Hello, World!"_.
>
> Say `greeting`.

### Compiling and Running Programs

The Machine Dialect™ toolchain provides a complete toolchain for compiling and executing programs:

```bash
# Compile a .md file to bytecode (.mdbc)
python -m machine_dialect compile hello.md

# Compile with custom filename (main)
python -m machine_dialect compile hello.md -o main.mdbc

# Run a compiled bytecode file
python -m machine_dialect run hello.mdbc

# Interactive shell (REPL)
python -m machine_dialect shell
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for detailed information.

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file
for details.
