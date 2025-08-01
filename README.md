# Machine Dialect (.md)

**Machine Dialect** is a programming language designed to look like natural language and feel like
structured documentation. It is written in Markdown and intended to be both human-friendly and AI-
native — readable by people, generatable and parsable by machines.

## Why?

Modern programming languages were made for humans to instruct machines. But now that machines can
understand and generate human-like language, it’s time to rethink the language itself.

Machine Dialect is for a future where:

- **AI writes most of the code**, and humans supervise, modify, and approve.
- Code is **visually readable**, even by non-programmers.
- The structure of the program is as **intuitive as a document**, and lives comfortably inside
  Markdown files.

## Philosophy

- ✍️ **Natural structure**: Programs are written as paragraphs, headings, lists — not brackets,
  semicolons, and cryptic symbols.
- 🧠 **AI-first**: Syntax is deterministic enough for parsing, but optimized for LLMs to generate and
  understand effortlessly.
- 👁️ **Human-supervisable**: Markdown keeps everything readable, diffable, and renderable.
- 🪶 **Lightweight**: No ceremony. Just write it like you'd explain it.
- 📐 **Math as code**: Mathematical operations are expressed using LaTeX syntax inside `$$...$$`
  blocks. This keeps formulas readable, renderable, and easy to evaluate with symbolic math engines
  like SymPy or MathJax.
- 🏷️ **Metadata-aware**: Executable files begin with a YAML frontmatter block (`---`) that declares
  intent (e.g. `exec: true`). This convention is widely supported by other tools and safely ignored by
  standard Markdown renderers, making it easy to difference executable files from context-only files.

## Features

- Functions are declared using Markdown headers.
- Each sentence is an instruction — terminated with a period.
- Markdown lists represent arrays or sets depending on.
- Key-value pairs are written like definitions: `**Label**: Value`.
- Variables, values, and calls are identified with lightweight formatting rules (e.g. **bold** for
  variables, _italics_ for constants).
- All source files are `.md` and can be opened in any Markdown editor.

## Example

```markdown
---
exec: true
---
# Shopping Calculator

## Initialize variables
Set **total** to _0_.
Set **item count** to _0_.

## Items
- Banana: _15_
- Toothpaste: _30_
- Notebook: _120_

## Compute total
Add all **Items** values to **total**.
Count all **Items**, store _them_ in **item count**.
Apply formula:

$$
\text{average} = \frac{\text{total}}{\text{itemCount}}
$$

## Results
Print: "You have spent: " + **total**.
Print: "Average per item: " + **average**.
```

## How It Works

- Markdown structure defines the hierarchy.
- The interpreter parses sentences line by line and infers instructions.
- AI models can generate this structure with very little training.
- Humans can preview and edit it using standard Markdown tools.

## Status

> ⚠️ This project is a prototype. We’re exploring syntax design, parsing strategies, and possible
> runtimes. Expect breaking changes. Contributions welcome.

## Goals

- Define a minimal, deterministic grammar.
- Build a compiler and/or interpreter in Python.
- Support a virtual machine or bytecode executor.
- Eventually: build a Rust-based interpreter for performance.
