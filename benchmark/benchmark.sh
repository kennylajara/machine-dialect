#!/bin/bash
# benchmark.sh - Multi-language performance benchmark

set -e  # Exit on error

RESULTS_FILE="/workspace/benchmark_results.json"
ITERATIONS=5
FIBONACCI_N=30
EXPECTED_RESULT=832040

# Initialize results
echo '{"benchmark": "fibonacci", "n": 30, "results": [' > $RESULTS_FILE
FIRST_RESULT=true

# Helper function for timing
run_benchmark() {
    local lang=$1
    local cmd=$2
    local mode=$3

    echo "Testing $lang ($mode)..."

    # Warm-up for JIT languages
    if [ "$mode" = "jit" ]; then
        for i in {1..3}; do
            $cmd > /dev/null 2>&1 || true
        done
    fi

    # Measure execution time
    local times=""
    for i in $(seq 1 $ITERATIONS); do
        # Use /usr/bin/time with format for microsecond precision
        local start_ns=$(date +%s%N)
        $cmd > /tmp/bench_output 2>&1
        local end_ns=$(date +%s%N)
        local output=$(cat /tmp/bench_output 2>/dev/null || echo "ERROR")
        # Calculate duration in nanoseconds, then convert to milliseconds
        local duration_ns=$((end_ns - start_ns))
        local duration_ms=$(echo "scale=3; $duration_ns / 1000000" | bc)
        if [ -z "$times" ]; then
            times="$duration_ms"
        else
            times="$times $duration_ms"
        fi

        # Validate output
        if [ "$output" != "$EXPECTED_RESULT" ]; then
            echo "WARNING: $lang produced output: $output (expected: $EXPECTED_RESULT)"
        fi
    done

    # Calculate statistics (using bc for floating point comparison)
    local min=$(echo $times | tr ' ' '\n' | sort -g | head -1)
    local max=$(echo $times | tr ' ' '\n' | sort -g | tail -1)
    local median=$(echo $times | tr ' ' '\n' | sort -g | sed -n "$((ITERATIONS/2+1))p")

    # Output JSON result
    if [ "$FIRST_RESULT" = "false" ]; then
        echo -n ',' >> $RESULTS_FILE
    fi
    FIRST_RESULT=false
    echo -n "{\"language\": \"$lang\", \"mode\": \"$mode\", " >> $RESULTS_FILE
    echo -n "\"times_ms\": [${times// /, }], " >> $RESULTS_FILE
    echo -n "\"min_ms\": $min, \"max_ms\": $max, \"median_ms\": $median}" >> $RESULTS_FILE
}

# C Implementation
cat > fib.c << 'EOF'
#include <stdio.h>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { printf("%d\n", fib(30)); return 0; }
EOF
gcc -O3 -march=native -mtune=native -flto fib.c -o fib_c
run_benchmark "C" "./fib_c" "compiled"

# C++ Implementation
cat > fib.cpp << 'EOF'
#include <iostream>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { std::cout << fib(30) << std::endl; return 0; }
EOF
g++ -O3 -march=native -mtune=native -flto fib.cpp -o fib_cpp
run_benchmark "C++" "./fib_cpp" "compiled"

# Go Implementation
cat > fib.go << 'EOF'
package main
import "fmt"
func fib(n int) int {
    if n <= 1 { return n }
    return fib(n-1) + fib(n-2)
}
func main() { fmt.Println(fib(30)) }
EOF
go build -ldflags "-s -w" -o fib_go fib.go
run_benchmark "Go" "./fib_go" "compiled"

# Rust Implementation
cat > fib.rs << 'EOF'
fn fib(n: i32) -> i32 {
    if n <= 1 { n } else { fib(n-1) + fib(n-2) }
}
fn main() { println!("{}", fib(30)); }
EOF
rustc -C opt-level=3 -C target-cpu=native -C lto=fat fib.rs -o fib_rust
run_benchmark "Rust" "./fib_rust" "compiled"

# Java Implementation
cat > Fib.java << 'EOF'
public class Fib {
    static int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
    public static void main(String[] args) { System.out.println(fib(30)); }
}
EOF
javac Fib.java
run_benchmark "Java" "java Fib" "jit"

# C# Implementation
mkdir -p /tmp/csharp && cd /tmp/csharp
cat > Program.cs << 'EOF'
class Program {
    static int Fib(int n) => n <= 1 ? n : Fib(n-1) + Fib(n-2);
    static void Main() => System.Console.WriteLine(Fib(30));
}
EOF
cat > csharp.csproj << 'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
EOF
if dotnet build -c Release > /dev/null 2>&1; then
    cd /workspace
    run_benchmark "C#" "dotnet run --project /tmp/csharp -c Release --no-build" "jit"
else
    echo "C# build failed - skipping"
    cd /workspace
fi

# JavaScript Implementation
cat > fib.js << 'EOF'
function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
console.log(fib(30));
EOF
run_benchmark "JavaScript" "node fib.js" "jit"

# Python Implementation
cat > fib.py << 'EOF'
def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)
print(fib(30))
EOF
run_benchmark "Python" "python3 fib.py" "interpreted"

