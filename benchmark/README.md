# Machine Dialect Performance Benchmark

This benchmark suite evaluates Machine Dialect's performance against 10 popular
programming languages using a recursive Fibonacci implementation (n=40).

## Quick Start

### Option 1: Local Benchmark (Recommended for quick testing)

```bash
cd benchmark
python3 run_benchmark.py
```

This will test all available languages on your system and generate `benchmark_results.json`.

### Option 2: Docker Benchmark (Full environment)

```bash
# Build the Docker image
docker build -t benchmark:latest -f Dockerfile ..

# Run the benchmark
docker run --rm \
  --cpus="1.0" \
  --memory="2g" \
  -v $(pwd):/workspace \
  benchmark:latest \
  /workspace/benchmark.sh
```

### Option 3: Docker Compose

```bash
docker-compose up --build
```

## Files

- `Dockerfile` - Multi-stage Docker image with all language runtimes
- `benchmark.sh` - Shell script for Docker-based benchmarking
- `run_benchmark.py` - Python script for local benchmarking
- `fibonacci.md` - Machine Dialect implementation of Fibonacci
- `docker-compose.yml` - Docker Compose configuration

## Benchmark Details

- **Algorithm**: Recursive Fibonacci(40) = 102334155
- **Iterations**: 5 runs per language
- **Metrics**: Min, Max, Median execution time in milliseconds
- **Languages Tested**:
  - Compiled: C, C++, Go, Rust
  - JIT: Java, C#, JavaScript
  - Interpreted: Python, Ruby, Perl, Machine Dialect

## Expected Performance Tiers

1. **Tier 1** (0.3-0.5s): C, C++, Rust - Native compiled with optimizations
1. **Tier 2** (0.5-0.8s): Go - Native compiled with GC
1. **Tier 3** (0.8-1.5s): Java, C# - JIT compiled
1. **Tier 4** (1.5-3s): JavaScript - V8 JIT
1. **Tier 5** (2-5s): Machine Dialect (Compiled) - Bytecode VM
1. **Tier 6** (15-40s): Machine Dialect (Interpreted) - MIR interpreter
1. **Tier 7** (20-60s): Ruby, Python, Perl - Pure interpreted

## Results

After running the benchmark, results are saved to `benchmark_results.json` and a
summary table is displayed showing:

- Ranking by median execution time
- Language name and execution mode
- Performance metrics

The benchmark validates that Machine Dialect's optimization passes provide measurable
performance improvements over baseline interpretation.
