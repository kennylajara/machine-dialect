# Machine Dialect™ Performance Benchmark

This benchmark compares the Machine Dialect™ language performance against other programming languages
using a recursive Fibonacci(30) implementation.

## Benchmark Methodology

- **Algorithm**: Recursive Fibonacci (intentionally suboptimal for CPU stress testing)
- **Test Case**: `fibonacci(30) = 832040`
- **Iterations**: 5 runs per language, using median for comparison
- **Timing**: Nanosecond precision with conversion to milliseconds
- **Warm-up**: JIT languages get 3 warm-up runs before measurement

## Language Implementations

All implementations use the same recursive algorithm:

```python
function fib(n):
    if n <= 1:
        return n
    else:
        return fib(n-1) + fib(n-2)
```

### Compilation Flags

Compiled languages use aggressive optimizations:

- **C/C++**: `-O3 -march=native -mtune=native -flto`
- **Rust**: `-C opt-level=3 -C target-cpu=native -C lto=fat`
- **Go**: `-ldflags "-s -w"`
- **Machine Dialect™**: `--opt-level 3` (bytecode compilation)

## Running the Benchmark

### Docker (Recommended for full environment)

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

### Local (Quick testing)

```bash
cd benchmark
python3 run_benchmark.py
```

### Docker Compose

```bash
docker-compose up --build
```

## Current Results (2025-09-09)

```text
============================================================
BENCHMARK RESULTS - Fibonacci(30)
============================================================
Rank  Language                       Median (ms)  Mode
------------------------------------------------------------
1     C                              3.058        compiled
2     Rust                           3.407        compiled
3     C++                            4.221        compiled
4     Go                             6.159        compiled
5     Java                           37.225       jit
6     JavaScript                     38.339       jit
7     Python                         83.916       interpreted
8     Ruby                           108.853      interpreted
9     Perl                           235.435      interpreted
10    C#                             440.874      jit
11    Machine Dialect™                9634.53      bytecode
============================================================

MACHINE DIALECT PERFORMANCE ANALYSIS
------------------------------------------------------------
Machine Dialect™: 9634.5ms
  vs C                    3150.6x slower
  vs Rust                 2827.9x slower
  vs C++                  2282.5x slower
  vs Go                   1564.3x slower
  vs Java                 258.8x slower
  vs JavaScript           251.3x slower
  vs Python               114.8x slower
  vs Ruby                 88.5x slower
  vs Perl                 40.9x slower
  vs C#                   21.9x slower

Closest competitor: C# (440.9ms - 21.9x slower)

vs avg compiled languages: 2287.8x slower
vs avg JIT languages: 56.0x slower
vs avg interpreted languages: 67.5x slower
```

## Performance Analysis

The Machine Dialect™ bytecode VM implementation shows significant performance gaps:

| Comparison | Factor | Analysis |
|------------|--------|----------|
| vs Compiled Languages | ~2288x slower | Expected due to lack of native code generation |
| vs JIT Languages | ~56x slower | VM lacks JIT compilation and optimization |
| vs Interpreted Languages | ~68x slower | VM overhead exceeds typical interpreter overhead |

### Key Observations

1. **Closest Competitor**: C# at 440.9ms (21.9x faster than Machine Dialect™)
2. **Best Case**: Only 21.9x slower than C# (a JIT-compiled language)
3. **Worst Case**: 3150.6x slower than C (optimized native code)
4. **VM Overhead**: Current implementation has higher overhead than even interpreted languages

## Files

- `Dockerfile` - Multi-stage Docker image with all language runtimes
- `benchmark.sh` - Shell script for Docker-based benchmarking
- `run_benchmark.py` - Python script for local benchmarking
- `docker-compose.yml` - Docker Compose configuration
- `benchmark_results.json` - Benchmark results in JSON format
- `visualize_results.py` - Generate charts from results
- `IMPLEMENTATION_STATUS.md` - Detailed implementation tracking

## Performance Roadmap

### Phase 1: VM Optimization (Target: 10x improvement)

- [ ] Optimize instruction dispatch loop
- [ ] Implement threaded code or computed goto
- [ ] Reduce stack operation overhead
- [ ] Cache frequently used values

### Phase 2: Advanced VM Features (Target: 5x improvement)

- [ ] Implement inline caching for method calls
- [ ] Add specialized bytecode instructions
- [ ] Optimize recursive call handling
- [ ] Implement tail call optimization

### Phase 3: JIT Compilation (Target: 10x improvement)

- [ ] Basic JIT for hot paths
- [ ] Type specialization
- [ ] Method inlining
- [ ] Register allocation

### Ultimate Goal

- **Short term**: Match Python's performance (~84ms for fibonacci(30))
- **Medium term**: Match JavaScript's V8 JIT performance (~38ms)
- **Long term**: Approach compiled language performance (sub-10ms)