# Ruby Implementation
cat > fib.rb << 'EOF'
def fib(n); n <= 1 ? n : fib(n-1) + fib(n-2); end
puts fib(30)
EOF
run_benchmark "Ruby" "ruby fib.rb" "interpreted"

# Perl Implementation
cat > fib.pl << 'EOF'
sub fib { my $n = shift; $n <= 1 ? $n : fib($n-1) + fib($n-2) }
print fib(30), "\n";
EOF
run_benchmark "Perl" "perl fib.pl" "interpreted"

# Machine Dialect™ Implementation
cat > fib.md << 'EOF'
### **Utility**: `Fibonacci`

<details>
<summary>Calculate the nth Fibonacci number recursively</summary>

> If `n` is less than or equal to _1_:
> > Give back `n`.
> Else:
> > Define `n_minus_1` as Whole Number. \
> > Set `n_minus_1` to `n` - _1_. \
> > Define `n_minus_2` as Whole Number. \
> > Set `n_minus_2` to `n` - _2_. \
> > Define `fib_1` as Whole Number. \
> > Set `fib_1` using `Fibonacci` with `n_minus_1`. \
> > Define `fib_2` as Whole Number. \
> > Set `fib_2` using `Fibonacci` with `n_minus_2`. \
> > Define `result` as Whole Number. \
> > Set `result` to `fib_1` + `fib_2`. \
> > Give back `result`.

</details>

#### Inputs:

- `n` **as** Whole Number (required)

#### Outputs:

- `result`

Define `m` as Whole Number.
Set `m` to _30_.

Define `final result` as Whole Number.
Set `final result` using `Fibonacci` with `m`.

Say `final result`.
EOF

# Machine Dialect™ (Compiled) - using Rust VM
if [ -f fib.md ]; then
    # Compile to bytecode first (not timed)
    if python3 -m machine_dialect compile fib.md -o fib.mdbc --opt-level 3 >/dev/null 2>&1; then
        # Check if Rust VM is available
        if python3 -c "import machine_dialect_vm" 2>/dev/null; then
            run_benchmark "Machine Dialect™" \
                "python3 -m machine_dialect run fib.mdbc" "bytecode"
        else
            echo "Rust VM not available - skipping"
        fi
    else
        echo "Machine Dialect™ compilation failed - skipping"
    fi
else
    echo "fib.md not found - skipping Machine Dialect™"
fi

# Finalize JSON
echo ']}' >> $RESULTS_FILE

# Generate summary report
python3 << 'EOF'
import json
import sys

try:
    with open('/workspace/benchmark_results.json') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading results: {e}")
    sys.exit(1)

results = sorted(data['results'], key=lambda x: x['median_ms'])
print("\n" + "="*60)
print("BENCHMARK RESULTS - Fibonacci(30)")
print("="*60)
print(f"{'Rank':<5} {'Language':<30} {'Median (ms)':<12} {'Mode':<12}")
print("-"*60)

md_result = None
for i, r in enumerate(results, 1):
    print(f"{i:<5} {r['language']:<30} {r['median_ms']:<12} {r['mode']:<12}")
    if r['language'] == 'Machine Dialect™':
        md_result = r

print("="*60)
if md_result:
    print("\nMACHINE DIALECT PERFORMANCE ANALYSIS")
    print("-"*60)
    print(f"Machine Dialect™: {md_result['median_ms']:.1f}ms")

    # Helper function to format performance comparison
    def format_comparison(md_time, other_time):
        ratio = md_time / other_time
        if ratio > 1:
            return f"{ratio:.1f}x slower"
        elif ratio < 1:
            return f"{1/ratio:.1f}x faster"
        else:
            return "same speed"

    # Compare with different language categories
    for r in results:
        if r['language'] != 'Machine Dialect™':
            comparison = format_comparison(md_result['median_ms'], r['median_ms'])
            print(f"  vs {r['language']:<20} {comparison:>12}")

    # Find closest competitor
    closest = min([r for r in results if r['language'] != 'Machine Dialect™'],
                  key=lambda x: abs(x['median_ms'] - md_result['median_ms']))
    comparison = format_comparison(md_result['median_ms'], closest['median_ms'])
    print(f"\nClosest competitor: {closest['language']} ({closest['median_ms']:.1f}ms - {comparison})\n")

    # Category comparisons
    compiled = [r for r in results if r['mode'] == 'compiled']
    jit = [r for r in results if r['mode'] == 'jit']
    interpreted = [r for r in results if r['mode'] == 'interpreted' and r['language'] != 'Machine Dialect™']

    if compiled:
        avg_compiled = sum(r['median_ms'] for r in compiled) / len(compiled)
        print(f"vs avg compiled languages: {format_comparison(md_result['median_ms'], avg_compiled)}")
    if jit:
        avg_jit = sum(r['median_ms'] for r in jit) / len(jit)
        print(f"vs avg JIT languages: {format_comparison(md_result['median_ms'], avg_jit)}")
    if interpreted:
        avg_interpreted = sum(r['median_ms'] for r in interpreted) / len(interpreted)
        print(f"vs avg interpreted languages: {format_comparison(md_result['median_ms'], avg_interpreted)}")

    print("")
EOF

# Clean up
rm -f fib.* Fib.* *.class /tmp/fib.*
rm -rf /tmp/csharp
