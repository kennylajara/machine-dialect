#!/bin/bash
# benchmark.sh - Multi-language performance benchmark

set -e  # Exit on error

RESULTS_FILE="/workspace/benchmark_results.json"
ITERATIONS=5
FIBONACCI_N=40
EXPECTED_RESULT=102334155

# Initialize results
echo '{"benchmark": "fibonacci", "n": 40, "results": [' > $RESULTS_FILE

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
        local start=$(date +%s%N)
        local output=$($cmd 2>/dev/null || echo "ERROR")
        local end=$(date +%s%N)
        local duration=$((($end - $start) / 1000000))  # Convert to ms
        times="$times $duration"

        # Validate output
        if [ "$output" != "$EXPECTED_RESULT" ]; then
            echo "WARNING: $lang produced output: $output (expected: $EXPECTED_RESULT)"
        fi
    done

    # Calculate statistics
    local min=$(echo $times | tr ' ' '\n' | sort -n | head -1)
    local max=$(echo $times | tr ' ' '\n' | sort -n | tail -1)
    local median=$(echo $times | tr ' ' '\n' | sort -n | sed -n "$((ITERATIONS/2+1))p")

    # Output JSON result
    if [ -f $RESULTS_FILE ]; then
        echo -n ',' >> $RESULTS_FILE
    fi
    echo -n "{\"language\": \"$lang\", \"mode\": \"$mode\", " >> $RESULTS_FILE
    echo -n "\"times_ms\": [${times// /, }], " >> $RESULTS_FILE
    echo -n "\"min_ms\": $min, \"max_ms\": $max, \"median_ms\": $median}" >> $RESULTS_FILE
}

# C Implementation
cat > fib.c << 'EOF'
#include <stdio.h>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { printf("%d\n", fib(40)); return 0; }
EOF
gcc -O3 fib.c -o fib_c
run_benchmark "C" "./fib_c" "compiled"

# C++ Implementation
cat > fib.cpp << 'EOF'
#include <iostream>
int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
int main() { std::cout << fib(40) << std::endl; return 0; }
EOF
g++ -O3 fib.cpp -o fib_cpp
run_benchmark "C++" "./fib_cpp" "compiled"

# Go Implementation
cat > fib.go << 'EOF'
package main
import "fmt"
func fib(n int) int {
    if n <= 1 { return n }
    return fib(n-1) + fib(n-2)
}
func main() { fmt.Println(fib(40)) }
EOF
go build -o fib_go fib.go
run_benchmark "Go" "./fib_go" "compiled"

# Rust Implementation
cat > fib.rs << 'EOF'
fn fib(n: i32) -> i32 {
    if n <= 1 { n } else { fib(n-1) + fib(n-2) }
}
fn main() { println!("{}", fib(40)); }
EOF
rustc -O fib.rs -o fib_rust
run_benchmark "Rust" "./fib_rust" "compiled"

# Java Implementation
cat > Fib.java << 'EOF'
public class Fib {
    static int fib(int n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
    public static void main(String[] args) { System.out.println(fib(40)); }
}
EOF
javac Fib.java
run_benchmark "Java" "java Fib" "jit"

# C# Implementation
mkdir -p /tmp/csharp && cd /tmp/csharp
cat > Program.cs << 'EOF'
class Program {
    static int Fib(int n) => n <= 1 ? n : Fib(n-1) + Fib(n-2);
    static void Main() => System.Console.WriteLine(Fib(40));
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
dotnet build -c Release > /dev/null 2>&1 || echo "C# build failed"
cd /workspace
run_benchmark "C#" "dotnet run --project /tmp/csharp -c Release --no-build" "jit"

# JavaScript Implementation
cat > fib.js << 'EOF'
function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
console.log(fib(40));
EOF
run_benchmark "JavaScript" "node fib.js" "jit"

# Python Implementation
cat > fib.py << 'EOF'
def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)
print(fib(40))
EOF
run_benchmark "Python" "python3 fib.py" "interpreted"

# Ruby Implementation
cat > fib.rb << 'EOF'
def fib(n); n <= 1 ? n : fib(n-1) + fib(n-2); end
puts fib(40)
EOF
run_benchmark "Ruby" "ruby fib.rb" "interpreted"

# Perl Implementation
cat > fib.pl << 'EOF'
sub fib { my $n = shift; $n <= 1 ? $n : fib($n-1) + fib($n-2) }
print fib(40), "\n";
EOF
run_benchmark "Perl" "perl fib.pl" "interpreted"

# Machine Dialect (Interpreted)
cp /workspace/fibonacci.md /tmp/fibonacci.md
run_benchmark "Machine Dialect (Interpreted)" \
    "python3 -m machine_dialect /tmp/fibonacci.md" "interpreted"

# Machine Dialect (Compiled) - if bytecode compilation is available
if python3 -c "from machine_dialect.compiler import compile" 2>/dev/null; then
    python3 -m machine_dialect compile /tmp/fibonacci.md -o /tmp/fibonacci.mdb 2>/dev/null
    run_benchmark "Machine Dialect (Compiled)" \
        "python3 -m machine_dialect run /tmp/fibonacci.mdb" "bytecode"
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
print("BENCHMARK RESULTS - Fibonacci(40)")
print("="*60)
print(f"{'Rank':<5} {'Language':<30} {'Median (ms)':<12} {'Mode':<12}")
print("-"*60)

for i, r in enumerate(results, 1):
    print(f"{i:<5} {r['language']:<30} {r['median_ms']:<12} {r['mode']:<12}")

print("="*60)
if results:
    print(f"Fastest: {results[0]['language']} ({results[0]['median_ms']}ms)")
    print(f"Slowest: {results[-1]['language']} ({results[-1]['median_ms']}ms)")
    if results[0]['median_ms'] > 0:
        print(f"Speedup: {results[-1]['median_ms']/results[0]['median_ms']:.1f}x")
EOF

# Clean up
rm -f fib.* Fib.* *.class /tmp/fibonacci.*
rm -rf /tmp/csharp
