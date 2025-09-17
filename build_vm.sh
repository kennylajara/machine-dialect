#!/bin/bash
# Build script for Machine Dialect™ Rust VM

set -e

# Parse command line arguments
BUILD_MODE="${1:-develop}"  # Default to develop mode

echo "Building Machine Dialect™ Rust VM..."
echo "=================================="
echo "Build mode: $BUILD_MODE"
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
if [ "$BUILD_MODE" = "release" ]; then
    echo "Building Rust VM wheel for release..."
    maturin build --release --features pyo3
    echo ""
    echo "✅ Release build complete!"
    echo "Wheel files created in: target/wheels/"
elif [ "$BUILD_MODE" = "develop" ]; then
    echo "Building Rust VM with Python bindings for development..."
    maturin develop --features pyo3
    echo ""
    echo "✅ Development build complete!"
    echo "You can now import the VM in Python:"
    echo "  import machine_dialect_vm"
else
    echo "❌ Invalid build mode: $BUILD_MODE"
    echo "Usage: ./build_vm.sh [develop|release]"
    exit 1
fi

# Change to root directory
cd ..
