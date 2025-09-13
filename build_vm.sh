#!/bin/bash
# Build script for Machine Dialect™ Rust VM

set -e

echo "Building Machine Dialect™ Rust VM..."
echo "=================================="
echo ""

# Check if maturin is installed
if ! command -v maturin &> /dev/null; then
    echo "❌ maturin is not installed."
    echo ""
    echo "Please install dev dependencies first:"
    echo "  uv sync --all-groups"
    echo ""
    echo "This will install maturin and other development tools."
    exit 1
fi

# Change to VM directory
cd machine_dialect_vm

# Build the Rust VM with PyO3 bindings
echo "Building Rust VM with Python bindings..."
maturin develop --features pyo3

echo ""
echo "✅ Build complete!"
echo ""
echo "You can now import the VM in Python:"
echo "  import machine_dialect_vm"

# Change to rood directory
cd ..
